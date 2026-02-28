"""
Flying Wheel — 18 Controlli (Implementazione Reale)

Ogni funzione riceve un dizionario di contesto e restituisce (passed: bool, motivo: str).

Contesto atteso (ctx):
  - df:           pandas DataFrame con colonne OHLCV e indicatori calcolati
  - plan:         dizionario {side, entry, sl, tp, qty, rr} o None
  - config:       dizionario di configurazione dal main
  - client:       istanza PionexClient
  - market_data:  dizionario {spread_bps: float|None}
  - risk_state:   dizionario {daily_loss_usdt, trades_this_hour, consecutive_losses, ...}
  - swing_high:   float — swing high recente
  - swing_low:    float — swing low recente
"""
import datetime

import pandas as pd


# ---------------------------------------------------------------------------
# CHECK 01 — Allineamento trend higher timeframe: close > EMA200
# ---------------------------------------------------------------------------

def check_01(ctx: dict) -> tuple[bool, str]:
    """Trend rialzista: close corrente > EMA200."""
    df = ctx.get("df")
    if df is None or df.empty or "ema200" not in df.columns:
        return False, "check_01: dati insufficienti per EMA200"
    last = df.iloc[-1]
    ema200 = last.get("ema200")
    if pd.isna(ema200):
        return True, "check_01: EMA200 non ancora stabilizzata — skip (dati insuff.)"
    close = float(last["close"])
    ema200 = float(ema200)
    if close > ema200:
        return True, f"check_01: trend rialzista — close {close:.4f} > EMA200 {ema200:.4f}"
    return False, f"check_01: close {close:.4f} <= EMA200 {ema200:.4f} — nessun trend rialzista"


# ---------------------------------------------------------------------------
# CHECK 02 — Market Structure BOS: ultimo high rompe lo swing high recente
# ---------------------------------------------------------------------------

def check_02(ctx: dict) -> tuple[bool, str]:
    """Break of Structure rialzista: ultimo high > swing high delle N barre precedenti."""
    df = ctx.get("df")
    if df is None or len(df) < 10:
        return False, "check_02: dati insufficienti per BOS"
    current_high = float(df.iloc[-1]["high"])
    prev_swing_high = float(df.iloc[-11:-1]["high"].max())
    if current_high > prev_swing_high:
        return True, f"check_02: BOS rialzista — high {current_high:.4f} > swing {prev_swing_high:.4f}"
    return False, f"check_02: nessun BOS — high {current_high:.4f} <= swing {prev_swing_high:.4f}"


# ---------------------------------------------------------------------------
# CHECK 03 — Order Block: candela bearish prima di mossa impulsiva rialzista
# ---------------------------------------------------------------------------

def check_03(ctx: dict) -> tuple[bool, str]:
    """Order block: ultima candela bearish seguita da impulso rialzista >= 1.5x."""
    df = ctx.get("df")
    if df is None or len(df) < 5:
        return False, "check_03: dati insufficienti per Order Block"
    window = min(20, len(df))
    recent = df.tail(window).reset_index(drop=True)
    for i in range(len(recent) - 2, 0, -1):
        candle = recent.iloc[i]
        next_c = recent.iloc[i + 1]
        # Candela bearish: close < open
        if candle["close"] < candle["open"]:
            bearish_body = float(candle["open"] - candle["close"])
            bullish_body = float(next_c["close"] - next_c["open"])
            if bearish_body > 0 and bullish_body >= bearish_body * 1.5:
                return (
                    True,
                    f"check_03: Order Block rilevato — bearish {bearish_body:.4f}, "
                    f"impulso rialzista {bullish_body:.4f}",
                )
    return False, "check_03: nessun Order Block rilevato nelle ultime barre"


# ---------------------------------------------------------------------------
# CHECK 04 — Liquidity Sweep: ultimo low spazza il minimo delle N barre precedenti
# ---------------------------------------------------------------------------

def check_04(ctx: dict) -> tuple[bool, str]:
    """Liquidity sweep rialzista: ultimo low <= minimo precedente, ma close sopra."""
    df = ctx.get("df")
    if df is None or len(df) < 10:
        return False, "check_04: dati insufficienti per liquidity sweep"
    n = 5
    last = df.iloc[-1]
    prev_lows = df.iloc[-(n + 1):-1]["low"]
    prev_low_min = float(prev_lows.min())
    last_low = float(last["low"])
    last_close = float(last["close"])
    if last_low <= prev_low_min and last_close > prev_low_min:
        return (
            True,
            f"check_04: Liquidity sweep — low {last_low:.4f} <= {prev_low_min:.4f}, "
            f"recupero a {last_close:.4f}",
        )
    return (
        False,
        f"check_04: nessun sweep (last low: {last_low:.4f}, prev min: {prev_low_min:.4f})",
    )


