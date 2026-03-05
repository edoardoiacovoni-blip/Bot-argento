"""
Bot Argento - Flying Wheel System
==================================
Bot di trading automatico che accumula metalli preziosi (PAXG, argento) tramite Pionex.

Flusso principale:
1. Verifica le credenziali API e le connessioni al momento dell'avvio.
2. Se USDT scende sotto MIN_USDT_RESERVE, vende XAG per ripristinare la liquidità
   (execute_rebalancing_under_10). Rispetta un cooldown di REBALANCE_COOLDOWN_SEC secondi.
3. Opzionalmente accumula argento (SILVER_SYMBOL) su SPOT se ENABLE_SILVER_ACCUMULATION=1:
   - In modalità DRY_RUN registra l'azione prevista senza inviare ordini reali.
4. Avvia il motore Flying Wheel a 18 controlli:
   a. Controlla i segnali istituzionali.
   b. Recupera i dati di mercato in tempo reale dall'API Pionex.
   c. Applica l'analisi 18 punti (quantum jump) per trovare asset con
      variazione di prezzo > 1.8%.
   d. Esegue micro-operazioni di acquisto (0.01 unità) sulle opportunità.
   e. Converte i profitti in PAXG (PAX Gold, token ancorato all'oro fisico)
      tramite ordini MARKET su PAXGUSD.
5. In caso di errori transitori, riprova automaticamente dopo un breve ritardo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY              -- API key dell'account Pionex
    PIONEX_SECRET_KEY           -- Secret key dell'account Pionex
    SILVER_SYMBOL               -- Simbolo argento SPOT, es. XAG_USDT
    SILVER_BUY_AMOUNT_USDT      -- Importo USDT da spendere per ogni acquisto (default: 5)

Variabili d'ambiente opzionali:
    ENABLE_SILVER_ACCUMULATION  -- 1 per abilitare acquisti automatici di argento (default: 0)
    MIN_USDT_RESERVE            -- Soglia USDT minima prima del rebalancing (default: 10.0)
    TARGET_USDT_AFTER_REBALANCE -- Obiettivo USDT dopo rebalancing (default: MIN_USDT_RESERVE)
    REBALANCE_COOLDOWN_SEC      -- Cooldown in secondi tra vendite XAG (default: 300)
    MIN_XAG_NOTIONAL_TO_SELL    -- Notional minimo USDT per vendita XAG (default: 2.0)
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

    enable_silver_accumulation = os.environ.get(
        "ENABLE_SILVER_ACCUMULATION", "0"
    ).strip() in ("1", "true", "True")

    try:
        min_usdt_reserve = float(os.environ.get("MIN_USDT_RESERVE", "10.0"))
    except ValueError as exc:
        logger.warning(
            "MIN_USDT_RESERVE non valido (%r), uso default 10.0: %s",
            os.environ.get("MIN_USDT_RESERVE"),
            exc,
        )
        min_usdt_reserve = 10.0

    try:
        target_usdt_after_rebalance = float(
            os.environ.get("TARGET_USDT_AFTER_REBALANCE", str(min_usdt_reserve))
        )
    except ValueError as exc:
        logger.warning(
            "TARGET_USDT_AFTER_REBALANCE non valido (%r), uso fallback %s: %s",
            os.environ.get("TARGET_USDT_AFTER_REBALANCE"),
            min_usdt_reserve,
            exc,
        )
        target_usdt_after_rebalance = min_usdt_reserve

    try:
        rebalance_cooldown_sec = int(os.environ.get("REBALANCE_COOLDOWN_SEC", "300"))
    except ValueError as exc:
        logger.warning(
            "REBALANCE_COOLDOWN_SEC non valido (%r), uso default 300: %s",
            os.environ.get("REBALANCE_COOLDOWN_SEC"),
            exc,
        )
        rebalance_cooldown_sec = 300

    try:
        min_xag_notional_to_sell = float(
            os.environ.get("MIN_XAG_NOTIONAL_TO_SELL", "2.0")
        )
    except ValueError as exc:
        logger.warning(
            "MIN_XAG_NOTIONAL_TO_SELL non valido (%r), uso default 2.0: %s",
            os.environ.get("MIN_XAG_NOTIONAL_TO_SELL"),
            exc,
        )
        min_xag_notional_to_sell = 2.0

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
        "silver_symbol": silver_symbol,
        "silver_buy_amount": silver_buy_amount,
        "enable_silver_accumulation": enable_silver_accumulation,
        "min_usdt_reserve": min_usdt_reserve,
        "target_usdt_after_rebalance": target_usdt_after_rebalance,
        "rebalance_cooldown_sec": rebalance_cooldown_sec,
        "min_xag_notional_to_sell": min_xag_notional_to_sell,
    }


def accumulate_silver(config: dict, client) -> None:
    """Accumula argento su SPOT oppure simula l'acquisto in modalità DRY_RUN.

    Viene eseguita solo se ENABLE_SILVER_ACCUMULATION=1. In DRY_RUN=1 registra
    l'azione prevista senza inviare alcun ordine reale. All'avvio verifica che
    il simbolo esista tra i ticker disponibili; in caso contrario emette un
    avviso non bloccante.
    """
    if not config.get("enable_silver_accumulation"):
        logger.debug("ENABLE_SILVER_ACCUMULATION non attivo — acquisto argento saltato.")
        return

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


# Epsilon per confronti floating-point nelle soglie di notional
_FLOAT_EPSILON = 1e-6
# Timestamp (epoch) dell'ultima vendita XAG per il cooldown
_last_xag_sell_time: float = 0.0


def execute_rebalancing_under_10(config: dict, client, balances: dict) -> dict:
    """Vende XAG per ripristinare la liquidità USDT quando scende sotto MIN_USDT_RESERVE.

    Regole:
    - Trigger: usdt_free < MIN_USDT_RESERVE.
    - Vende il minimo tra la quantità necessaria e tutto l'XAG disponibile.
    - Se il notional da vendere è < MIN_XAG_NOTIONAL_TO_SELL, non vende.
    - Rispetta un cooldown di REBALANCE_COOLDOWN_SEC secondi tra vendite.
    - Dopo la vendita, rilegge i saldi reali tramite get_real_balances().

    :param config:   configurazione corrente.
    :param client:   istanza di PionexClient.
    :param balances: saldi correnti {asset: {"free": float, "locked": float}}.
    :return: saldi aggiornati (invariati se non è stata eseguita alcuna vendita).
    """
    global _last_xag_sell_time

    min_reserve = config["min_usdt_reserve"]
    target = config["target_usdt_after_rebalance"]
    cooldown = config["rebalance_cooldown_sec"]
    min_notional = config["min_xag_notional_to_sell"]
    silver_symbol = config["silver_symbol"]  # es. "XAG_USDT"

    usdt_free = balances.get("USDT", {}).get("free", 0.0)

    if usdt_free >= min_reserve:
        return balances

    logger.info(
        "REBALANCING: USDT disponibile %.4f < soglia minima %.4f — valutazione vendita XAG.",
        usdt_free,
        min_reserve,
    )

    # Cooldown
    now = time.time()
    elapsed = now - _last_xag_sell_time
    if elapsed < cooldown:
        remaining = cooldown - elapsed
        logger.info(
            "REBALANCING: cooldown attivo — prossima vendita XAG tra %.0f secondi.",
            remaining,
        )
        return balances

    # Ricava l'asset base dal simbolo (es. "XAG" da "XAG_USDT")
    parts = silver_symbol.split("_")
    if len(parts) < 2:
        logger.error(
            "REBALANCING: formato simbolo non valido '%s' (atteso BASE_QUOTE) — vendita annullata.",
            silver_symbol,
        )
        return balances
    base_asset = parts[0]
    xag_free = balances.get(base_asset, {}).get("free", 0.0)
    if xag_free <= 0:
        logger.warning("REBALANCING: nessun %s disponibile da vendere.", base_asset)
        return balances

    # Prezzo XAG corrente
    tickers = client.get_tickers()
    xag_price: float = 0.0
    for t in tickers:
        if isinstance(t, dict) and t.get("symbol") == silver_symbol:
            try:
                xag_price = float(t.get("close", t.get("price", 0)))
            except (TypeError, ValueError):
                xag_price = 0.0
            break

    if xag_price <= 0:
        logger.warning(
            "REBALANCING: impossibile ottenere il prezzo di %s — vendita annullata.",
            silver_symbol,
        )
        return balances

    xag_value_usdt = xag_free * xag_price
    amount_needed_usdt = target - usdt_free
    sell_notional = min(amount_needed_usdt, xag_value_usdt)

    if sell_notional < min_notional:
        logger.info(
            "REBALANCING: notional da vendere %.4f USDT < minimo %.4f USDT — vendita saltata.",
            sell_notional,
            min_notional,
        )
        return balances

    selling_all = sell_notional >= xag_value_usdt - _FLOAT_EPSILON
    if selling_all:
        logger.warning(
            "REBALANCING: XAG insufficiente per tornare a %.4f USDT — "
            "vendita di TUTTO il %s disponibile (%.6f %s, ~%.4f USDT).",
            target,
            base_asset,
            xag_free,
            base_asset,
            xag_value_usdt,
        )
    else:
        logger.info(
            "REBALANCING: vendita parziale di %s per ~%.4f USDT "
            "(USDT attuale %.4f → obiettivo %.4f).",
            base_asset,
            sell_notional,
            usdt_free,
            target,
        )

    if config["dry_run"]:
        logger.info(
            "DRY_RUN: ordine MARKET SELL simulato per %s — notional %.4f USDT.",
            silver_symbol,
            sell_notional,
        )
        _last_xag_sell_time = now
        # In DRY_RUN non ci sono saldi reali da rileggere; restituisce invariati
        return balances

    result = client.create_order(silver_symbol, "SELL", "MARKET", amount=sell_notional)
    if result is not None:
        logger.info("REBALANCING: ordine SELL eseguito per %s: %s", silver_symbol, result)
    else:
        logger.error(
            "REBALANCING: errore nell'invio dell'ordine SELL per %s.", silver_symbol
        )
        return balances

    _last_xag_sell_time = now

    # Rilegge i saldi reali dopo la vendita
    updated = client.get_real_balances()
    if updated:
        logger.info(
            "REBALANCING: saldi aggiornati — USDT free: %.4f",
            updated.get("USDT", {}).get("free", 0.0),
        )
        return updated

    logger.warning("REBALANCING: impossibile rileggere i saldi reali dopo la vendita.")
    return balances


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
            # 1. Leggi i saldi reali dal exchange
            balances = client.get_real_balances()
            if not balances and not config["dry_run"]:
                logger.warning(
                    "Impossibile leggere i saldi reali — ciclo saltato per sicurezza."
                )
                time.sleep(CYCLE_SLEEP_SECONDS)
                continue

            # 2. Rebalancing liquidità: vendi XAG se USDT < MIN_USDT_RESERVE
            balances = execute_rebalancing_under_10(config, client, balances)

            # 3. Accumulo argento (opzionale, se ENABLE_SILVER_ACCUMULATION=1)
            accumulate_silver(config, client)

            # 4. Flying Wheel engine (18 check + micro-trade)
            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            elif config["dry_run"]:
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
