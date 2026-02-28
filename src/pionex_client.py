"""
Client per le API di Pionex.

Gestisce l'autenticazione HMAC-SHA256 e le chiamate HTTP
all'API di Pionex per dati di mercato e ordini.
"""
import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)


class PionexClient:
    """Client autenticato per le API REST di Pionex."""

    BASE_URL = "https://api.pionex.com"

    def __init__(self, api_key: str, secret_key: str) -> None:
        self.api_key = api_key
        self.secret_key = secret_key

    # ------------------------------------------------------------------
    # Helpers interni
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> str:
        """Genera la firma HMAC-SHA256 dei parametri di query."""
        query_string = urlencode(sorted(params.items()))
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request(self, method: str, endpoint: str, params: dict | None = None):
        """Effettua una richiesta autenticata all'API di Pionex.

        :return: dizionario JSON della risposta, o None in caso di errore.
        """
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000  # finestra di validità della richiesta in ms (5 s)
        params["signature"] = self._sign(params)

        headers = {
            "PIONEX-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Metodo HTTP non supportato: {method}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Errore richiesta API Pionex [%s %s]: %s", method, endpoint, exc)
            return None  # il chiamante gestisce il None

    # ------------------------------------------------------------------
    # API pubbliche
    # ------------------------------------------------------------------

    def get_ticker(self, symbol: str | None = None):
        """Restituisce i dati di mercato (ticker).

        :param symbol: es. 'PAXG_USDT'; se None, restituisce tutti i ticker.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v1/market/tickers", params)

    def create_order(self, symbol: str, side: str, order_type: str, quantity: float):
        """Crea un ordine su Pionex.

        :param symbol:     coppia di trading, es. 'PAXG_USDT'
        :param side:       'BUY' o 'SELL'
        :param order_type: 'MARKET' o 'LIMIT'
        :param quantity:   quantità da acquistare/vendere
        """
        return self._request(
            "POST",
            "/api/v1/trade/order",
            {"symbol": symbol, "side": side, "type": order_type, "quantity": quantity},
        )

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> list:
        """Recupera dati OHLCV (klines) per il simbolo e l'intervallo specificati.

        :param symbol:   coppia di trading, es. 'XAG_USDT'
        :param interval: intervallo temporale, es. '5m', '1h'
        :param limit:    numero massimo di candele da restituire
        :return: lista di [timestamp, open, high, low, close, volume], o [] in caso di errore.
        """
        result = self._request(
            "GET",
            "/api/v1/market/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        if result is None:
            return []
        data = result.get("data", {})
        if isinstance(data, dict):
            return data.get("klines", data.get("data", []))
        if isinstance(data, list):
            return data
        logger.warning("Formato klines inatteso da Pionex: %s", type(data).__name__)
        return []

    def get_orderbook(self, symbol: str):
        """Recupera il book degli ordini (bid/ask) per il simbolo.

        :param symbol: coppia di trading, es. 'XAG_USDT'
        :return: dizionario con 'bids' e 'asks', o None in caso di errore.
        """
        return self._request("GET", "/api/v1/market/depth", {"symbol": symbol})

    def get_balances(self):
        """Recupera i saldi dell'account.

        :return: dizionario con i saldi, o None in caso di errore.
        """
        return self._request("GET", "/api/v1/account/balances")

    def test_connection(self) -> bool:
        """Verifica che le credenziali siano valide e l'API raggiungibile.

        :return: True se la connessione ha successo, False altrimenti.
        """
        result = self._request("GET", "/api/v1/common/timestamp")
        return result is not None
