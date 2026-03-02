"""
Bot Argento - Flying Wheel System
==================================
Bot di trading automatico che accumula metalli preziosi (PAXG, argento) tramite Pionex.

Flusso principale:
1. Verifica le credenziali API e le connessioni al momento dell'avvio.
2. Accumula argento (SILVER_SYMBOL) su SPOT:
   - In modalità DRY_RUN registra l'azione prevista senza inviare ordini reali.
3. Avvia il motore Flying Wheel a 18 controlli:
   a. Controlla i segnali istituzionali.
   b. Recupera i dati di mercato in tempo reale dall'API Pionex.
   c. Applica l'analisi 18 punti (quantum jump) per trovare asset con
      variazione di prezzo > 1.8%.
   d. Esegue micro-operazioni di acquisto (0.01 unità) sulle opportunità.
   e. Converte i profitti in PAXG (PAX Gold, token ancorato all'oro fisico)
      tramite ordini MARKET su PAXG_USDT.
4. In caso di errori transitori, riprova automaticamente dopo un breve ritardo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY          -- API key dell'account Pionex
    PIONEX_SECRET_KEY       -- Secret key dell'account Pionex
    SILVER_SYMBOL           -- Simbolo argento SPOT, es. XAG_USDT
    SILVER_BUY_AMOUNT_USDT  -- Importo USDT da spendere per ogni acquisto (default: 5)
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

# Parametri della procedura Cime
MICRO_TRADE_QUANTITY = 0.01       # unità base per ogni micro-acquisto
PRICE_CHANGE_THRESHOLD = 1.8     # soglia variazione % per identificare opportunità
PAXG_SYMBOL = "PAXG_USDT"       # simbolo PAXG per la conversione in oro
TOP_OPPORTUNITIES = 5            # numero massimo di asset da tradare per ciclo


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

    silver_symbol = os.environ.get("SILVER_SYMBOL", "").strip()
    if not silver_symbol:
        logger.error("Variabile d'ambiente SILVER_SYMBOL non impostata.")
        sys.exit(1)

    try:
        silver_buy_amount = float(os.environ.get("SILVER_BUY_AMOUNT_USDT", "5"))
        if silver_buy_amount <= 0:
            raise ValueError("deve essere > 0")
    except ValueError as exc:
        logger.error("SILVER_BUY_AMOUNT_USDT non valido: %s", exc)
        sys.exit(1)

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
        "silver_symbol": silver_symbol,
        "silver_buy_amount": silver_buy_amount,
    }


def accumulate_silver(config: dict, client) -> None:
    """Accumula argento su SPOT oppure simula l'acquisto in modalità DRY_RUN.

    In DRY_RUN=1 registra l'azione prevista senza inviare alcun ordine reale.
    All'avvio verifica che il simbolo esista tra i ticker disponibili; in caso
    contrario emette un avviso non bloccante.
    """
    symbol = config["silver_symbol"]
    amount = config["silver_buy_amount"]

    tickers = client.get_tickers()
    known_symbols = {t.get("symbol") for t in tickers if isinstance(t, dict)}
    if known_symbols and symbol not in known_symbols:
        logger.warning(
            "SILVER_SYMBOL '%s' non trovato tra i ticker Pionex — "
            "verifica il simbolo. Il bot continua comunque.",
            symbol,
        )

    if config["dry_run"]:
        logger.info(
            "DRY_RUN: ordine MARKET BUY simulato per %s spendendo %.4f USDT (amount=%.4f USDT)",
            symbol,
            amount,
            amount,
        )
        return

    result = client.create_order(symbol, "BUY", "MARKET", amount=amount)
    if result is not None:
        logger.info("Ordine MARKET BUY inviato per %s: %s", symbol, result)
    else:
        logger.error("Errore nell'invio dell'ordine MARKET BUY per %s.", symbol)


def find_opportunities(tickers: list) -> list:
    """Identifica i top asset con variazione di prezzo > PRICE_CHANGE_THRESHOLD%.

    :param tickers: lista di dizionari ticker restituita da get_tickers().
    :return: lista di simboli ordinata per variazione decrescente (max TOP_OPPORTUNITIES).
    """
    opportunities = []
    for ticker in tickers:
        if not isinstance(ticker, dict):
            continue
        symbol = ticker.get("symbol")
        if not symbol:
            continue
        try:
            change = float(ticker.get("change", 0))
        except (TypeError, ValueError):
            continue
        if change > PRICE_CHANGE_THRESHOLD:
            opportunities.append((symbol, change))
    opportunities.sort(key=lambda x: x[1], reverse=True)
    return [sym for sym, _ in opportunities[:TOP_OPPORTUNITIES]]


def execute_micro_trade(client, symbol: str, dry_run: bool) -> None:
    """Esegue una micro-operazione di acquisto (MICRO_TRADE_QUANTITY unità) per il simbolo indicato.

    In DRY_RUN=1 registra l'azione prevista senza inviare alcun ordine reale.
    """
    if dry_run:
        logger.info(
            "DRY_RUN: micro-acquisto simulato per %s (quantity=%.2f)",
            symbol,
            MICRO_TRADE_QUANTITY,
        )
        return
    result = client.create_order(symbol, "BUY", "MARKET", quantity=MICRO_TRADE_QUANTITY)
    if result is not None:
        logger.info("Micro-acquisto inviato per %s: %s", symbol, result)
    else:
        logger.error("Errore nel micro-acquisto per %s.", symbol)


def convert_to_gold(client, dry_run: bool) -> None:
    """Converte i profitti in PAXG tramite ordine MARKET su PAXG_USDT.

    In DRY_RUN=1 registra l'azione prevista senza inviare alcun ordine reale.
    """
    if dry_run:
        logger.info(
            "DRY_RUN: conversione in PAXG simulata (%s MARKET BUY quantity=%.2f)",
            PAXG_SYMBOL,
            MICRO_TRADE_QUANTITY,
        )
        return
    result = client.create_order(PAXG_SYMBOL, "BUY", "MARKET", quantity=MICRO_TRADE_QUANTITY)
    if result is not None:
        logger.info("Conversione in PAXG inviata: %s", result)
    else:
        logger.error("Errore nella conversione in PAXG.")


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
            accumulate_silver(config, ctx["client"])

            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            else:
                tickers = ctx["client"].get_tickers()
                opportunities = find_opportunities(tickers)
                if opportunities:
                    logger.info("Opportunità identificate: %s", opportunities)
                    for sym in opportunities:
                        execute_micro_trade(ctx["client"], sym, config["dry_run"])
                    convert_to_gold(ctx["client"], config["dry_run"])
                else:
                    logger.info(
                        "Nessuna opportunità trovata (variazione < %.1f%%).",
                        PRICE_CHANGE_THRESHOLD,
                    )
                if config["dry_run"]:
                    logger.info("DRY_RUN: operazione simulata completata con successo.")
                else:
                    logger.info("Tutti i check superati — esecuzione ordini completata.")

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