# ---------------------------------------------------------------------------
# CHECK 05 — FVG Imbalance: gap tra candela 1 e candela 3 (3-candle heuristic)
# ---------------------------------------------------------------------------

def check_05(ctx: dict) -> tuple[bool, str]:
    """FVG rialzista: low[i+2] > high[i] nelle ultime 20 barre."""
    df = ctx.get("df")
    if df is None or len(df) < 5:
        return False, "check_05: dati insufficienti per FVG"
    recent = df.tail(20).reset_index(drop=True)
    for i in range(len(recent) - 2):
        if recent.iloc[i + 2]["low"] > recent.iloc[i]["high"]:
            gap = float(recent.iloc[i + 2]["low"] - recent.iloc[i]["high"])
            return True, f"check_05: FVG rialzista — gap {gap:.4f}"
    return False, "check_05: nessun FVG rialzista nelle ultime barre"


# ---------------------------------------------------------------------------
# CHECK 06 — Fibonacci OTE: prezzo in zona 0.618–0.786 dal recente swing
# ---------------------------------------------------------------------------

def check_06(ctx: dict) -> tuple[bool, str]:
    """Fibonacci OTE: prezzo nel range 61.8%–78.6% di ritracciamento."""
    df = ctx.get("df")
    if df is None or df.empty:
        return False, "check_06: dati insufficienti per Fibonacci OTE"
    swing_high = float(ctx.get("swing_high", df["high"].max()))
    swing_low = float(ctx.get("swing_low", df["low"].min()))
    if swing_high <= swing_low:
        return False, "check_06: swing high <= swing low — OTE non calcolabile"
    current_price = float(df.iloc[-1]["close"])
    rng = swing_high - swing_low
    fib_618 = swing_high - rng * 0.618
    fib_786 = swing_high - rng * 0.786
    if fib_786 <= current_price <= fib_618:
        return (
            True,
            f"check_06: OTE OK — prezzo {current_price:.4f} in [{fib_786:.4f}, {fib_618:.4f}]",
        )
    return (
        False,
        f"check_06: OTE FAIL — prezzo {current_price:.4f} fuori [{fib_786:.4f}, {fib_618:.4f}]",
    )


# ---------------------------------------------------------------------------
# CHECK 07 — RSI: oversold (RSI < soglia configurabile, default 30)
# ---------------------------------------------------------------------------

def check_07(ctx: dict) -> tuple[bool, str]:
    """RSI in zona oversold."""
    df = ctx.get("df")
    config = ctx.get("config", {})
    if df is None or df.empty or "rsi14" not in df.columns:
        return False, "check_07: RSI14 non disponibile"
    rsi_threshold = float(config.get("rsi_oversold", 30))
    last_rsi = df.iloc[-1].get("rsi14")
    if last_rsi is None or pd.isna(last_rsi):
        return False, "check_07: RSI14 non ancora calcolato"
    last_rsi = float(last_rsi)
    if last_rsi < rsi_threshold:
        return True, f"check_07: RSI oversold — {last_rsi:.1f} < {rsi_threshold}"
    return False, f"check_07: RSI {last_rsi:.1f} non in oversold (soglia: {rsi_threshold})"


# ---------------------------------------------------------------------------
# CHECK 08 — Volume spike: ultimo volume > rolling mean 20 barre
# ---------------------------------------------------------------------------

def check_08(ctx: dict) -> tuple[bool, str]:
    """Volume spike: volume corrente sopra la media mobile 20 barre."""
    df = ctx.get("df")
    if df is None or df.empty or "vol_mean20" not in df.columns:
        return False, "check_08: dati volume non disponibili"
    last = df.iloc[-1]
    vol = float(last["volume"])
    vol_mean = last.get("vol_mean20")
    if vol_mean is None or pd.isna(vol_mean) or vol_mean == 0:
        return True, "check_08: volume mean non calcolato — skip"
    vol_mean = float(vol_mean)
    if vol > vol_mean:
        return True, f"check_08: volume spike — {vol:.2f} > media {vol_mean:.2f}"
    return False, f"check_08: volume {vol:.2f} < media {vol_mean:.2f} — nessun spike"


# ---------------------------------------------------------------------------
# CHECK 09 — ATR Volatilità: ATR% in banda accettabile
# ---------------------------------------------------------------------------

