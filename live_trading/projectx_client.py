"""
ProjectX Gateway API client — REST (httpx) + SignalR WebSocket (signalrcore).

Handles authentication, order management, account/position queries,
and real-time market data streaming for TopStep funded accounts.
"""
from __future__ import annotations

import logging
import threading
import time as _time
from datetime import datetime, timezone
from typing import Callable

import httpx
from signalrcore.hub_connection_builder import HubConnectionBuilder

from live_trading.config import ProjectXConfig

log = logging.getLogger(__name__)


# ── REST Client ─────────────────────────────────────────────────────
class ProjectXRest:
    """Synchronous REST wrapper around the ProjectX Gateway API."""

    def __init__(self, cfg: ProjectXConfig):
        self.cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.base_url,
            timeout=30.0,
            headers={"Content-Type": "application/json"},
        )

    # ── Auth ─────────────────────────────────────────────────────────
    def login(self) -> str:
        """Authenticate with API key, store token. Returns token."""
        resp = self._client.post(
            "/api/Auth/loginKey",
            json={"userName": self.cfg.username, "apiKey": self.cfg.api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token") or data.get("Token", "")
        if not token:
            raise RuntimeError(f"Login failed — response: {data}")
        self.cfg.token = token
        self._client.headers["Authorization"] = f"Bearer {token}"
        log.info("Authenticated with ProjectX Gateway")
        return token

    def _ensure_auth(self):
        if not self.cfg.token:
            self.login()

    # ── Accounts ─────────────────────────────────────────────────────
    def get_accounts(self) -> list[dict]:
        self._ensure_auth()
        resp = self._client.get("/api/Account/search")
        resp.raise_for_status()
        accounts = resp.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("accounts", accounts.get("data", []))
        log.info("Found %d account(s)", len(accounts))
        return accounts

    def set_account(self, account_id: int):
        self.cfg.account_id = account_id
        log.info("Using account ID: %d", account_id)

    # ── Contracts ────────────────────────────────────────────────────
    def search_contracts(self, symbol: str = "ES") -> list[dict]:
        self._ensure_auth()
        resp = self._client.get(
            "/api/Contract/search", params={"name": symbol}
        )
        resp.raise_for_status()
        contracts = resp.json()
        if isinstance(contracts, dict):
            contracts = contracts.get("contracts", contracts.get("data", []))
        return contracts

    def find_front_month_contract(self, symbol: str = "ES") -> int:
        """Find front-month contract ID for the given symbol."""
        contracts = self.search_contracts(symbol)
        if not contracts:
            raise RuntimeError(f"No contracts found for {symbol}")
        # Sort by expiry, take closest future
        now = datetime.now(timezone.utc)
        future_contracts = []
        for c in contracts:
            exp = c.get("expirationDate") or c.get("expiration", "")
            try:
                exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                if exp_dt > now:
                    future_contracts.append((exp_dt, c))
            except (ValueError, TypeError):
                future_contracts.append((datetime.max.replace(tzinfo=timezone.utc), c))
        if not future_contracts:
            # Fall back to first contract
            cid = contracts[0].get("contractId") or contracts[0].get("id", 0)
            log.warning("No future contracts found, using first: %s", cid)
            return cid
        future_contracts.sort(key=lambda x: x[0])
        front = future_contracts[0][1]
        cid = front.get("contractId") or front.get("id", 0)
        log.info("Front-month %s contract ID: %d", symbol, cid)
        return cid

    # ── Orders ───────────────────────────────────────────────────────
    def place_market_order(self, side: str, size: int) -> dict:
        """Place a market order. side: 'Buy' or 'Sell'."""
        self._ensure_auth()
        payload = {
            "accountId": self.cfg.account_id,
            "contractId": self.cfg.contract_id,
            "type": "Market",
            "side": side,
            "size": size,
        }
        log.info("Placing MARKET %s x%d", side, size)
        resp = self._client.post("/api/Order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def place_stop_order(self, side: str, size: int, stop_price: float) -> dict:
        """Place a stop order for stop-loss."""
        self._ensure_auth()
        payload = {
            "accountId": self.cfg.account_id,
            "contractId": self.cfg.contract_id,
            "type": "Stop",
            "side": side,
            "size": size,
            "stopPrice": stop_price,
        }
        log.info("Placing STOP %s x%d @ %.2f", side, size, stop_price)
        resp = self._client.post("/api/Order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def place_limit_order(self, side: str, size: int, limit_price: float) -> dict:
        """Place a limit order for take-profit."""
        self._ensure_auth()
        payload = {
            "accountId": self.cfg.account_id,
            "contractId": self.cfg.contract_id,
            "type": "Limit",
            "side": side,
            "size": size,
            "limitPrice": limit_price,
        }
        log.info("Placing LIMIT %s x%d @ %.2f", side, size, limit_price)
        resp = self._client.post("/api/Order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def cancel_all_orders(self) -> None:
        """Cancel all open orders for the account."""
        self._ensure_auth()
        resp = self._client.delete(
            "/api/Order/cancelAll",
            params={"accountId": self.cfg.account_id},
        )
        resp.raise_for_status()
        log.info("Cancelled all open orders")

    # ── Positions ────────────────────────────────────────────────────
    def get_positions(self) -> list[dict]:
        self._ensure_auth()
        resp = self._client.get(
            "/api/Position/search",
            params={"accountId": self.cfg.account_id},
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("positions", data.get("data", []))
        return data

    def flatten_position(self) -> dict | None:
        """Close any open position by sending an opposite market order."""
        positions = self.get_positions()
        for pos in positions:
            contract_id = pos.get("contractId") or pos.get("contract_id", 0)
            if contract_id != self.cfg.contract_id:
                continue
            qty = pos.get("size") or pos.get("quantity", 0)
            if qty == 0:
                continue
            side = "Sell" if qty > 0 else "Buy"
            log.info("Flattening position: %s x%d", side, abs(qty))
            return self.place_market_order(side, abs(qty))
        return None

    def close(self):
        self._client.close()


# ── SignalR WebSocket Client ────────────────────────────────────────
class ProjectXWebSocket:
    """
    SignalR hub connection for real-time market data.

    Receives quote ticks and passes them to a callback.
    Runs in a background thread.
    """

    def __init__(self, cfg: ProjectXConfig):
        self.cfg = cfg
        self._hub: HubConnectionBuilder | None = None
        self._connection = None
        self._connected = threading.Event()
        self._stop = threading.Event()
        self._on_quote: Callable | None = None
        self._on_order_update: Callable | None = None

    def connect(
        self,
        on_quote: Callable[[dict], None],
        on_order_update: Callable[[dict], None] | None = None,
    ):
        """Build and start the SignalR connection."""
        if not self.cfg.token:
            raise RuntimeError("Must authenticate before connecting WebSocket")

        self._on_quote = on_quote
        self._on_order_update = on_order_update

        hub_url = f"{self.cfg.base_url}/hubs/userHub"
        options = {"access_token_factory": lambda: self.cfg.token}

        self._connection = (
            HubConnectionBuilder()
            .with_url(hub_url, options=options)
            .with_automatic_reconnect(
                {"type": "interval", "intervals": [1, 2, 5, 10, 30]}
            )
            .build()
        )

        self._connection.on_open(self._on_open)
        self._connection.on_close(self._on_close)
        self._connection.on_error(self._on_error)

        # Register server-invoked handlers
        self._connection.on("GotQuote", self._handle_quote)
        self._connection.on("GotQuoteData", self._handle_quote)
        self._connection.on("OrderUpdate", self._handle_order_update)
        self._connection.on("GotContractQuote", self._handle_quote)

        log.info("Connecting SignalR to %s", hub_url)
        self._connection.start()
        # Wait for connection with timeout
        if not self._connected.wait(timeout=15):
            log.warning("SignalR connection timed out, may still connect")

    def subscribe_quotes(self, contract_id: int):
        """Subscribe to real-time quotes for a contract."""
        if self._connection is None:
            raise RuntimeError("Not connected")
        log.info("Subscribing to quotes for contract %d", contract_id)
        self._connection.send("SubscribeQuotes", [contract_id])

    def unsubscribe_quotes(self, contract_id: int):
        if self._connection:
            self._connection.send("UnsubscribeQuotes", [contract_id])

    def subscribe_orders(self, account_id: int):
        """Subscribe to order updates for an account."""
        if self._connection:
            log.info("Subscribing to order updates for account %d", account_id)
            self._connection.send("SubscribeOrders", [account_id])

    # ── Internal handlers ────────────────────────────────────────────
    def _on_open(self):
        log.info("SignalR connected")
        self._connected.set()

    def _on_close(self):
        log.warning("SignalR disconnected")
        self._connected.clear()

    def _on_error(self, error):
        log.error("SignalR error: %s", error)

    def _handle_quote(self, args):
        """Route incoming quote data to the callback."""
        if self._on_quote and args:
            quote = args[0] if isinstance(args, list) else args
            try:
                self._on_quote(quote)
            except Exception:
                log.exception("Error in quote handler")

    def _handle_order_update(self, args):
        if self._on_order_update and args:
            update = args[0] if isinstance(args, list) else args
            try:
                self._on_order_update(update)
            except Exception:
                log.exception("Error in order update handler")

    def disconnect(self):
        self._stop.set()
        if self._connection:
            try:
                self._connection.stop()
            except Exception:
                pass
            log.info("SignalR disconnected")
