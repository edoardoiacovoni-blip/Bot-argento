"""
Provider DXY (Dollar Index) — configurabile tramite variabili d'ambiente.

Variabili d'ambiente:
  DXY_PROVIDER  = "none" (default) | "url"
  DXY_URL       = URL API che restituisce {"bias": "bullish"|"bearish"}
  DXY_API_KEY   = API key opzionale per il provider (inviata come X-API-Key)

NOTA: XAG (argento) e DXY sono inversamente correlati.
  DXY bullish → pressione ribassista su XAG.
  DXY bearish → supporto rialzista su XAG.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)


def get_dxy_bias() -> str | None:
    """
    Restituisce il bias DXY corrente: 'bullish', 'bearish', o None se non disponibile.

    :return: 'bullish', 'bearish', o None se provider non configurato o errore.
    """
    provider = os.environ.get("DXY_PROVIDER", "none").strip().lower()

    if provider == "none":
        return None

    if provider == "url":
        url = os.environ.get("DXY_URL", "").strip()
        if not url:
            logger.warning("DXY_PROVIDER=url ma DXY_URL non configurata")
            return None
        api_key = os.environ.get("DXY_API_KEY", "").strip()
        headers = {"X-API-Key": api_key} if api_key else {}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            bias = data.get("bias", "").lower()
            if bias in ("bullish", "bearish"):
                return bias
            logger.warning("DXY provider risposta inattesa: %s", data)
            return None
        except Exception as exc:
            logger.warning("Errore provider DXY: %s", exc)
            return None

    logger.warning("DXY_PROVIDER='%s' non supportato (valori: 'none', 'url')", provider)
    return None
