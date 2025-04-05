import random
import time
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from web3 import Web3

# Configuración
RPC_URL = "TU RPC AQUI"
CHAIN_ID = TU ID DE LA CADENA AQUI SIN COMILLAS
TOKEN_ADDRESS = "CONTRATO DE TU TOKEN"
PRIVATE_KEY = "TU LLAVE PRIVADA DE DONDE TIENES LOS TOKEN QUE DISTRIBUIRAS"  # ¡Cambia esto!
OWNER_ADDRESS = "TU DIRECCION DE CARTERA DE LA LLAVE PRIVADA"
BOT_TOKEN = "AQUI EL TOKEN DEL BOT DE TELEGRAM"

# Configuración del airdrop
COOLDOWN = 3600  # 1 hora en segundos (cambia a 86400 para 24 horas)
CLAIM_AMOUNT = Web3.to_wei(100, 'ether')
DATA_FILE = "airdrop_data.json"

# Inicializar Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
token_contract = web3.eth.contract(
    address=TOKEN_ADDRESS,
    abi=[{
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }]
)

# Cargar datos persistentes
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"last_claim": {}, "wallet_claims": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Mensajes
meme_messages = [
    "¡F5 presionado! Tokens refrescados!",
    "¡Recarga completada! Sigue apretando F5!",
    "¡BOOM! 100 F5 han aterrizado en tu wallet!",
    "¡Error 404: Tokens no encontrados... oh, espera, sí llegaron!"
]

async def can_claim(user_id: int, wallet: str, data: dict) -> bool:
    """Verifica si el usuario puede reclamar"""
    now = time.time()
    
    # Verificar cooldown por usuario
    if str(user_id) in data["last_claim"]:
        last_time = data["last_claim"][str(user_id)]
        if now - last_time < COOLDOWN:
            return False
    
    # Verificar cooldown por wallet (opcional)
    if wallet.lower() in data["wallet_claims"]:
        last_time = data["wallet_claims"][wallet.lower()]
        if now - last_time < COOLDOWN:
            return False
    
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /start"""
    keyboard = [[InlineKeyboardButton("📥 Reclamar F5", callback_data="init_claim")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚀 *Bienvenido al Airdrop de F5 en TuxaChain!*\n\n"
        f"Puedes reclamar *100 F5* cada {COOLDOWN//3600} horas.\n"
        "Usa /claim 0xTuDireccion o presiona el botón.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def init_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de reclamo"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Por favor, envía tu dirección de wallet de TuxaChain:")
    context.user_data["awaiting_wallet"] = True

async def handle_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la dirección de wallet"""
    if not context.user_data.get("awaiting_wallet"):
        return
    
    user_id = update.message.from_user.id
    wallet = update.message.text.strip()
    data = load_data()
    
    if not Web3.is_address(wallet):
        await update.message.reply_text("❌ Dirección inválida. Intenta nuevamente.")
        return
    
    wallet = web3.to_checksum_address(wallet)
    
    if not await can_claim(user_id, wallet, data):
        remaining = COOLDOWN - (time.time() - max(
            data["last_claim"].get(str(user_id), 0),
            data["wallet_claims"].get(wallet.lower(), 0)
        ))
        await update.message.reply_text(
            f"⏳ Ya reclamaste recientemente. Espera {int(remaining//3600)}h {int((remaining%3600)//60)}m."
        )
        return
    
    try:
        tx = token_contract.functions.transfer(wallet, CLAIM_AMOUNT).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 200000,
            'gasPrice': web3.to_wei('1', 'gwei'),
            'nonce': web3.eth.get_transaction_count(OWNER_ADDRESS),
        })
        
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Actualizar datos
        data["last_claim"][str(user_id)] = time.time()
        data["wallet_claims"][wallet.lower()] = time.time()
        save_data(data)
        
        await update.message.reply_text(
            f"🎉 {random.choice(meme_messages)}\n\n"
            f"🔹 *Tokens enviados:* 100 F5\n"
            f"📭 *Destino:* `{wallet}`\n"
            f"🔗 *Transacción:* [{tx_hash.hex()}](AQUI TU URL DEL EXPLORADOR DE BLOQUES/tx/{tx_hash.hex()})",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    context.user_data.pop("awaiting_wallet", None)

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /claim"""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usa: /claim 0xTuDireccionDeWallet\n"
            f"Puedes reclamar cada {COOLDOWN//3600} horas.",
            parse_mode="Markdown"
        )
        return
    
    wallet = context.args[0]
    user_id = update.message.from_user.id
    data = load_data()
    
    if not Web3.is_address(wallet):
        await update.message.reply_text("❌ Dirección inválida. Intenta nuevamente.")
        return
    
    wallet = web3.to_checksum_address(wallet)
    
    if not await can_claim(user_id, wallet, data):
        remaining = COOLDOWN - (time.time() - max(
            data["last_claim"].get(str(user_id), 0),
            data["wallet_claims"].get(wallet.lower(), 0)
        ))
        await update.message.reply_text(
            f"⏳ Ya reclamaste recientemente. Espera {int(remaining//3600)}h {int((remaining%3600)//60)}m."
        )
        return
    
    try:
        tx = token_contract.functions.transfer(wallet, CLAIM_AMOUNT).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 200000,
            'gasPrice': web3.to_wei('1', 'gwei'),
            'nonce': web3.eth.get_transaction_count(OWNER_ADDRESS),
        })
        
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Actualizar datos
        data["last_claim"][str(user_id)] = time.time()
        data["wallet_claims"][wallet.lower()] = time.time()
        save_data(data)
        
        await update.message.reply_text(
            f"🎉 {random.choice(meme_messages)}\n\n"
            f"🔹 *Tokens enviados:* 100 F5\n"
            f"📭 *Destino:* `{wallet}`\n"
            f"🔗 *Transacción:* [{tx_hash.hex()}](AQUI TU URL DEL EXPLORADOR DE BLOQUES/tx/{tx_hash.hex()})",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Configuración del bot"""
    # Crear archivo de datos si no existe
    if not os.path.exists(DATA_FILE):
        save_data({"last_claim": {}, "wallet_claims": {}})
    
    # Configurar aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CallbackQueryHandler(init_claim, pattern="init_claim"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_input))
    
    # Iniciar bot
    application.run_polling()

if __name__ == "__main__":
    main()
