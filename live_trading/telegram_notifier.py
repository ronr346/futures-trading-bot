"""
Telegram trade notification service.

Sends formatted trade entry, exit, and status messages
to a Telegram chat via the Bot API.
"""
from __future__ import annotations

import logging
from datetime import datetime

import httpx

from live_trading.config import TelegramConfig

log = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramNotifier:
    """Send trade alerts to Telegram."""

    def __init__(self, cfg: TelegramConfig):
        self.cfg = cfg
        self._client = httpx.Client(timeout=10.0)

    def _send(self, text: str):
        if not self.cfg.enabled:
            return
        url = f"{TELEGRAM_API}/bot{self.cfg.bot_token}/sendMessage"
        try:
            resp = self._client.post(
                url,
                json={
                    "chat_id": self.cfg.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            if resp.status_code != 200:
                log.warning("Telegram send failed: %s", resp.text)
        except Exception:
            log.exception("Telegram send error")

    # ── Trade Notifications ──────────────────────────────────────────
    def notify_entry(
        self,
        direction: str,
        entry: float,
        stop: float,
        target: float,
        contracts: int,
        score: int,
    ):
        arrow = "BUY" if direction == "long" else "SELL"
        rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0
        text = (
            f"<b>TRADE ENTRY - {arrow}</b>\n"
            f"Entry: {entry:.2f}\n"
            f"Stop: {stop:.2f}\n"
            f"Target: {target:.2f}\n"
            f"Contracts: {contracts}\n"
            f"Score: {score}/4\n"
            f"R:R: {rr:.1f}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S ET')}"
        )
        self._send(text)

    def notify_exit(
        self,
        reason: str,
        direction: str,
        entry: float,
        exit_price: float,
        contracts: int,
        pnl: float,
    ):
        text = (
            f"<b>TRADE EXIT - {reason.upper()}</b>\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry:.2f}\n"
            f"Exit: {exit_price:.2f}\n"
            f"Contracts: {contracts}\n"
            f"P&L: ${pnl:+,.0f}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S ET')}"
        )
        self._send(text)

    def notify_status(self, message: str):
        self._send(f"<b>BOT STATUS</b>\n{message}")

    def notify_error(self, error: str):
        self._send(f"<b>BOT ERROR</b>\n{error}")

    def close(self):
        self._client.close()
