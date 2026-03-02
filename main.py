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
5. Stampa un riepilogo dello stato al termine di ogni ciclo.

Variabili d'ambiente richieste:
    PIONEX_API_KEY          -- API key dell'account Pionex
    PIONEX_SECRET_KEY       -- Secret key dell'account Pionex
    SILVER_SYMBOL           -- Simbolo argento SPOT, es. XAG_USDT
    SILVER_BUY_AMOUNT_USDT  -- Importo USDT da spendere per ogni acquisto (default: 5)
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


class StatusTracker:
    """Tiene traccia delle statistiche operative del bot e genera report di stato."""

    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.start_time: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.cycles_total: int = 0
        self.cycles_ok: int = 0
        self.cycles_failed: int = 0
        self.consecutive_errors: int = 0
        self.last_cycle_time: datetime.datetime | None = None
        self.last_fw_passed: bool | None = None

    def record_cycle(self, fw_passed: bool) -> None:
        """Registra il risultato di un ciclo completato."""
        self.cycles_total += 1
        self.consecutive_errors = 0
        self.last_cycle_time = datetime.datetime.now(datetime.timezone.utc)
        self.last_fw_passed = fw_passed
        if fw_passed:
            self.cycles_ok += 1
        else:
            self.cycles_failed += 1

    def record_error(self) -> None:
        """Registra un errore imprevisto durante un ciclo."""
        self.cycles_total += 1
        self.cycles_failed += 1
        self.consecutive_errors += 1
        self.last_cycle_time = datetime.datetime.now(datetime.timezone.utc)

    def uptime(self) -> str:
        """Restituisce l'uptime formattato come stringa HH:MM:SS."""
        delta = datetime.datetime.now(datetime.timezone.utc) - self.start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def seconds_since_last_cycle(self) -> str:
        """Restituisce il tempo trascorso dall'ultimo ciclo in secondi, o 'N/D'."""
        if self.last_cycle_time is None:
            return "N/D"
        delta = datetime.datetime.now(datetime.timezone.utc) - self.last_cycle_time
        return f"{int(delta.total_seconds())}s fa"

    def log_status(self) -> None:
        """Stampa un riepilogo dello stato corrente del bot nei log."""
        mode = "DRY_RUN" if self.dry_run else "REALE"
        fw_result = (
            "PASS ✅" if self.last_fw_passed
            else ("FAIL ❌" if self.last_fw_passed is False else "N/D")
        )
        logger.info(
            "━━━ STATO BOT ━━━ | Modalità: %s | Uptime: %s | "
            "Cicli: %d (OK: %d, FAIL: %d) | Ultimo ciclo: %s | "
            "Ultimo Flying Wheel: %s | Errori consecutivi: %d",
            mode,
            self.uptime(),
            self.cycles_total,
            self.cycles_ok,
            self.cycles_failed,
            self.seconds_since_last_cycle(),
            fw_result,
            self.consecutive_errors,
        )


def main() -> None:
    config = load_config()

    if config["dry_run"]:
        logger.info("Modalità DRY_RUN attiva — nessun ordine reale verrà eseguito.")
    else:
        logger.warning("Modalità REALE attiva — gli ordini verranno inviati a Pionex!")

    ctx = {"config": config, "client": PionexClient(config["api_key"], config["secret_key"])}
    tracker = StatusTracker(dry_run=config["dry_run"])

    while True:
        try:
            accumulate_silver(config, ctx["client"])

            all_passed = engine.run(ctx)

            if not all_passed:
                logger.warning("Flying Wheel non completato: operazione annullata.")
            elif config["dry_run"]:
                logger.info("DRY_RUN: operazione simulata completata con successo.")
            else:
                logger.info("Tutti i check superati — avvio esecuzione ordine reale.")
                # TODO: integrare le chiamate API Pionex per l'ordine effettivo

            tracker.record_cycle(all_passed)
            tracker.log_status()
            logger.info("Prossimo ciclo tra %d secondi.", CYCLE_SLEEP_SECONDS)
            time.sleep(CYCLE_SLEEP_SECONDS)

        except Exception as exc:
            tracker.record_error()
            wait = min(2 ** min(tracker.consecutive_errors, 10), MAX_BACKOFF_SECONDS)
            logger.error(
                "Errore imprevisto (ciclo #%d): %s — riprovo tra %d secondi.",
                tracker.cycles_total,
                exc,
                wait,
            )
            tracker.log_status()
            time.sleep(wait)


if __name__ == "__main__":
    main()
