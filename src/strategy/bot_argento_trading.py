"""
Strategia Bot Argento per XAG_USDT — Flying Wheel Trading.

Recupera dati OHLCV da Pionex, calcola indicatori tecnici e produce
il piano di trading (entry, SL, TP, quantità).
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_dataframe(klines: list) -> pd.DataFrame:
    """
    Converte la lista di klines in un DataFrame OHLCV.

    Accetta klines come lista di liste/tuple nel formato:
    [timestamp, open, high, low, close, volume]
    """
    if not klines:
        return pd.DataFrame()

    try:
        df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume"])
    except Exception:
        # fallback: prova a prendere le prime 6 colonne
        rows = [list(row)[:6] for row in klines if len(row) >= 6]
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df.dropna(subset=["open", "high", "low", "close", "volume"], inplace=True)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calcola EMA200, RSI14, ATR14, VWAP e volume rolling mean."""
    if df.empty or len(df) < 3:
        return df

    # EMA200 (converge anche con meno barre grazie a ewm)
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    # RSI14
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))

    # ATR14
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["atr14"] = tr.ewm(span=14, adjust=False).mean()

    # VWAP cumulativo sull'intero dataset
    tp = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (tp * df["volume"]).cumsum() / df["volume"].cumsum()

    # Volume rolling mean (20 barre)
    df["vol_mean20"] = df["volume"].rolling(20, min_periods=1).mean()

    return df


def find_swing_high(df: pd.DataFrame, window: int = 5) -> float:
    """Trova il più recente swing high nelle ultime barre."""
    if len(df) < window * 2 + 1:
        return float(df["high"].max())
    # Cerca nei recenti (fino a 40 barre)
    recent = df.tail(min(40, len(df))).reset_index(drop=True)
    for i in range(len(recent) - window - 1, window - 1, -1):
        local = recent.iloc[i - window: i + window + 1]
        if recent.iloc[i]["high"] == local["high"].max():
            return float(recent.iloc[i]["high"])
    return float(df["high"].max())


def find_swing_low(df: pd.DataFrame, window: int = 5) -> float:
    """Trova il più recente swing low nelle ultime barre."""
    if len(df) < window * 2 + 1:
        return float(df["low"].min())
    recent = df.tail(min(40, len(df))).reset_index(drop=True)
    for i in range(len(recent) - window - 1, window - 1, -1):
        local = recent.iloc[i - window: i + window + 1]
        if recent.iloc[i]["low"] == local["low"].min():
            return float(recent.iloc[i]["low"])
    return float(df["low"].min())


def compute_trade_plan(df: pd.DataFrame, config: dict) -> Optional[dict]:
    """
    Produce il piano di trading: side, qty, entry, sl, tp, R:R.

    :return: dizionario con il piano, o None se dati insufficienti.
    """
    if df.empty or len(df) < 14:
        return None

    last = df.iloc[-1]
    entry = float(last["close"])
    atr = float(last["atr14"]) if not pd.isna(last.get("atr14", float("nan"))) else 0.0

    if atr <= 0 or entry <= 0:
        return None

    side = "BUY"
    sl_distance = atr * 1.5
    sl = entry - sl_distance
    tp = entry + sl_distance * 3.0  # R:R = 3

    micro_usdt = float(config.get("micro_trade_usdt", 5))
    qty = round(micro_usdt / entry, 6)

    rr = round((tp - entry) / (entry - sl), 2) if (entry - sl) > 0 else 0.0

    return {
        "side": side,
        "entry": round(entry, 6),
        "sl": round(sl, 6),
        "tp": round(tp, 6),
        "qty": qty,
        "atr": round(atr, 6),
        "rr": rr,
    }


def fetch_and_prepare(client, config: dict) -> tuple[pd.DataFrame, Optional[dict]]:
    """
    Recupera klines da Pionex, calcola indicatori e produce il piano di trading.

    :return: (df, plan) — df può essere vuoto, plan può essere None.
    """
    symbol = config.get("symbol", "XAG_USDT")
    timeframe = config.get("timeframe", "5m")
    limit = int(config.get("klines_limit", 300))

    klines = client.get_klines(symbol, timeframe, limit)
    if not klines:
        logger.warning("Nessun dato klines ricevuto per %s/%s", symbol, timeframe)
        return pd.DataFrame(), None

    df = build_dataframe(klines)
    if df.empty:
        logger.warning("DataFrame vuoto dopo la costruzione per %s", symbol)
        return df, None

    df = compute_indicators(df)
    plan = compute_trade_plan(df, config)
    return df, plan
