# Istruzioni per GitHub Copilot — Bot Argento

## Panoramica del Progetto

**Bot Argento** è un bot di trading automatico Python che opera su **Pionex** per accumulare metalli preziosi (argento e PAXG/oro). Implementa il sistema **Flying Wheel a 18 controlli**: tutti i check devono risultare `PASS` prima che venga eseguito un ordine reale.

Il progetto **non è completo**: molti check in `src/flying_wheel/checks.py` sono ancora stub con `TODO` e devono essere implementati con la logica reale.

---

## Struttura del Progetto

```
Bot-argento/
├── main.py                        # Entry point: ciclo principale, accumulate_silver(), engine.run()
├── src/
│   ├── pionex_client.py           # Client API Pionex (HMAC-SHA256, GET/POST autenticati)
│   └── flying_wheel/
│       ├── engine.py              # Motore: esegue i 18 check in sequenza, restituisce bool
│       └── checks.py              # 18 funzioni check_01…check_18, da implementare
├── requirements.txt
├── render.yaml                    # Deploy su Render (Python Background Worker)
├── .env.example                   # Template variabili d'ambiente
└── README.md                      # Documentazione completa in italiano
```

---

## Convenzioni di Codice

- **Lingua**: tutta la documentazione, i commenti e i messaggi di log sono in **italiano**.
- **Python**: usare type hints ovunque (`str`, `bool`, `dict`, `float | None`, ecc.).
- **Docstring**: ogni funzione pubblica deve avere una docstring in italiano.
- **Logging**: usare `logger = logging.getLogger(__name__)` in ogni modulo; usare `logger.info/warning/error` (non `print`).
- **Nessuna dipendenza esterna non necessaria**: preferire la libreria standard Python; aggiungere pacchetti solo se strettamente necessari.
- **Gestione errori**: i metodi del client Pionex restituiscono `None` in caso di errore (mai sollevare eccezioni non gestite verso il chiamante).

---

## Pattern dei Check Flying Wheel

Ogni funzione check in `checks.py` deve:

1. Ricevere `ctx: dict` come unico parametro.
2. Restituire `tuple[bool, str]` — `(passed, motivo)`.
3. Usare `ctx.get("client")` per accedere al `PionexClient`.
4. Usare `ctx.get("config")` per accedere alla configurazione (api_key, dry_run, silver_symbol, ecc.).
5. Non sollevare eccezioni: restituire `(False, "messaggio errore")` in caso di problemi.

```python
def check_XX(ctx: dict) -> tuple[bool, str]:
    """TODO: descrizione del check."""
    client = ctx.get("client")
    # logica reale qui
    return True, "check_XX: OK"
```

---

## Variabili d'Ambiente

| Variabile                | Obbligatoria | Default | Note                                           |
|--------------------------|:------------:|---------|------------------------------------------------|
| `PIONEX_API_KEY`         | ✅            | —       | API Key Pionex                                 |
| `PIONEX_SECRET_KEY`      | ✅            | —       | Secret Key Pionex                              |
| `SILVER_SYMBOL`          | ✅            | —       | Es. `XAG_USDT`                                 |
| `SILVER_BUY_AMOUNT_USDT` | ❌            | `5`     | Importo USDT per acquisto argento              |
| `DRY_RUN`                | ❌            | `1`     | Solo `0` o `false` disabilitano il DRY_RUN     |

**DRY_RUN è sicuro per default**: qualsiasi valore diverso da `"0"` o `"false"` mantiene la modalità simulazione.

---

## Sviluppo Locale

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # aggiungere le chiavi API reali
DRY_RUN=1 python main.py
```

Non esiste ancora una suite di test: aggiungere test in una cartella `tests/` usando `pytest`.

---

## Sicurezza

- **Non committare mai** chiavi API reali (`.env` è in `.gitignore`).
- Testare sempre con `DRY_RUN=1` prima di usare `DRY_RUN=0`.
- Il `PionexClient` usa HMAC-SHA256 con timestamp per prevenire replay attack.

---

## Stato Attuale e Lavoro Rimanente

- ✅ `check_01`: verifica connessione API Pionex — **implementato**
- ⬜ `check_02`–`check_18`: tutti gli altri check sono **stub placeholder** da implementare con logica reale (saldo, prezzo, spread, volume, EMA, RSI, MACD, ATR/Bollinger, correlazione oro, notizie macro, size posizione, stop-loss, take-profit, max posizioni, limiti rischio globale).
- ⬜ `execute_micro_trade` e `convert_to_gold` menzionati nel README ma non ancora presenti nel codice.
- ⬜ Integrazione ordine reale in `main.py` (TODO al completamento dei check).
