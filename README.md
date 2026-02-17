# Bot Argento - Flying Wheel System

Bot di trading automatico per accumulare argento (PAXG) tramite Pionex.

## 🚀 Funzionalità

- Connessione API Pionex per trading automatico
- Sistema "Flying Wheel" con analisi 18 punti
- Accumulo automatico in Silver (PAXG)
- Deploy su Render Cloud Platform
- Monitoraggio segnali istituzionali

## 📋 Requisiti

- Python 3.8+
- Account Pionex con API Key
- Account Render (per deployment cloud)

## 🔧 Configurazione

### Variabili d'Ambiente

Configura le seguenti variabili d'ambiente:

```bash
PIONEX_API_KEY=your_api_key_here
PIONEX_SECRET_KEY=your_secret_key_here
RENDER=true  # (opzionale, automatico su Render)
```

### Installazione Locale

```bash
# Clona il repository
git clone https://github.com/edoardoiacovoni-blip/Bot-argento.git
cd Bot-argento

# Installa le dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
export PIONEX_API_KEY="your_api_key"
export PIONEX_SECRET_KEY="your_secret_key"

# Avvia il bot
python main.py
```

## ☁️ Deploy su Render

### 1. Crea un nuovo Web Service su Render

1. Vai su [Render Dashboard](https://dashboard.render.com/)
2. Clicca su "New +" → "Web Service"
3. Connetti il tuo repository GitHub
4. Seleziona questo repository

### 2. Configura il servizio

- **Name**: `bot-argento`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

### 3. Aggiungi le Environment Variables

Nel pannello "Environment" di Render, aggiungi:

```
PIONEX_API_KEY = <your_pionex_api_key>
PIONEX_SECRET_KEY = <your_pionex_secret_key>
```

### 4. Deploy

Clicca su "Create Web Service" e Render farà automaticamente il deploy del bot.

## 🔐 Sicurezza Pionex API

Per ottenere le credenziali API di Pionex:

1. Accedi al tuo account Pionex
2. Vai su Account → API Management
3. Crea una nuova API Key
4. Salva API Key e Secret Key in modo sicuro
5. **NON condividere mai le tue chiavi API**

## 📊 Architettura

```
Bot Argento
├── Pionex API → Trading automatico
├── GitHub → Version control
└── Render → Cloud deployment
```

## 🛠️ Sviluppo

### Struttura del Codice

- `main.py` - Codice principale del bot
- `requirements.txt` - Dipendenze Python
- `.gitignore` - File da escludere dal repository

### Funzioni Principali

- `PionexClient` - Client per API Pionex
- `verify_connections()` - Verifica connessioni
- `calculate_quantum_jump()` - Analisi 18 punti
- `execute_micro_trade()` - Esecuzione micro-operazioni
- `convert_to_silver()` - Conversione profitti in PAXG
- `flying_wheel_engine()` - Motore principale

## 📝 Note

- Il bot è progettato per operare in modo continuativo
- Usa piccole quantità per le operazioni (0.01)
- Accumula profitti automaticamente in Silver (PAXG)
- Monitora costantemente i segnali istituzionali

## ⚠️ Disclaimer

Questo software è fornito "così com'è", senza garanzie di alcun tipo. Il trading di criptovalute comporta rischi. Usa questo bot a tuo rischio e pericolo.

## 📄 Licenza

MIT License
