"""
Bot Argento — Entry point principale.

Legge le credenziali Pionex da variabili d'ambiente e avvia il motore
Flying Wheel a 18 controlli. In modalità DRY_RUN nessun ordine reale
viene eseguito.
"""
import logging
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opzionale in produzione (Render inietta le env vars)

from src.flying_wheel import engine
from src.pionex_client import PionexClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carica e valida la configurazione da variabili d'ambiente."""
    api_key = os.environ.get("PIONEX_API_KEY", "").strip()
    secret_key = os.environ.get("PIONEX_SECRET_KEY", "").strip()

    missing = []
    if not api_key:
        missing.append("PIONEX_API_KEY")
    if not secret_key:
        missing.append("PIONEX_SECRET_KEY")
    if missing:
        logger.error("Variabili d'ambiente mancanti: %s", ", ".join(missing))
        logger.error("Copia .env.example in .env e inserisci le tue chiavi API.")
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "1").strip() not in ("0", "false", "False")

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
    }


def main() -> None:
    config = load_config()

    if config["dry_run"]:
        logger.info("Modalità DRY_RUN attiva — nessun ordine reale verrà eseguito.")
    else:
        logger.warning("Modalità REALE attiva — gli ordini verranno inviati a Pionex!")

    ctx = {"config": config, "client": PionexClient(config["api_key"], config["secret_key"])}
    all_passed = engine.run(ctx)

    if not all_passed:
        logger.warning("Flying Wheel non completato: operazione annullata.")
        return

    if config["dry_run"]:
        logger.info("DRY_RUN: operazione simulata completata con successo.")
    else:
        logger.info("Tutti i check superati — avvio esecuzione ordine reale.")
        # TODO: integrare le chiamate API Pionex per l'ordine effettivo


if __name__ == "__main__":
    main()
