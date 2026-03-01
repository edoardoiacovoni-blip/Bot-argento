"""
Bot Argento - Flying Wheel System
==================================
Bot di trading automatico che accumula argento (SPOT) tramite Pionex.

Flusso principale:
1. Verifica le credenziali API e le connessioni al momento dell'avvio.
2. Valida che il simbolo argento (SILVER_SYMBOL) sia configurato.
3. Avvia il motore Flying Wheel a 18 controlli:
   a. Controlla i segnali istituzionali.
   b. Recupera i dati di mercato in tempo reale dall'API Pionex.
   c. Applica l'analisi 18 punti (quantum jump) per trovare asset con
      variazione di prezzo > 1.8%.
   d. Esegue micro-operazioni di acquisto sulle opportunità.
   e. Accumula argento tramite ordine MARKET su SILVER_SYMBOL usando
      SILVER_BUY_AMOUNT_USDT come importo in USDT.
4. In caso di errori transitori, riprova automaticamente dopo un breve ritardo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY           -- API key dell'account Pionex
    PIONEX_SECRET_KEY        -- Secret key dell'account Pionex
    SILVER_SYMBOL            -- Coppia SPOT argento su Pionex (es. XAG_USDT)
    SILVER_BUY_AMOUNT_USDT   -- Importo in USDT per ogni acquisto di argento (default: 10)
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
    silver_symbol = os.environ.get("SILVER_SYMBOL", "").strip()

    missing = []
    if not api_key:
        missing.append("PIONEX_API_KEY")
    if not secret_key:
        missing.append("PIONEX_SECRET_KEY")
    if not silver_symbol:
        missing.append("SILVER_SYMBOL")
    if missing:
        logger.error("Variabili d'ambiente mancanti: %s", ", ".join(missing))
        logger.error("Copia .env.example in .env e inserisci le tue chiavi API.")
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "1").strip() not in ("0", "false", "False")

    try:
        buy_amount = float(os.environ.get("SILVER_BUY_AMOUNT_USDT", "10").strip())
        if buy_amount <= 0:
            raise ValueError
    except ValueError:
        logger.error("SILVER_BUY_AMOUNT_USDT deve essere un numero positivo. Es: 10")
        sys.exit(1)

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
        "silver_symbol": silver_symbol,
        "buy_amount_usdt": buy_amount,
    }


def validate_silver_symbol(client, symbol: str) -> bool:
    """Verifica che SILVER_SYMBOL sia presente tra i ticker Pionex.

    :return: True se il simbolo è trovato, False altrimenti.
    """
    tickers = client.get_tickers(symbol=symbol)
    if tickers:
        logger.info("Simbolo argento '%s' trovato su Pionex ✅", symbol)
        return True
    # Fallback: simbolo non trovato tra i ticker (o errore API)
    logger.warning(
        "Simbolo argento '%s' non trovato tra i ticker Pionex. "
        "Verifica SILVER_SYMBOL nelle variabili d'ambiente.",
        symbol,
    )
    return False


def accumulate_silver(client, symbol: str, amount_usdt: float, dry_run: bool) -> None:
    """Esegue un ordine MARKET BUY per accumulare argento SPOT.

    :param client:      istanza di PionexClient
    :param symbol:      coppia SPOT argento, es. 'XAG_USDT'
    :param amount_usdt: importo in USDT da spendere
    :param dry_run:     se True, registra l'operazione senza inviarla
    """
    if dry_run:
        logger.info(
            "DRY_RUN: ordine simulato — BUY %s con %.2f USDT (nessun ordine inviato).",
            symbol,
            amount_usdt,
        )
        return

    logger.info("Invio ordine MARKET BUY %s per %.2f USDT …", symbol, amount_usdt)
    result = client.create_order(
        symbol=symbol,
        side="BUY",
        order_type="MARKET",
        amount=amount_usdt,
    )
    if result:
        logger.info("Ordine argento eseguito con successo: %s", result)
    else:
        logger.error("Ordine argento fallito — controlla le credenziali e il saldo USDT.")


def main() -> None:
    config = load_config()

    if config["dry_run"]:
        logger.info("Modalità DRY_RUN attiva — nessun ordine reale verrà eseguito.")
    else:
        logger.warning("Modalità REALE attiva — gli ordini verranno inviati a Pionex!")

    client = PionexClient(config["api_key"], config["secret_key"])
    ctx = {"config": config, "client": client}

    # Validazione simbolo argento all'avvio
    validate_silver_symbol(client, config["silver_symbol"])

    all_passed = engine.run(ctx)

    if not all_passed:
        logger.warning("Flying Wheel non completato: operazione annullata.")
        return

    accumulate_silver(
        client=client,
        symbol=config["silver_symbol"],
        amount_usdt=config["buy_amount_usdt"],
        dry_run=config["dry_run"],
    )


if __name__ == "__main__":
    main()
