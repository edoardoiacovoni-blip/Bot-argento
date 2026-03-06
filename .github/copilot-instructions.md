# Copilot Instructions for Bot Argento

## Project Overview

Bot Argento is an automated trading bot for Pionex that accumulates precious metals (PAXG gold token and silver) using the **Flying Wheel** 18-check framework. The bot runs as a Python background worker (deployed on Render) and is safe-by-default through its `DRY_RUN` mode.

## Repository Structure

```
Bot-argento/
├── main.py                    # Entry point: config loading, main loop, silver accumulation
├── src/
│   ├── pionex_client.py       # Pionex REST API client (HMAC-SHA256 auth)
│   └── flying_wheel/
│       ├── engine.py          # Runs all 18 checks sequentially
│       └── checks.py          # Individual check functions (check_01 … check_18)
├── render.yaml                # Render Worker deployment config
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variable template
```

## Language & Documentation

- All **code comments, docstrings, log messages, and documentation** are written in **Italian**.
- Follow this convention for any new code or documentation you add.

## Tech Stack

- **Python 3.11+** — use modern syntax (e.g. `X | Y` union types, `tuple[bool, str]` generics)
- **requests** — HTTP calls to the Pionex REST API
- **python-dotenv** — optional local `.env` loading (Render injects env vars directly)
- No test framework is currently set up

## Key Conventions

### DRY_RUN Safety
- `DRY_RUN` defaults to `"1"` (safe). Only `"0"` or `"false"` disables it.
- Always guard real order execution behind `if not config["dry_run"]`.
- In DRY_RUN mode, log the intended action with the `DRY_RUN:` prefix.

### Flying Wheel Checks
- Each check function lives in `src/flying_wheel/checks.py` and has the signature:
  ```python
  def check_NN(ctx: dict) -> tuple[bool, str]:
  ```
- Return `(True, "check_NN: <descrizione successo>")` on PASS.
- Return `(False, "check_NN: <motivo fallimento>")` on FAIL.
- The `ctx` dict contains at minimum `{"config": dict, "client": PionexClient}`.
- Many checks are still stubs (`return True, "check_NN: placeholder PASS"`); implement them one at a time without breaking the engine.

### Pionex API Client
- All API calls go through `PionexClient` in `src/pionex_client.py`.
- Authentication is HMAC-SHA256; never embed credentials in code — always read from env vars.
- Methods return the parsed JSON dict on success, or `None` on error; callers must handle `None`.

### Error Handling
- Use the module-level `logger = logging.getLogger(__name__)` pattern.
- Transient errors are retried with exponential backoff capped at `MAX_BACKOFF_SECONDS`.
- Fatal config errors (missing env vars) call `sys.exit(1)` with a clear Italian message.

## Environment Variables

| Variable               | Required | Default | Description                          |
|------------------------|:--------:|:-------:|--------------------------------------|
| `PIONEX_API_KEY`       | ✅       | —       | Pionex API key                       |
| `PIONEX_SECRET_KEY`    | ✅       | —       | Pionex secret key                    |
| `SILVER_SYMBOL`        | ✅       | —       | Silver spot symbol in Pionex format, e.g. `XAG_USDT` (underscore separator) |
| `DRY_RUN`              | ❌       | `"1"`   | `"1"` = simulate, `"0"` = real                                               |
| `SILVER_BUY_AMOUNT_USDT` | ❌     | `"5"`   | USDT to spend per silver buy                                                 |

## Security

- **Never** commit real API keys or secrets.
- `.env` is already in `.gitignore`.
- Rotate API keys periodically from the Pionex dashboard.
- Always test with `DRY_RUN=1` before switching to live trading.
