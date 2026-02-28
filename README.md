# Bot Argento 🤖

Bot di trading automatico su Pionex per **XAG_USDT (argento)** basato sul framework **Flying Wheel a 18 punti**.

## Descrizione

Bot Argento esegue un'analisi strutturata in 18 controlli tecnici prima di effettuare operazioni di trading su XAG_USDT. In modalità `DRY_RUN` (default) il bot non esegue ordini reali, consentendo di testare la logica senza rischi.

## ⚙️ Come Funziona

### Il Sistema Flying Wheel

Il bot implementa un sistema di trading automatico chiamato **"Flying Wheel"** che opera in un loop continuo ogni `LOOP_SECONDS` secondi (default: 10s):

```
Loop continuo (ogni 10 secondi)
├── 1. Recupera klines OHLCV da Pionex (XAG_USDT, 5m)
├── 2. Calcola indicatori (EMA200, RSI14, ATR14, VWAP, volume)
├── 3. Calcola swing high/low e piano di trading (entry/SL/TP)
├── 4. Esegue 18 check Flying Wheel
└── 5. Se tutti PASS: invia ordine MARKET (o simula in DRY_RUN)
```

### 18 Controlli Flying Wheel (`src/flying_wheel/checks.py`)

| # | Controllo | Descrizione |
|---|-----------|-------------|
| 01 | Trend EMA200 | close > EMA200 → trend rialzista |
| 02 | Market Structure BOS | ultimo high rompe lo swing high recente |
| 03 | Order Block | candela bearish prima di impulso rialzista |
| 04 | Liquidity Sweep | ultimo low spazza il minimo precedente con recupero |
| 05 | FVG Imbalance | gap rialzista tra candela 1 e candela 3 |
| 06 | Fibonacci OTE | prezzo nel range 61.8%–78.6% di ritracciamento |
| 07 | RSI Oversold | RSI14 < soglia configurabile (default: 30) |
| 08 | Volume Spike | volume corrente > media 20 barre |
| 09 | ATR Volatilità | ATR% in banda accettabile (evita spike) |
| 10 | DXY Correlation | DXY bearish = favorevole per XAG (provider pluggabile) |
| 11 | Candlestick | pinbar/hammer o engulfing rialzista |
| 12 | VWAP Alignment | close > VWAP per posizione long |
| 13 | Risk/Reward >= 3 | R:R calcolato su SL/TP del piano |
| 14 | News Filter | blocca su eventi macro ad alto impatto (provider pluggabile) |
| 15 | Daily Drawdown | blocca se perdita giornaliera supera la soglia |
| 16 | Spread Check | spread bid/ask < max_spread_bps |
| 17 | Time Session | trading solo nelle ore UTC configurate |
| 18 | Overtrading Guard | limita trade/ora e perdite consecutive |

### Provider Esterni (DXY e Notizie)

I check 10 (DXY) e 14 (News) usano provider pluggabili:

- `DXY_PROVIDER=none` (default): check 10 viene **saltato** (non blocca il trading)
- `DXY_PROVIDER=url`: recupera bias DXY da un endpoint HTTP che risponde `{"bias": "bullish"|"bearish"}`
- `STRICT_EXTERNALS=0` (default): provider mancante → check passa (non bloccante)
- `STRICT_EXTERNALS=1`: provider mancante → check fallisce (blocca il trading)

### Gestione Rischio

- **Max trade/ora**: `MAX_TRADES_PER_HOUR` (default: 20)
- **Max drawdown giornaliero**: `MAX_DAILY_DRAWDOWN` (default: 2% del saldo)
- **Max perdite consecutive**: `MAX_CONSECUTIVE_LOSSES` (default: 5)
- **Spread massimo**: `MAX_SPREAD_BPS` (default: 10 basis points)
- **Sessione di trading**: ore UTC `SESSION_START_UTC`–`SESSION_END_UTC` (default: 9–22)

## Struttura del Progetto

```
Bot-argento/
├── main.py                              # Entry point — worker continuo
├── src/
│   ├── pionex_client.py                 # Client API Pionex (klines, orderbook, ordini)
│   ├── flying_wheel/
│   │   ├── engine.py                    # Motore Flying Wheel (18 controlli)
│   │   └── checks.py                    # Implementazione reale dei 18 check
│   ├── strategy/
│   │   └── bot_argento_trading.py       # DataFrame, indicatori, piano di trading
│   └── providers/
│       ├── dxy_provider.py              # Provider DXY (pluggabile)
│       └── news_provider.py             # Provider notizie (pluggabile)
├── requirements.txt
├── render.yaml                          # Configurazione deploy su Render (Worker)
├── .env.example                         # Template variabili d'ambiente
├── GUIDA_RENDER.md                      # Guida deploy su Render
└── README.md                            # Questo file
```

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `PIONEX_API_KEY` | — | API Key Pionex (**obbligatoria**) |
| `PIONEX_SECRET_KEY` | — | Secret Key Pionex (**obbligatoria**) |
| `DRY_RUN` | `1` | `0` = trading reale, `1` = simulazione |
| `SYMBOL` | `XAG_USDT` | Simbolo di trading |
| `TIMEFRAME` | `5m` | Timeframe klines |
| `LOOP_SECONDS` | `10` | Intervallo loop in secondi |
| `MICRO_TRADE_USDT` | `5` | Importo micro-trade in USDT |
| `MAX_TRADES_PER_HOUR` | `20` | Max trade per ora |
| `MAX_DAILY_DRAWDOWN` | `0.02` | Max drawdown giornaliero (2%) |
| `MAX_SPREAD_BPS` | `10` | Max spread bid/ask in basis points |
| `STRICT_EXTERNALS` | `0` | `1` = provider DXY/News bloccanti se mancanti |
| `SESSION_START_UTC` | `9` | Ora UTC inizio sessione |
| `SESSION_END_UTC` | `22` | Ora UTC fine sessione |
| `RSI_OVERSOLD` | `30` | Soglia RSI oversold |
| `MAX_CONSECUTIVE_LOSSES` | `5` | Max perdite consecutive |
| `DXY_PROVIDER` | `none` | Provider DXY: `none` o `url` |
| `DXY_URL` | — | URL API DXY (se `DXY_PROVIDER=url`) |
| `DXY_API_KEY` | — | API key provider DXY (opzionale) |
| `NEWS_PROVIDER` | `none` | Provider notizie: `none` o `url` |
| `NEWS_URL` | — | URL API notizie (se `NEWS_PROVIDER=url`) |
| `NEWS_API_KEY` | — | API key provider notizie (opzionale) |

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
# Modifica .env con le tue chiavi API reali
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
4. Aggiungi `PIONEX_API_KEY` e `PIONEX_SECRET_KEY` nelle Environment Variables
5. Fai il deploy

## Note di Sicurezza

⚠️ **Non committare mai** le chiavi API reali nel repository.
✅ Usa sempre variabili d'ambiente o il file `.env` (già escluso da `.gitignore`).
✅ Testa sempre con `DRY_RUN=1` prima di andare in produzione.
🔒 Le API key devono avere solo permesso **Trading** — **NON abilitare Withdraw**.
🔒 Ruota le API key periodicamente dal pannello Pionex.

