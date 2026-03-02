"""
Bot Argento - Flying Wheel System
==================================
Bot di trading automatico che accumula metalli preziosi (PAXG) tramite Pionex.

Flusso principale:
1. Verifica le credenziali API e le connessioni al momento dell'avvio.
2. Avvia il motore Flying Wheel a 18 controlli:
   a. Controlla i segnali istituzionali.
   b. Recupera i dati di mercato in tempo reale dall'API Pionex.
   c. Applica l'analisi 18 punti (quantum jump) per trovare asset con
      variazione di prezzo > 1.8%.
   d. Esegue micro-operazioni di acquisto (0.01 unità) sulle opportunità.
   e. Converte i profitti in PAXG (PAX Gold, token ancorato all'oro fisico)
      tramite ordini MARKET su PAXGUSD.
3. In caso di errori transitori, riprova automaticamente dopo un breve ritardo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY    -- API key dell'account Pionex
    PIONEX_SECRET_KEY -- Secret key dell'account Pionex
"""
import logging
import os
import sys
import time

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

# Secondi di pausa tra un ciclo completo e il successivo
CYCLE_SLEEP_SECONDS = 60
# Massimo ritardo (secondi) per il backoff esponenziale in caso di errori
MAX_BACKOFF_SECONDS = 300


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

    consecutive_errors = 0
    while True:
        try:
            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            elif config["dry_run"]:
                logger.info("DRY_RUN: operazione simulata completata con successo.")
            else:
                logger.info("Tutti i check superati — avvio esecuzione ordine reale.")
                # TODO: integrare le chiamate API Pionex per l'ordine effettivo

            consecutive_errors = 0
            logger.info("Prossimo ciclo tra %d secondi.", CYCLE_SLEEP_SECONDS)
            time.sleep(CYCLE_SLEEP_SECONDS)

        except Exception as exc:
            consecutive_errors += 1
            wait = min(2 ** min(consecutive_errors, 10), MAX_BACKOFF_SECONDS)
            logger.error(
                "Errore imprevisto (ciclo #%d): %s — riprovo tra %d secondi.",
                consecutive_errors,
                exc,
                wait,
            )
            time.sleep(wait)


if __name__ == "__main__":
    main()
