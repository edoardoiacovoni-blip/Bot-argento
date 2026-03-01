# Bot Argento 🤖

Bot di trading automatico su Pionex (argento SPOT) basato sul framework **Flying Wheel a 18 punti**.

## Descrizione

Bot Argento esegue un'analisi strutturata in 18 controlli prima di effettuare operazioni di accumulo argento. In modalità `DRY_RUN` (default) il bot non esegue ordini reali, consentendo di testare la logica senza rischi.

## ⚙️ Come Funziona

### Il Sistema Flying Wheel

Il bot implementa un sistema di trading automatico chiamato **"Flying Wheel"** che opera tramite il motore a 18 controlli su Pionex:

```
Loop principale
├── 1. Controlla segnali istituzionali
├── 2. Recupera dati di mercato (ticker)
├── 3. Analisi 18 punti → identifica opportunità (variazione > 1.8%)
├── 4. Esegue micro-operazioni di acquisto
└── 5. Accumula argento SPOT tramite SILVER_SYMBOL
```

### Analisi 18 Punti (`src/flying_wheel/engine.py`)

Il cuore del bot è il **motore Flying Wheel a 18 controlli**: esegue in sequenza 18 verifiche prima di ogni operazione. Tutti i check devono risultare `PASS` per procedere. Le verifiche coprono:
- Connessione API e saldo disponibile
- Prezzo corrente, spread bid/ask e volume 24h
- Indicatori tecnici: trend (EMA), RSI, MACD, volatilità (ATR/Bollinger)
- Correlazione con l'indice argento spot e notizie macro rilevanti
- Dimensione posizione, stop-loss, take-profit e limiti di rischio globale

### Accumulo Argento (`accumulate_silver`)

Dopo aver superato tutti i 18 controlli, il bot esegue un **ordine MARKET BUY** per accumulare argento SPOT:
- Simbolo configurabile tramite `SILVER_SYMBOL` (es. `XAG_USDT`)
- Importo fisso in USDT configurabile tramite `SILVER_BUY_AMOUNT_USDT`
- Utilizza il client REST interno `PionexClient` (nessuna dipendenza esterna)

### Gestione degli Errori

Il bot è progettato per essere **resiliente**:
- Se un check fallisce, l'operazione viene annullata e il ciclo si ripete
- In caso di errore generico, attende e riprova automaticamente
- Se le credenziali non sono configurate, il bot si arresta con un messaggio chiaro

## Struttura del Progetto

```
Bot-argento/
├── main.py                        # Entry point principale
├── src/
│   ├── pionex_client.py           # Client REST autenticato per Pionex
│   └── flying_wheel/
│       ├── engine.py              # Motore Flying Wheel (18 controlli)
│       └── checks.py              # Definizioni dei 18 check
├── requirements.txt
├── render.yaml                    # Configurazione deploy su Render (Worker)
├── .env.example                   # Template variabili d'ambiente
├── GUIDA_RENDER.md                # Guida deploy su Render
└── README.md                      # Questo file
```

## Variabili d'Ambiente

| Variabile                 | Obbligatoria | Descrizione                                                      |
|---------------------------|:------------:|------------------------------------------------------------------|
| `PIONEX_API_KEY`          | ✅            | API Key ottenuta dal pannello Pionex                             |
| `PIONEX_SECRET_KEY`       | ✅            | Secret Key ottenuta dal pannello Pionex                          |
| `SILVER_SYMBOL`           | ✅            | Coppia SPOT argento su Pionex (es. `XAG_USDT`)                  |
| `SILVER_BUY_AMOUNT_USDT`  | ❌            | Importo in USDT per ogni acquisto di argento (default: `10`)     |
| `DRY_RUN`                 | ❌            | `1` = nessun ordine reale (default consigliato), `0` = trading reale |

## Come Eseguire in Locale

### 1. Clona il repository

```bash
git clone https://github.com/edoardoiacovoni-blip/Bot-argento.git
cd Bot-argento
```

### 2. Crea l'ambiente virtuale e installa le dipendenze

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# oppure: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

```bash
cp .env.example .env
# Modifica .env con le tue chiavi API reali e il simbolo argento corretto
```

### 4. Esegui in modalità DRY_RUN (sicura, default)

```bash
DRY_RUN=1 python main.py
```

### 5. Esegui in modalità reale (solo quando pronto!)

```bash
DRY_RUN=0 python main.py
```

## Deploy su Render (Worker)

Consulta [GUIDA_RENDER.md](./GUIDA_RENDER.md) per i passaggi dettagliati.

In sintesi:
1. Crea un account su [Render](https://render.com)
2. Collega il repository GitHub
3. Render rileva automaticamente `render.yaml` e configura il Worker
4. Aggiungi `PIONEX_API_KEY`, `PIONEX_SECRET_KEY` e `SILVER_SYMBOL` nelle Environment Variables
5. Fai il deploy

## Note di Sicurezza

⚠️ **Non committare mai** le chiavi API reali nel repository.  
✅ Usa sempre variabili d'ambiente o il file `.env` (già escluso da `.gitignore`).  
✅ Testa sempre con `DRY_RUN=1` prima di andare in produzione.  
🔒 Ruota le API key periodicamente dal pannello Pionex.

## Flying Wheel — 18 Controlli

Il motore Flying Wheel esegue 18 controlli sequenziali prima di ogni ciclo di trading.  
Tutti i check devono risultare `PASS` per procedere con un ordine reale.  
I dettagli dei singoli controlli sono definiti in `src/flying_wheel/checks.py`.

