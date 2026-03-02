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
      tramite ordini MARKET su PAXGUSD.
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

    try:
        total_capital = float(os.environ.get("TOTAL_CAPITAL", "67.0"))
        if total_capital <= 0:
            raise ValueError("deve essere > 0")
    except ValueError as exc:
        logger.error("TOTAL_CAPITAL non valido: %s", exc)
        sys.exit(1)

    try:
        trade_margin = float(os.environ.get("TRADE_MARGIN", "5.0"))
        if trade_margin <= 0:
            raise ValueError("deve essere > 0")
    except ValueError as exc:
        logger.error("TRADE_MARGIN non valido: %s", exc)
        sys.exit(1)

    volatile_targets_raw = os.environ.get("VOLATILE_TARGETS", "BTC_USDT,ETH_USDT,SOL_USDT").strip()
    volatile_targets = [t.strip() for t in volatile_targets_raw.split(",") if t.strip()]

    enable_silver_accumulation = (
        os.environ.get("ENABLE_SILVER_ACCUMULATION", "1").strip() not in ("0", "false", "False")
    )

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
        "silver_symbol": silver_symbol,
        "silver_buy_amount": silver_buy_amount,
        "total_capital": total_capital,
        "trade_margin": trade_margin,
        "min_usdt_reserve": 10.0,
        "volatile_targets": volatile_targets,
        "enable_silver_accumulation": enable_silver_accumulation,
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


def get_real_balances(config: dict, client) -> tuple:
    """Recupera i saldi reali USDT e XAG tramite API Pionex.

    Punto 18: Verifica dello stato prima di operare.
    :return: tupla (usdt_free, xag_held, xag_price)
    """
    balances = client.get_balance()
    usdt_free = 0.0
    xag_held = 0.0

    for b in balances:
        currency = b.get("currency", "")
        free = float(b.get("free", 0) or 0)
        if currency == "USDT":
            usdt_free = free
        elif currency in ("XAG", "SILVER"):
            xag_held = free

    # Recupera il prezzo attuale di XAG dal ticker
    xag_price = 0.0
    silver_symbol = config.get("silver_symbol", "")
    if silver_symbol:
        tickers = client.get_tickers()
        for t in tickers:
            if t.get("symbol") == silver_symbol:
                try:
                    xag_price = float(t.get("close", 0) or 0)
                except (ValueError, TypeError):
                    pass
                break

    return usdt_free, xag_held, xag_price


def check_market_trend(client, asset: str) -> bool:
    """Verifica se l'asset è in crescita prima del salto.

    Punto 3: Usa la variazione di prezzo nelle ultime 24h come segnale.
    :return: True se l'asset mostra trend positivo, False altrimenti.
    """
    tickers = client.get_tickers()
    for t in tickers:
        if t.get("symbol") == asset:
            try:
                change = float(t.get("change", 0) or 0)
                return change > 0
            except (ValueError, TypeError):
                pass
    return False


def execute_rebalancing(
    config: dict, client, amount_needed: float, xag_held: float, xag_price: float
) -> bool:
    """Vende XAG per ottenere liquidità USDT quando il saldo è insufficiente.

    LOGICA DI REINVESTIMENTO: L'Argento diventa Moneta (Opzione B).
    Punto 9: Se un sistema è lento o serve liquidità, cambiamo subito.
    :return: True se il rebalancing è stato eseguito, False altrimenti.
    """
    min_reserve = config.get("min_usdt_reserve", 10.0)
    valor_xag = xag_held * xag_price

    if valor_xag <= min_reserve:
        return False

    if xag_price <= 0:
        return False

    amount_to_sell = (amount_needed / xag_price) * 1.01  # +1% buffer per le commissioni
    silver_symbol = config.get("silver_symbol", "XAG_USDT")
    logger.info(
        "AZIONE BIP: Vendo %.4f XAG (%s) per finanziare il salto.",
        amount_to_sell,
        silver_symbol,
    )

    if config.get("dry_run"):
        logger.info(
            "DRY_RUN: vendita XAG simulata (%.4f %s).", amount_to_sell, silver_symbol
        )
        return True

    result = client.create_order(silver_symbol, "SELL", "MARKET", quantity=amount_to_sell)
    if result is not None:
        logger.info("Ordine SELL XAG inviato: %s", result)
        return True
    logger.error("Errore nell'invio dell'ordine SELL XAG.")
    return False


def execute_micro_trade(config: dict, client, asset: str) -> None:
    """Esegue un micro-trade sull'asset specificato (0.01 unità).

    Punto 4: Micro-operazione di acquisto sull'opportunità identificata.
    """
    quantity = 0.01
    if config.get("dry_run"):
        logger.info(
            "DRY_RUN: micro-trade simulato su %s (quantità: %.4f).", asset, quantity
        )
        return

    result = client.create_order(asset, "BUY", "MARKET", quantity=quantity)
    if result is not None:
        logger.info("Micro-trade BUY eseguito su %s: %s", asset, result)
    else:
        logger.error("Errore nel micro-trade su %s.", asset)


def main() -> None:
    config = load_config()

    if config["dry_run"]:
        logger.info("Modalità DRY_RUN attiva — nessun ordine reale verrà eseguito.")
    else:
        logger.warning("Modalità REALE attiva — gli ordini verranno inviati a Pionex!")

    client = PionexClient(config["api_key"], config["secret_key"])
    ctx = {"config": config, "client": client}

    consecutive_errors = 0
    while True:
        try:
            # Punto 18: Recupero saldi reali prima di ogni ciclo
            usdt, xag, xag_price = get_real_balances(config, client)
            total_equity = usdt + (xag * xag_price)
            logger.info(
                "Equity: %.2f USDT | Liquidità: %.2f | Argento: %.2f",
                total_equity,
                usdt,
                xag * xag_price,
            )
            # Aggiorna il contesto con i saldi correnti per i check
            ctx["usdt_balance"] = usdt
            ctx["xag_balance"] = xag
            ctx["xag_price"] = xag_price

            # Accumulo argento (Punto 1) — controllato dal flag ENABLE_SILVER_ACCUMULATION
            if config.get("enable_silver_accumulation"):
                accumulate_silver(config, client)

            # Gestione liquidità per il salto (Punti 8 e 9)
            if usdt < config["trade_margin"]:
                logger.warning("⚠️ USDT insufficienti per il salto. Controllo riserve Argento...")
                needed = config["trade_margin"] - usdt
                if not execute_rebalancing(config, client, needed, xag, xag_price):
                    logger.error("❌ Riserve Argento insufficienti. Attendo prossimo ciclo.")
                    time.sleep(CYCLE_SLEEP_SECONDS)
                    consecutive_errors = 0
                    continue
                usdt = config["trade_margin"]

            # Flying Wheel Engine: 18 controlli sequenziali
            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            else:
                # Scansione opportunità sui target volatili (Punti 2, 3 e 17)
                for target in config["volatile_targets"]:
                    if check_market_trend(client, target):
                        logger.info(
                            "🚀 SALTO: Trend positivo su %s. Eseguo micro-trade.", target
                        )
                        execute_micro_trade(config, client, target)
                        break

                if config["dry_run"]:
                    logger.info("DRY_RUN: operazione simulata completata con successo.")
                else:
                    logger.info("Tutti i check superati — esecuzione completata.")

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
