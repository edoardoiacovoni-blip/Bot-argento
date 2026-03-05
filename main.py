"""
Bot Argento - Flying Wheel System (Worker Continuo)
====================================================
Worker continuo per trading XAG_USDT su Pionex tramite il motore Flying Wheel a 18 punti.

Variabili d'ambiente:
    PIONEX_API_KEY          -- API key dell'account Pionex (obbligatoria)
    PIONEX_SECRET_KEY       -- Secret key dell'account Pionex (obbligatoria)
    DRY_RUN                 -- 0 = trading reale, 1 = simulazione (default: 1)
    SYMBOL                  -- Simbolo di trading (default: XAG_USDT)
    TIMEFRAME               -- Timeframe klines (default: 5m)
    LOOP_SECONDS            -- Intervallo loop in secondi (default: 10)
    MICRO_TRADE_USDT        -- Importo per micro-trade in USDT (default: 5)
    MAX_TRADES_PER_HOUR     -- Max trade per ora (default: 20)
    MAX_DAILY_DRAWDOWN      -- Max drawdown giornaliero % (default: 0.02)
    MAX_SPREAD_BPS          -- Max spread in basis points (default: 10)
    STRICT_EXTERNALS        -- 1 = provider DXY/News bloccanti se mancanti (default: 0)
    DXY_PROVIDER            -- Provider DXY: none|url (default: none)
    DXY_URL                 -- URL API DXY (se DXY_PROVIDER=url)
    DXY_API_KEY             -- API key per il provider DXY (opzionale)
    NEWS_PROVIDER           -- Provider notizie: none|url (default: none)
    NEWS_URL                -- URL API notizie (se NEWS_PROVIDER=url)
    NEWS_API_KEY            -- API key per il provider notizie (opzionale)
    SESSION_START_UTC       -- Ora UTC inizio sessione trading (default: 9)
    SESSION_END_UTC         -- Ora UTC fine sessione trading (default: 22)
    RSI_OVERSOLD            -- Soglia RSI oversold (default: 30)
    MAX_CONSECUTIVE_LOSSES  -- Max perdite consecutive prima di pausa (default: 5)
"""
import datetime
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
from src.strategy.bot_argento_trading import fetch_and_prepare, find_swing_high, find_swing_low

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
        "symbol": os.environ.get("SYMBOL", "XAG_USDT").strip(),
        "timeframe": os.environ.get("TIMEFRAME", "5m").strip(),
        "loop_seconds": int(os.environ.get("LOOP_SECONDS", "10")),
        "micro_trade_usdt": float(os.environ.get("MICRO_TRADE_USDT", "5")),
        "max_trades_per_hour": int(os.environ.get("MAX_TRADES_PER_HOUR", "20")),
        "max_daily_drawdown": float(os.environ.get("MAX_DAILY_DRAWDOWN", "0.02")),
        "max_spread_bps": float(os.environ.get("MAX_SPREAD_BPS", "10")),
        "strict_externals": os.environ.get("STRICT_EXTERNALS", "0").strip() not in ("0", "false", "False"),
        "session_start_utc": int(os.environ.get("SESSION_START_UTC", "9")),
        "session_end_utc": int(os.environ.get("SESSION_END_UTC", "22")),
        "rsi_oversold": float(os.environ.get("RSI_OVERSOLD", "30")),
        "max_consecutive_losses": int(os.environ.get("MAX_CONSECUTIVE_LOSSES", "5")),
        "klines_limit": 300,
    }


