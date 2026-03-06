# Copilot Instructions — Bot Argento

## Panoramica del Progetto

**Bot Argento** è un bot di trading automatico scritto in Python che accumula
metalli preziosi (argento tramite `SILVER_SYMBOL`, PAXG come equivalente oro)
su Pionex tramite il sistema **Flying Wheel a 18 controlli**.

## Struttura del Progetto

```
Bot-argento/
├── main.py                          # Entry point: loop principale, load_config, accumulate_silver
├── src/
│   ├── pionex_client.py             # Client REST autenticato HMAC-SHA256 per le API Pionex
│   └── flying_wheel/
│       ├── engine.py                # Motore Flying Wheel: esegue i 18 check in sequenza
│       └── checks.py                # Definizioni dei 18 check (check_01…check_18)
├── render.yaml                      # Configurazione deploy Render (Background Worker)
├── requirements.txt                 # Dipendenze Python: requests, python-dotenv
├── .env.example                     # Template variabili d'ambiente
├── GUIDA_RENDER.md                  # Guida passo-passo per il deploy su Render
└── README.md                        # Documentazione principale
```

## Come Eseguire il Progetto

```bash
# Installa le dipendenze
pip install -r requirements.txt

# Copia e configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con PIONEX_API_KEY, PIONEX_SECRET_KEY, SILVER_SYMBOL

# Esegui in modalità sicura DRY_RUN (default — nessun ordine reale)
DRY_RUN=1 python main.py

# Esegui in modalità reale (solo quando sei sicuro!)
DRY_RUN=0 python main.py
```

Non esiste una test suite automatica nel progetto; la validazione avviene
manualmente con `DRY_RUN=1`.

## Variabili d'Ambiente

| Variabile                | Obbligatoria | Default | Descrizione                                      |
|--------------------------|:------------:|---------|--------------------------------------------------|
| `PIONEX_API_KEY`         | ✅           | —       | API Key Pionex                                   |
| `PIONEX_SECRET_KEY`      | ✅           | —       | Secret Key Pionex                                |
| `SILVER_SYMBOL`          | ✅           | —       | Simbolo argento SPOT, es. `XAG_USDT`             |
| `DRY_RUN`                | ❌           | `"1"`   | `"1"` = simula (sicuro); `"0"` = trading reale   |
| `SILVER_BUY_AMOUNT_USDT` | ❌           | `"5"`   | Importo USDT per ogni acquisto di argento        |

**Sicurezza DRY_RUN**: `DRY_RUN` è safe-by-default: qualsiasi valore diverso
da `"0"` o `"false"` attiva la modalità simulazione. Non disabilitare il
DRY_RUN senza una deliberata scelta.

## Convenzioni di Codice

- **Lingua**: commenti, docstring, messaggi di log e documentazione sono scritti
  **in italiano**.
- **Stile**: segui PEP 8. Usa type hints sulle funzioni pubbliche.
- **Logging**: usa `logging.getLogger(__name__)` in ogni modulo; non usare
  `print()`.
- **Gestione errori**: le funzioni che chiamano API restituiscono `None` in caso
  di errore (non sollevano eccezioni); i chiamanti devono gestire `None`.
- **Dipendenze**: usa solo le librerie già presenti in `requirements.txt`
  (`requests`, `python-dotenv`). Non aggiungere nuove dipendenze senza
  aggiornare `requirements.txt`.

## Architettura Flying Wheel

Il motore Flying Wheel (`src/flying_wheel/engine.py`) esegue in sequenza i 18
check definiti in `src/flying_wheel/checks.py`. Ogni check riceve il
dizionario `ctx` e restituisce `(passed: bool, motivo: str)`.

Il contesto `ctx` passato a `engine.run()` contiene:
- `ctx["config"]` — configurazione caricata da `load_config()` in `main.py`
- `ctx["client"]` — istanza di `PionexClient`

Se tutti i 18 check passano (`True`), il motore restituisce `True` e il ciclo
procede; altrimenti il ciclo viene saltato.

I check attualmente stub (check_02…check_18) devono essere implementati uno
alla volta, ognuno con la propria logica e aggiungendo al contesto `ctx` i
dati necessari ai check successivi.

## Client Pionex (`src/pionex_client.py`)

- `get_tickers()` — lista tutti i ticker disponibili
- `get_ticker(symbol)` — dati per un singolo ticker
- `create_order(symbol, side, order_type, quantity, amount)` — crea un ordine
- `test_connection()` — verifica raggiungibilità API (usato da check_01)

L'autenticazione è HMAC-SHA256: timestamp e firma vanno sempre nella query
string; il payload degli ordini POST va nel body JSON.

## Deploy su Render

Il file `render.yaml` configura automaticamente un **Background Worker** Python.
Consulta `GUIDA_RENDER.md` per la procedura completa.
Il valore di default `DRY_RUN=1` è impostato direttamente in `render.yaml`;
per il trading reale occorre impostare `DRY_RUN=0` nelle Environment Variables
del dashboard Render.
