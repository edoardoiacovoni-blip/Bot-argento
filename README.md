# Bot Argento - Flying Wheel System

Bot di trading automatico per accumulare argento (PAXG) tramite Pionex.

> 🚀 **Guida Rapida**: Se vuoi collegare questo repository a Render, leggi la [GUIDA_RENDER.md](./GUIDA_RENDER.md) per istruzioni dettagliate passo-passo!

## 🚀 Funzionalità

- Connessione API Pionex per trading automatico
- Sistema "Flying Wheel" con analisi 18 punti
- Accumulo automatico in Silver (PAXG)
- Deploy su Render Cloud Platform
- Monitoraggio segnali istituzionali

## ⚙️ Come Funziona

### Il Sistema Flying Wheel

Il bot implementa un sistema di trading automatico chiamato **"Flying Wheel"** che opera in un ciclo continuo su Pionex:

```
Loop principale
├── 1. Controlla segnali istituzionali
├── 2. Recupera dati di mercato (ticker)
├── 3. Analisi 18 punti → identifica opportunità
├── 4. Esegue micro-operazioni di acquisto
└── 5. Converte i profitti in Silver (PAXG)
```

### Analisi 18 Punti (`calculate_quantum_jump`)

Il cuore del bot è l'**analisi 18 punti** (`quantumJump`): filtra i ticker di mercato cercando asset con una variazione di prezzo superiore all'**1.8%** (`priceChangePercent > 1.8`). Vengono selezionate al massimo le prime **5 opportunità** più rilevanti.

### Micro-Operazioni (`execute_micro_trade`)

Per ogni opportunità identificata, il bot esegue una **micro-operazione** di acquisto tramite l'API Pionex:
- Ordine di tipo `MARKET`
- Quantità fissa di `0.01` unità
- Simbolo dell'asset individuato dall'analisi

### Accumulo in Oro (PAXG) (`convert_to_silver`)

Ogni profitto generato viene automaticamente convertito in **PAXG** (PAX Gold, token ancorato al prezzo dell'oro fisico) tramite un ordine `MARKET` su `PAXGUSD`. L'obiettivo è accumulare valore in un asset stabile legato ai metalli preziosi.

### Monitoraggio Connessioni (`verify_connections`)

All'avvio, il bot verifica:
1. Presenza delle credenziali API Pionex (`PIONEX_API_KEY`, `PIONEX_SECRET_KEY`)
2. Raggiungibilità dell'API Pionex
3. Ambiente di esecuzione (Render vs locale)

### Gestione degli Errori

Il bot è progettato per essere **resiliente**:
- Se il recupero dei ticker fallisce, attende 30 secondi e riprova
- In caso di errore generico nel ciclo, attende 10 secondi e riprova
- Se le credenziali non sono configurate, il bot si arresta con un messaggio chiaro

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

### ❓ Il Repository sarà già su Render?

**NO** - Il repository GitHub NON sarà automaticamente su Render. Devi collegarlo tu manualmente seguendo questi passaggi:

### 📝 Procedura Completa di Collegamento

#### 1. Prerequisiti

Prima di iniziare, assicurati di avere:
- ✅ Un account su [Render](https://render.com) (gratuito)
- ✅ Un account GitHub con accesso a questo repository
- ✅ Le credenziali API di Pionex pronte

#### 2. Collega GitHub a Render

1. Vai su [Render Dashboard](https://dashboard.render.com/)
2. Se è la prima volta, Render ti chiederà di autorizzare l'accesso a GitHub
3. Clicca su "Connect GitHub" o "Authorize GitHub"
4. Autorizza Render ad accedere ai tuoi repository GitHub

#### 3. Crea il Web Service

1. Nel Dashboard di Render, clicca su **"New +"** (in alto a destra)
2. Seleziona **"Web Service"**
3. Render mostrerà la lista dei tuoi repository GitHub
4. Cerca **"Bot-argento"** nella lista
5. Clicca su **"Connect"** accanto al repository

#### 4. Configura il Servizio

Render rileverà automaticamente il file `render.yaml` e compilerà i campi, ma verifica:

- **Name**: `bot-argento` (puoi cambiarlo se vuoi)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Plan**: Seleziona "Free" (o un piano a pagamento se preferisci)

#### 5. Aggiungi le Environment Variables

**IMPORTANTE**: Prima di fare il deploy, devi aggiungere le variabili d'ambiente:

1. Scorri fino alla sezione **"Environment Variables"**
2. Clicca su **"Add Environment Variable"**
3. Aggiungi:
   ```
   Key: PIONEX_API_KEY
   Value: <la_tua_api_key_pionex>
   ```
4. Clicca di nuovo su **"Add Environment Variable"**
5. Aggiungi:
   ```
   Key: PIONEX_SECRET_KEY
   Value: <il_tuo_secret_key_pionex>
   ```

#### 6. Deploy

1. Clicca su **"Create Web Service"**
2. Render inizierà automaticamente il build e il deploy
3. Potrai vedere i log in tempo reale
4. Quando vedi "FLYING WHEEL ENGINE: TAKEOFF" nei log, il bot è attivo! 🚀

### 🔍 Come Trovare il Tuo Servizio su Render

Dopo il deploy:
- Il servizio sarà visibile nel tuo [Render Dashboard](https://dashboard.render.com/)
- Il nome sarà quello che hai scelto al punto 4 (es: `bot-argento`)
- Render gli assegnerà un URL tipo: `https://bot-argento-xyz123.onrender.com`

### 🔄 Aggiornamenti Automatici

Una volta collegato, ogni volta che fai un push su GitHub:
- Render rileverà automaticamente le modifiche
- Farà il build e deploy della nuova versione
- Il bot si riavvierà con il nuovo codice

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

## ❓ FAQ (Domande Frequenti)

### Il repository sarà già presente su Render?

No, devi collegarlo manualmente. Render non crea automaticamente servizi dai repository GitHub. Devi:
1. Accedere a Render
2. Autorizzare Render ad accedere a GitHub
3. Creare un nuovo Web Service selezionando questo repository

### Con che nome apparirà su Render?

Il nome predefinito suggerito da `render.yaml` è **"bot-argento"**, ma puoi cambiarlo durante la creazione del servizio. Il nome che scegli sarà quello che vedrai nel Dashboard di Render.

### Il servizio è gratuito?

Render offre un piano gratuito che include:
- 750 ore/mese di runtime
- Il servizio si spegne dopo 15 minuti di inattività
- Si riavvia automaticamente quando necessario

Per un bot che deve funzionare 24/7, considera un piano a pagamento.

### Cosa succede dopo il primo deploy?

Dopo il primo deploy su Render:
- Ogni push su GitHub attiverà un nuovo deploy automatico
- Il bot si riavvierà con le nuove modifiche
- I log saranno sempre visibili nel Dashboard di Render

### Come faccio a vedere se il bot sta funzionando?

1. Vai nel tuo Dashboard Render
2. Clicca sul servizio "bot-argento"
3. Vai nella sezione "Logs"
4. Dovresti vedere il messaggio "FLYING WHEEL ENGINE: TAKEOFF"
5. Se vedi errori, controlla che le variabili d'ambiente siano configurate correttamente

### Posso cambiare le API Key dopo il deploy?

Sì! Nel Dashboard di Render:
1. Vai nel tuo servizio
2. Sezione "Environment"
3. Modifica le variabili PIONEX_API_KEY e PIONEX_SECRET_KEY
4. Salva e Render riavvierà automaticamente il servizio

## 📄 Licenza

MIT License
