"""
Provider notizie macro — configurabile tramite variabili d'ambiente.

Variabili d'ambiente:
  NEWS_PROVIDER = "none" (default) | "url"
  NEWS_URL      = URL API che restituisce {"high_impact": true|false}
  NEWS_API_KEY  = API key opzionale per il provider (inviata come X-API-Key)
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)


def is_high_impact_news_window() -> bool | None:
    """
    Restituisce True se siamo in una finestra di evento macro ad alto impatto,
    False se nessun evento, None se provider non configurato o errore.

    :return: True/False/None
    """
    provider = os.environ.get("NEWS_PROVIDER", "none").strip().lower()

    if provider == "none":
        return None

    if provider == "url":
        url = os.environ.get("NEWS_URL", "").strip()
        if not url:
            logger.warning("NEWS_PROVIDER=url ma NEWS_URL non configurata")
            return None
        api_key = os.environ.get("NEWS_API_KEY", "").strip()
        headers = {"X-API-Key": api_key} if api_key else {}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return bool(data.get("high_impact", False))
        except Exception as exc:
            logger.warning("Errore provider notizie: %s", exc)
            return None

    logger.warning("NEWS_PROVIDER='%s' non supportato (valori: 'none', 'url')", provider)
    return None