def check_09(ctx: dict) -> tuple[bool, str]:
    """ATR volatilità: ATR% entro il range accettabile [min_atr_pct, max_atr_pct]."""
    df = ctx.get("df")
    config = ctx.get("config", {})
    if df is None or df.empty or "atr14" not in df.columns:
        return False, "check_09: ATR14 non disponibile"
    last = df.iloc[-1]
    atr = last.get("atr14")
    if atr is None or pd.isna(atr):
        return True, "check_09: ATR non ancora calcolato — skip"
    atr = float(atr)
    close = float(last["close"])
    if close == 0:
        return True, "check_09: close = 0, skip"
    atr_pct = atr / close * 100
    max_atr_pct = float(config.get("max_atr_pct", 5.0))
    min_atr_pct = float(config.get("min_atr_pct", 0.05))
    if min_atr_pct <= atr_pct <= max_atr_pct:
        return True, f"check_09: ATR OK — {atr_pct:.2f}% in [{min_atr_pct}%, {max_atr_pct}%]"
    return False, f"check_09: ATR {atr_pct:.2f}% fuori range [{min_atr_pct}%, {max_atr_pct}%]"


# ---------------------------------------------------------------------------
# CHECK 10 — DXY Correlation: provider pluggabile (inversa con XAG)
# ---------------------------------------------------------------------------

def check_10(ctx: dict) -> tuple[bool, str]:
    """Correlazione DXY: DXY bearish è favorevole per XAG (correlazione inversa)."""
    config = ctx.get("config", {})
    strict = config.get("strict_externals", False)
    from src.providers.dxy_provider import get_dxy_bias

    bias = get_dxy_bias()
    if bias is None:
        if strict:
            return False, "check_10: provider DXY non configurato (STRICT_EXTERNALS=1)"
        return True, "check_10: provider DXY DISABLED (non bloccante con STRICT_EXTERNALS=0)"
    if bias == "bearish":
        return True, "check_10: DXY bearish — favorevole per XAG rialzista"
    return False, f"check_10: DXY {bias} — sfavorevole per posizione long XAG"


# ---------------------------------------------------------------------------
# CHECK 11 — Candlestick Confluence: pinbar o engulfing rialzista
# ---------------------------------------------------------------------------

def check_11(ctx: dict) -> tuple[bool, str]:
    """Pattern candlestick: pinbar (hammer) o engulfing rialzista."""
    df = ctx.get("df")
    if df is None or len(df) < 2:
        return False, "check_11: dati insufficienti per pattern candlestick"
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(float(last["close"]) - float(last["open"]))
    upper_wick = float(last["high"]) - max(float(last["close"]), float(last["open"]))
    lower_wick = min(float(last["close"]), float(last["open"])) - float(last["low"])

    # Pinbar (hammer): lower wick >= 2x body, upper wick piccolo
    if body > 0 and lower_wick >= body * 2.0 and upper_wick <= body * 0.5:
        return True, f"check_11: Pinbar/Hammer — lower wick {lower_wick:.4f}"

    # Engulfing rialzista: candela rialzista che ingloba la precedente bearish
    if float(last["close"]) > float(last["open"]):  # candela rialzista
        if float(last["open"]) <= float(prev["close"]) and float(last["close"]) >= float(prev["open"]):
            return True, "check_11: Engulfing rialzista rilevato"

    return False, "check_11: nessun pattern candlestick confluente rilevato"


# ---------------------------------------------------------------------------
# CHECK 12 — VWAP Alignment: close sopra VWAP
# ---------------------------------------------------------------------------

def check_12(ctx: dict) -> tuple[bool, str]:
    """VWAP alignment: close deve essere sopra VWAP per posizione long."""
    df = ctx.get("df")
    if df is None or df.empty or "vwap" not in df.columns:
        return False, "check_12: VWAP non disponibile"
    last = df.iloc[-1]
    vwap = last.get("vwap")
    if vwap is None or pd.isna(vwap):
        return True, "check_12: VWAP non calcolato — skip"
    close = float(last["close"])
    vwap = float(vwap)
    if close > vwap:
        return True, f"check_12: VWAP OK — close {close:.4f} > VWAP {vwap:.4f}"
    return False, f"check_12: close {close:.4f} <= VWAP {vwap:.4f} — nessun alignment long"


# ---------------------------------------------------------------------------
# CHECK 13 — Risk/Reward Ratio >= 3
# ---------------------------------------------------------------------------

def check_13(ctx: dict) -> tuple[bool, str]:
    """Risk/Reward ratio: il piano deve avere R:R >= 3."""
    plan = ctx.get("plan")
    if plan is None:
        return False, "check_13: piano di trading non disponibile"
    rr = float(plan.get("rr", 0))
    if rr >= 3.0:
        return True, f"check_13: R:R {rr:.2f} >= 3 — accettabile"
    return False, f"check_13: R:R {rr:.2f} < 3 — insufficiente"


