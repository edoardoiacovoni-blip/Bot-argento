# Bot Argento 🤖

Bot di trading automatico su Pionex (PAXG/USDT) basato sul framework **Flying Wheel a 18 punti**.

## Descrizione

Bot Argento esegue un'analisi strutturata in 18 controlli prima di effettuare operazioni di trading. In modalità `DRY_RUN` (default) il bot non esegue ordini reali, consentendo di testare la logica senza rischi.

## Struttura del Progetto

```
Bot-argento/
├── main.py                        # Entry point principale
├── src/
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

| Variabile          | Obbligatoria | Descrizione                                  |
|--------------------|:------------:|----------------------------------------------|
| `PIONEX_API_KEY`   | ✅            | API Key ottenuta dal pannello Pionex          |
| `PIONEX_SECRET_KEY`| ✅            | Secret Key ottenuta dal pannello Pionex       |
| `DRY_RUN`          | ❌            | Se `1` (default), nessun ordine reale viene eseguito |

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
🔒 Ruota le API key periodicamente dal pannello Pionex.

## Flying Wheel — 18 Controlli

Il motore Flying Wheel esegue 18 controlli sequenziali prima di ogni ciclo di trading.  
Tutti i check devono risultare `PASS` per procedere con un ordine reale.  
I dettagli dei singoli controlli sono definiti in `src/flying_wheel/checks.py`.
