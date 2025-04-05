## 🚀 Ejecución en Segundo Plano (3 Métodos)

### 1. Método Simple con Nohup
```bash
nohup python bot_config.py > bot.log 2>&1 &
```

### 2. Método Avanzado con Screen
```bash
screen -S airdrop_bot -dm python bot_config.py
```
**Para reconectar:**
```bash
screen -r airdrop_bot
```

### 3. Como Servicio Systemd (Recomendado para producción)
```bash
sudo tee /etc/systemd/system/airdrop.service > /dev/null <<EOL
[Unit]
Description=Airdrop Bot Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python) $(pwd)/bot_config.py
Restart=always
Environment="BOT_PK=tu_llave_privada"
Environment="BOT_TOKEN=tu_token_de_telegram"

[Install]
WantedBy=multi-user.target
EOL

# Activar servicio
sudo systemctl daemon-reload
sudo systemctl enable airdrop.service
sudo systemctl start airdrop.service
```

## 🔍 Verificación del Funcionamiento

```bash
# Ver logs
tail -f bot.log

# Ver procesos
pgrep -fl "python bot_config.py"

# Ver servicio (si usas systemd)
journalctl -u airdrop.service -f
```

## 🛠️ Resolución Rápida de Problemas

**Si el bot se detiene:**
1. Verifica saldo de gas: `web3.eth.get_balance(CONFIG['OWNER_ADDRESS'])`
2. Revisa conexión RPC: `web3.is_connected()`
3. Verifica permisos: `chmod 600 airdrop_data.json`

**Reinicio rápido:**
```bash
pkill -f "python bot_config.py" && nohup python bot_config.py > bot.log 2>&1 &
```

Esta configuración unificada mantiene todo en un solo archivo para fácil despliegue, con opciones seguras para ejecución continua.
