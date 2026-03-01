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

    def _auth_params(self) -> dict:
        """Restituisce i parametri di autenticazione (timestamp, recvWindow, signature)."""
        params = {
            "timestamp": int(time.time() * 1000),
            "recvWindow": 5000,  # finestra di validità in ms (5 s)
        }
        params["signature"] = self._sign(params)
        return params

    def _request(self, method: str, endpoint: str, params: dict | None = None,
                 body: dict | None = None):
        """Effettua una richiesta autenticata all'API di Pionex.

        Per le richieste GET i parametri vengono passati come query string.
        Per le richieste POST i parametri di autenticazione vengono passati
        come query string mentre il payload dell'ordine viene inviato nel body JSON.

        :return: dizionario JSON della risposta, o None in caso di errore.
        """
        auth = self._auth_params()
        headers = {
            "PIONEX-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                query = {**auth, **(params or {})}
                response = requests.get(url, params=query, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(
                    url, params=auth, json=body or {}, headers=headers, timeout=10
                )
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

    def get_tickers(self, symbol: str | None = None) -> list[dict]:
        """Restituisce la lista dei ticker di mercato.

        :param symbol: es. 'XAG_USDT'; se None, restituisce tutti i ticker.
        :return: lista di dizionari ticker, vuota in caso di errore.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        data = self._request("GET", "/api/v1/market/tickers", params)
        if data is None:
            return []
        # La risposta ha la forma: {"result": true, "data": {"tickers": [...]}}
        try:
            return data["data"]["tickers"]
        except (KeyError, TypeError):
            logger.warning("Formato risposta ticker inatteso: %s", data)
            return []

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        size: float | None = None,
        amount: float | None = None,
    ):
        """Crea un ordine su Pionex.

        :param symbol:     coppia di trading, es. 'XAG_USDT'
        :param side:       'BUY' o 'SELL'
        :param order_type: 'MARKET' o 'LIMIT'
        :param size:       quantità in valuta base (per SELL o BUY in base asset)
        :param amount:     importo in valuta quotata, es. USDT (per BUY a importo fisso)
        """
        if size is None and amount is None:
            raise ValueError("È necessario specificare 'size' oppure 'amount'.")
        if size is not None and amount is not None:
            raise ValueError("Specificare 'size' oppure 'amount', non entrambi.")
        payload: dict = {"symbol": symbol, "side": side, "type": order_type}
        if amount is not None:
            payload["amount"] = amount
        if size is not None:
            payload["size"] = size
        return self._request("POST", "/api/v1/trade/order", body=payload)

    def test_connection(self) -> bool:
        """Verifica che le credenziali siano valide e l'API raggiungibile.

        :return: True se la connessione ha successo, False altrimenti.
        """
        result = self._request("GET", "/api/v1/common/timestamp")
        return result is not None
