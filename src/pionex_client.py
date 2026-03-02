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

        Per GET:  tutti i parametri (inclusi auth) vanno nella query string.
        Per POST: i parametri di autenticazione (timestamp, recvWindow, signature)
                  vanno nella query string; il payload dell'ordine va nel body JSON.

        :return: dizionario JSON della risposta, o None in caso di errore.
        """
        params = dict(params or {})
        ts = int(time.time() * 1000)

        headers = {
            "PIONEX-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                # Firma tutti i parametri GET nella query string
                query_params = {**params, "timestamp": ts, "recvWindow": 5000}
                query_params["signature"] = self._sign(query_params)
                response = requests.get(url, params=query_params, headers=headers, timeout=10)
            elif method == "POST":
                # Firma solo i parametri di autenticazione nella query string;
                # il payload dell'ordine va nel body JSON
                auth_params = {"timestamp": ts, "recvWindow": 5000}
                auth_params["signature"] = self._sign(auth_params)
                response = requests.post(
                    url, params=auth_params, json=params, headers=headers, timeout=10
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

    def get_ticker(self, symbol: str | None = None):
        """Restituisce i dati di mercato (ticker).

        :param symbol: es. 'PAXG_USDT'; se None, restituisce tutti i ticker.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v1/market/tickers", params)

    def get_tickers(self) -> list:
        """Restituisce la lista di tutti i ticker di mercato.

        :return: lista di dizionari ticker, oppure [] in caso di errore o forma inattesa.
        """
        result = self._request("GET", "/api/v1/market/tickers", {})
        try:
            tickers = result.get("data", {}).get("tickers", [])
            if isinstance(tickers, list):
                return tickers
        except (AttributeError, TypeError):
            pass
        logger.warning("Risposta ticker inattesa: %s", result)
        return []

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float | None = None,
        amount: float | None = None,
    ):
        """Crea un ordine su Pionex.

        :param symbol:     coppia di trading, es. 'PAXG_USDT'
        :param side:       'BUY' o 'SELL'
        :param order_type: 'MARKET' o 'LIMIT'
        :param quantity:   quantità base da acquistare/vendere (base asset)
        :param amount:     importo in valuta di quotazione da spendere (es. USDT)
                           per acquisti MARKET basati sulla quota; alternativo a quantity.
        """
        payload: dict = {"symbol": symbol, "side": side, "type": order_type}
        if amount is not None:
            payload["amount"] = amount
        elif quantity is not None:
            payload["quantity"] = quantity
        return self._request("POST", "/api/v1/trade/order", payload)

    def get_balance(self, currency: str | None = None) -> list:
        """Restituisce i saldi dell'account.

        :param currency: se specificato, filtra per la valuta indicata (es. 'USDT', 'XAG').
        :return: lista di dizionari saldo, oppure [] in caso di errore o forma inattesa.
        """
        params: dict = {}
        if currency:
            params["currency"] = currency
        result = self._request("GET", "/api/v1/account/balances", params)
        try:
            balances = result.get("data", {}).get("balances", [])
            if isinstance(balances, list):
                return balances
        except (AttributeError, TypeError):
            pass
        logger.warning("Risposta saldi inattesa: %s", result)
        return []

    def test_connection(self) -> bool:
        """Verifica che le credenziali siano valide e l'API raggiungibile.

        :return: True se la connessione ha successo, False altrimenti.
        """
        result = self._request("GET", "/api/v1/common/timestamp")
        return result is not None