# ---------------------------------------------------------------------------
# CHECK 14 — News Filter: provider pluggabile, blocca su eventi ad alto impatto
# ---------------------------------------------------------------------------

def check_14(ctx: dict) -> tuple[bool, str]:
    """Filtro notizie: blocca il trading vicino a eventi macro ad alto impatto."""
    config = ctx.get("config", {})
    strict = config.get("strict_externals", False)
    from src.providers.news_provider import is_high_impact_news_window

    high_impact = is_high_impact_news_window()
    if high_impact is None:
        if strict:
            return False, "check_14: provider notizie non configurato (STRICT_EXTERNALS=1)"
        return True, "check_14: provider notizie DISABLED (non bloccante con STRICT_EXTERNALS=0)"
    if high_impact:
        return False, "check_14: evento macro ad alto impatto — trading bloccato"
    return True, "check_14: nessun evento macro ad alto impatto — OK"


# ---------------------------------------------------------------------------
# CHECK 15 — Daily Drawdown Limit
# ---------------------------------------------------------------------------

def check_15(ctx: dict) -> tuple[bool, str]:
    """Drawdown giornaliero: blocca se la perdita supera la soglia configurata."""
    config = ctx.get("config", {})
    risk_state = ctx.get("risk_state", {})
    max_daily_dd = float(config.get("max_daily_drawdown", 0.02))
    daily_loss = float(risk_state.get("daily_loss_usdt", 0.0))
    total_balance = float(risk_state.get("total_balance_usdt", 100.0))
    if total_balance > 0:
        dd_pct = daily_loss / total_balance
        if dd_pct >= max_daily_dd:
            return (
                False,
                f"check_15: drawdown {dd_pct * 100:.2f}% >= limite {max_daily_dd * 100:.2f}%",
            )
    return True, f"check_15: drawdown OK — perdita giornaliera {daily_loss:.4f} USDT"


# ---------------------------------------------------------------------------
# CHECK 16 — Spread Check: spread bid/ask < max_spread_bps
# ---------------------------------------------------------------------------

def check_16(ctx: dict) -> tuple[bool, str]:
    """Spread check: lo spread bid/ask deve essere sotto il massimo configurato."""
    config = ctx.get("config", {})
    market_data = ctx.get("market_data", {})
    max_spread_bps = float(config.get("max_spread_bps", 10))
    spread_bps = market_data.get("spread_bps")
    if spread_bps is None:
        return True, "check_16: spread non disponibile — skip"
    spread_bps = float(spread_bps)
    if spread_bps <= max_spread_bps:
        return True, f"check_16: spread {spread_bps:.2f} bps <= {max_spread_bps} bps — OK"
    return False, f"check_16: spread {spread_bps:.2f} bps > {max_spread_bps} bps — troppo ampio"


# ---------------------------------------------------------------------------
# CHECK 17 — Time Session: solo nelle ore configurate (UTC)
# ---------------------------------------------------------------------------

def check_17(ctx: dict) -> tuple[bool, str]:
    """Sessione di trading: solo nelle ore UTC configurate."""
    config = ctx.get("config", {})
    session_start = int(config.get("session_start_utc", 9))
    session_end = int(config.get("session_end_utc", 22))
    hour = datetime.datetime.utcnow().hour
    if session_start <= hour < session_end:
        return True, f"check_17: sessione attiva — ora UTC {hour:02d}:xx"
    return (
        False,
        f"check_17: fuori sessione — ora UTC {hour:02d}:xx, sessione [{session_start:02d}h, {session_end:02d}h)",
    )


# ---------------------------------------------------------------------------
# CHECK 18 — Psychology / Overtrading Guard
# ---------------------------------------------------------------------------

def check_18(ctx: dict) -> tuple[bool, str]:
    """Guardia anti-overtrading: limita trade/ora e perdite consecutive."""
    config = ctx.get("config", {})
    risk_state = ctx.get("risk_state", {})
    max_trades_hr = int(config.get("max_trades_per_hour", 20))
    max_consec_loss = int(config.get("max_consecutive_losses", 5))
    trades_this_hour = int(risk_state.get("trades_this_hour", 0))
    consecutive_losses = int(risk_state.get("consecutive_losses", 0))

    if trades_this_hour >= max_trades_hr:
        return (
            False,
            f"check_18: overtrading — {trades_this_hour}/{max_trades_hr} trade nell'ultima ora",
        )
    if consecutive_losses >= max_consec_loss:
        return (
            False,
            f"check_18: {consecutive_losses} perdite consecutive — pausa obbligatoria",
        )
    return (
        True,
        f"check_18: OK — {trades_this_hour} trade/h, {consecutive_losses} perdite consecutive",
    )

