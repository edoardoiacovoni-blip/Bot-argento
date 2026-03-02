"""
Bot Argento - Flying Wheel System (Fusione 18 Punti)
=====================================================
Bot di trading automatico che accumula argento (XAG) e opera sui mercati volatili
tramite Pionex, seguendo il framework Flying Wheel a 18 controlli.

Flusso principale:
1. Verifica le credenziali API e le connessioni al momento dell'avvio.
2. Recupera i saldi reali: USDT liberi, quantità XAG e prezzo XAG (Punto 18).
3. Gestione liquidità (Punti 8 & 9):
   - Se USDT < TRADE_MARGIN, vende XAG per finanziare il salto (execute_rebalancing).
4. Accumula argento (SILVER_SYMBOL) su SPOT se ENABLE_SILVER_ACCUMULATION=1:
   - In modalità DRY_RUN registra l'azione prevista senza inviare ordini reali.
5. Avvia il motore Flying Wheel a 18 controlli:
   a. Controlla i segnali istituzionali.
   b. Recupera i dati di mercato in tempo reale dall'API Pionex.
   c. Applica l'analisi 18 punti (quantum jump) per trovare asset con
      variazione di prezzo > 1.8%.
   d. Esegue micro-operazioni di acquisto (0.01 unità) sulle opportunità.
   e. Converte i profitti in argento tramite accumulate_silver.
6. Scansione opportunità sui target volatili (Punti 2, 3 & 17):
   - Verifica trend positivo (EMA/RSI placeholder) su VOLATILE_TARGETS.
   - Esegue micro-trade sul primo asset in trend positivo.
7. In caso di errori transitori, riprova automaticamente dopo un breve ritardo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY              -- API key dell'account Pionex
    PIONEX_SECRET_KEY           -- Secret key dell'account Pionex
    SILVER_SYMBOL               -- Simbolo argento SPOT, es. XAG_USDT
    SILVER_BUY_AMOUNT_USDT      -- Importo USDT per ogni acquisto di argento (default: 5)
    TOTAL_CAPITAL               -- Capitale totale gestito in USDT (default: 67.0)
    TRADE_MARGIN                -- Soglia minima USDT per eseguire un salto (default: 5.0)
    MIN_USDT_RESERVE            -- Soglia minima valore XAG prima di vendere (default: 10.0)
    ENABLE_SILVER_ACCUMULATION  -- 1 = accumula argento ogni ciclo (default: 1)
    VOLATILE_TARGETS            -- Target volatili separati da virgola (default: BTC_USDT,ETH_USDT,SOL_USDT)
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
    if "_" not in silver_symbol:
        logger.error(
            "SILVER_SYMBOL '%s' non valido: deve avere il formato BASE_QUOTE, es. XAG_USDT.",
            silver_symbol,
        )
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
        trade_margin = float(os.environ.get("TRADE_MARGIN", "5.0"))
        min_usdt_reserve = float(os.environ.get("MIN_USDT_RESERVE", "10.0"))
        micro_trade_quantity = float(os.environ.get("MICRO_TRADE_QUANTITY", "0.01"))
        if micro_trade_quantity <= 0:
            raise ValueError("MICRO_TRADE_QUANTITY deve essere > 0")
    except ValueError as exc:
        logger.error("Configurazione capitale non valida: %s", exc)
        sys.exit(1)

    enable_silver_accumulation = (
        os.environ.get("ENABLE_SILVER_ACCUMULATION", "1").strip() not in ("0", "false", "False")
    )
    volatile_targets_env = os.environ.get("VOLATILE_TARGETS", "BTC_USDT,ETH_USDT,SOL_USDT").strip()
    volatile_targets = [t.strip() for t in volatile_targets_env.split(",") if t.strip()]

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "dry_run": dry_run,
        "silver_symbol": silver_symbol,
        "silver_buy_amount": silver_buy_amount,
        "total_capital": total_capital,
        "trade_margin": trade_margin,
        "min_usdt_reserve": min_usdt_reserve,
        "micro_trade_quantity": micro_trade_quantity,
        "enable_silver_accumulation": enable_silver_accumulation,
        "volatile_targets": volatile_targets,
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


def get_real_balances(config: dict, client) -> tuple[float, float, float]:
    """Punto 18: Recupera i saldi reali — USDT liberi, quantità XAG e prezzo XAG.

    :return: (usdt_free, xag_held, xag_price)
    """
    usdt_free = 0.0
    xag_held = 0.0
    xag_price = 0.0

    safe_coin = config["silver_symbol"].split("_")[0]  # es. "XAG" da "XAG_USDT"

    balances = client.get_account_balance()
    for b in balances:
        coin = b.get("coin", "")
        if coin == "USDT":
            usdt_free = float(b.get("free", 0.0))
        elif coin == safe_coin:
            xag_held = float(b.get("free", 0.0))

    tickers = client.get_tickers()
    for t in tickers:
        if t.get("symbol") == config["silver_symbol"]:
            try:
                xag_price = float(t.get("close", 0.0))
            except (TypeError, ValueError):
                xag_price = 0.0
            break

    return usdt_free, xag_held, xag_price


def check_market_trend(client, asset: str) -> bool:
    """Punto 3: Verifica se l'asset è in trend positivo (placeholder EMA/RSI).

    Restituisce True se la variazione di prezzo nelle ultime 24h è positiva.
    """
    tickers = client.get_tickers()
    for t in tickers:
        if t.get("symbol") == asset:
            try:
                change = float(t.get("change", 0.0))
                return change > 0
            except (TypeError, ValueError):
                return False
    logger.warning("Asset %s non trovato nei ticker.", asset)
    return False


def execute_rebalancing(
    config: dict, client, amount_needed: float, xag_held: float, xag_price: float
) -> bool:
    """Punti 8 & 9: Vende XAG per finanziare il trade quando USDT è insufficiente.

    Logica di reinvestimento: L'Argento diventa Moneta (Opzione B).
    Procede solo se il valore XAG supera la soglia MIN_USDT_RESERVE.
    """
    if xag_price <= 0:
        logger.warning("Prezzo XAG non disponibile, impossibile eseguire rebalancing.")
        return False

    xag_value = xag_held * xag_price
    if xag_value > config["min_usdt_reserve"]:
        amount_to_sell = amount_needed / xag_price
        silver_symbol = config["silver_symbol"]
        if config["dry_run"]:
            logger.info(
                "DRY_RUN: AZIONE BIP: Vendo %.4f %s per finanziare il salto.",
                amount_to_sell,
                silver_symbol,
            )
            return True
        result = client.create_order(silver_symbol, "SELL", "MARKET", quantity=amount_to_sell)
        if result is not None:
            logger.info(
                "Rebalancing: venduto %.4f %s (valore: %.2f USDT).",
                amount_to_sell,
                silver_symbol,
                amount_needed,
            )
            return True
        logger.error("Errore nel rebalancing: vendita %s fallita.", silver_symbol)
        return False

    logger.warning(
        "Riserve XAG insufficienti per rebalancing (valore: %.2f USDT, soglia: %.2f USDT).",
        xag_value,
        config["min_usdt_reserve"],
    )
    return False


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
            # Punto 18: Recupera i saldi reali prima di ogni ciclo
            usdt, xag, xag_price = get_real_balances(config, client)
            total_equity = usdt + (xag * xag_price)
            logger.info(
                "Equity: %.2f USDT | Liquidità: %.2f | Argento: %.2f USDT",
                total_equity,
                usdt,
                xag * xag_price,
            )

            # Aggiorna il contesto con i saldi attuali (usati dai check 02, 03, 04)
            ctx.update({"usdt": usdt, "xag": xag, "xag_price": xag_price})

            # Punti 8 & 9: Gestione liquidità — vende XAG se USDT è insufficiente
            if usdt < config["trade_margin"]:
                logger.warning("⚠️ USDT insufficienti per il salto. Controllo riserve XAG...")
                if not execute_rebalancing(config, client, config["trade_margin"], xag, xag_price):
                    logger.error("❌ Riserve XAG insufficienti. Attendo prossimo ciclo.")
                    consecutive_errors = 0
                    logger.info("Prossimo ciclo tra %d secondi.", CYCLE_SLEEP_SECONDS)
                    time.sleep(CYCLE_SLEEP_SECONDS)
                    continue
                # Ricarica saldi dopo il rebalancing per avere valori accurati
                usdt, xag, xag_price = get_real_balances(config, client)
                ctx.update({"usdt": usdt, "xag": xag, "xag_price": xag_price})

            # Punto 1: Accumulo argento (condizionale)
            if config["enable_silver_accumulation"]:
                accumulate_silver(config, client)

            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            else:
                # Punti 2, 3 & 17: Scansione opportunità sui target volatili
                for target in config["volatile_targets"]:
                    if check_market_trend(client, target):
                        logger.info("🚀 SALTO: Trend positivo su %s. Eseguo micro-trade.", target)
                        if config["dry_run"]:
                            logger.info(
                                "DRY_RUN: micro-trade simulato su %s (%.4f unità).",
                                target,
                                config["micro_trade_quantity"],
                            )
                        else:
                            result = client.create_order(
                                target, "BUY", "MARKET", quantity=config["micro_trade_quantity"]
                            )
                            if result is not None:
                                logger.info("Micro-trade eseguito su %s: %s", target, result)
                            else:
                                logger.error("Errore nell'esecuzione del micro-trade su %s.", target)
                        break
                else:
                    logger.info("Nessun trend positivo trovato sui target volatili.")

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