def _reset_daily_state_if_needed(risk_state: dict) -> None:
    """Resetta lo stato giornaliero se è un nuovo giorno UTC."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    if risk_state.get("day") != today:
        risk_state["day"] = today
        risk_state["daily_loss_usdt"] = 0.0
        logger.info("Nuovo giorno UTC: reset drawdown giornaliero.")


def _get_spread_bps(client: PionexClient, symbol: str) -> float | None:
    """Recupera lo spread bid/ask corrente in basis points."""
    orderbook = client.get_orderbook(symbol)
    if orderbook is None:
        return None
    data = orderbook.get("data", {})
    bids = data.get("bids", [])
    asks = data.get("asks", [])
    if bids and asks:
        try:
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid = (best_bid + best_ask) / 2
            if mid > 0:
                return ((best_ask - best_bid) / mid) * 10_000
        except (IndexError, TypeError, ValueError):
            pass
    return None


def _execute_order(client: PionexClient, plan: dict, config: dict) -> bool:
    """Esegue l'ordine reale su Pionex. Restituisce True se l'ordine è stato accettato."""
    symbol = config.get("symbol", "XAG_USDT")
    result = client.create_order(
        symbol=symbol,
        side=plan["side"],
        order_type="MARKET",
        quantity=plan["qty"],
    )
    # Valida esplicitamente il criterio di successo atteso:
    # - payload deve essere un dict
    # - campo "result" deve essere True
    # - deve essere presente almeno uno tra "orderId" e "data"
    is_success = (
        isinstance(result, dict)
        and result.get("result") is True
        and ("orderId" in result or "data" in result)
    )
    if is_success:
        logger.info(
            "ORDINE ESEGUITO: %s %s qty=%s entry≈%s sl=%s tp=%s R:R=%s",
            plan["side"], symbol, plan["qty"],
            plan["entry"], plan["sl"], plan["tp"], plan["rr"],
        )
        return True

    # Logga con più dettagli quando il payload non è quello previsto
    if not isinstance(result, dict):
        logger.error(
            "Ordine fallito: risposta inattesa dal client (tipo=%s, valore=%r)",
            type(result).__name__,
            result,
        )
    else:
        logger.error(
            "Ordine fallito o payload non valido: result=%r, keys=%s",
            result.get("result"),
            list(result.keys()),
        )
    return False


def _run_loop_iteration(client: PionexClient, config: dict, risk_state: dict) -> None:
    """Esegue una singola iterazione del loop principale."""
    symbol = config["symbol"]

    _reset_daily_state_if_needed(risk_state)

    # Aggiorna contatore trade nell'ultima ora
    now_ts = time.time()
    risk_state["recent_trade_times"] = [
        t for t in risk_state["recent_trade_times"] if now_ts - t < 3600
    ]
    risk_state["trades_this_hour"] = len(risk_state["recent_trade_times"])

    # Aggiorna saldo USDT (best-effort)
    try:
        balances = client.get_balances()
        if balances:
            bal_list = balances.get("data", {}).get("balances", [])
            usdt_entry = next((b for b in bal_list if b.get("coin") == "USDT"), None)
            if usdt_entry:
                risk_state["total_balance_usdt"] = float(usdt_entry.get("free", 100))
    except Exception:
        pass

    # Recupera spread
    spread_bps = _get_spread_bps(client, symbol)
    market_data = {"spread_bps": spread_bps}

    # Recupera klines, calcola indicatori e piano
    df, plan = fetch_and_prepare(client, config)
    if df.empty:
        logger.warning("Nessun dato disponibile per %s — iterazione saltata.", symbol)
        return

    swing_high = find_swing_high(df)
    swing_low = find_swing_low(df)

    # Componi contesto per i 18 check Flying Wheel
    ctx = {
        "config": config,
        "client": client,
        "df": df,
        "plan": plan,
        "market_data": market_data,
        "risk_state": risk_state,
        "swing_high": swing_high,
        "swing_low": swing_low,
    }

    all_passed = engine.run(ctx)

    if not all_passed:
        logger.info("⚠️  Flying Wheel: uno o più check falliti — operazione annullata.")
        return

    if plan is None:
        logger.warning("Piano di trading non disponibile nonostante i check passati.")
        return

    logger.info(
        "✅ Flying Wheel completato — piano: %s qty=%s entry=%s sl=%s tp=%s R:R=%s",
        plan["side"], plan["qty"], plan["entry"], plan["sl"], plan["tp"], plan["rr"],
    )

    if config["dry_run"]:
        logger.info(
            "DRY_RUN: simulazione trade %s %s qty=%s (nessun ordine reale inviato)",
            plan["side"], symbol, plan["qty"],
        )
    else:
        success = _execute_order(client, plan, config)
        if success:
            risk_state["recent_trade_times"].append(time.time())
            risk_state["consecutive_losses"] = 0
        else:
            risk_state["consecutive_losses"] += 1
            risk_state["daily_loss_usdt"] += float(config.get("micro_trade_usdt", 5))


def main() -> None:
    config = load_config()
    loop_seconds = config["loop_seconds"]
    symbol = config["symbol"]

    if config["dry_run"]:
        logger.info("🔵 Modalità DRY_RUN attiva — nessun ordine reale verrà eseguito.")
    else:
        logger.warning("🔴 Modalità REALE attiva — gli ordini verranno inviati a Pionex!")

    client = PionexClient(config["api_key"], config["secret_key"])

    # Verifica connessione API all'avvio
    if not client.test_connection():
        logger.error("Impossibile connettersi all'API Pionex. Verifica le credenziali e la rete.")
        sys.exit(1)

    logger.info("Connessione API Pionex OK. Avvio loop worker per %s (ogni %ds)...", symbol, loop_seconds)

    # Stato di rischio persistente tra le iterazioni
    risk_state = {
        "day": None,
        "daily_loss_usdt": 0.0,
        "trades_this_hour": 0,
        "consecutive_losses": 0,
        "total_balance_usdt": 100.0,
        "recent_trade_times": [],
    }

    while True:
        loop_start = time.time()
        try:
            _run_loop_iteration(client, config, risk_state)
        except Exception as exc:
            logger.error("Errore nel loop principale: %s", exc, exc_info=True)
        elapsed = time.time() - loop_start
        sleep_time = max(0.0, loop_seconds - elapsed)
        logger.debug("Loop in %.2fs. Prossima iterazione tra %.2fs.", elapsed, sleep_time)
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()

