"""
Elder S&D Live Trading Bot — Main Orchestrator.

Connects ProjectX market data → Strategy → Order execution.

Flow:
  1. Authenticate with ProjectX Gateway
  2. Resolve front-month ES contract
  3. Connect SignalR WebSocket for live quotes
  4. Aggregate ticks into 5-minute bars
  5. Feed bars to ElderSupplyDemandStrategy
  6. Execute signals via ProjectX REST orders
  7. Manage stop-loss, take-profit, and EOD exit
  8. Send Telegram notifications on trades

Usage:
  python -m live_trading.bot
"""
from __future__ import annotations

import logging
import signal
import sys
import time as _time
from collections import deque
from datetime import datetime, time, timedelta

import pytz

from live_trading.config import Config, load_config
from live_trading.projectx_client import ProjectXRest, ProjectXWebSocket
from live_trading.strategy import Bar, ElderSupplyDemandStrategy, Signal
from live_trading.telegram_notifier import TelegramNotifier

log = logging.getLogger("elder_bot")


class BarAggregator:
    """
    Aggregate quote ticks into fixed-interval OHLCV bars.

    ProjectX sends quote updates with bid/ask/last price.
    We build bars from the last-traded price.
    """

    def __init__(self, interval_minutes: int = 5):
        self.interval = interval_minutes * 60  # seconds
        self._current_open: float = 0
        self._current_high: float = 0
        self._current_low: float = float("inf")
        self._current_close: float = 0
        self._current_volume: float = 0
        self._bar_start: float = 0  # epoch
        self._has_data = False

    def on_tick(self, price: float, volume: float = 1.0, timestamp: float = 0) -> Bar | None:
        """
        Feed a tick. Returns a completed Bar when the interval elapses.
        """
        if timestamp == 0:
            timestamp = _time.time()

        # Calculate bar boundary
        bar_start = timestamp - (timestamp % self.interval)

        if not self._has_data:
            # First tick
            self._bar_start = bar_start
            self._current_open = price
            self._current_high = price
            self._current_low = price
            self._current_close = price
            self._current_volume = volume
            self._has_data = True
            return None

        if bar_start > self._bar_start:
            # New bar period — emit the completed bar
            completed = Bar(
                timestamp=self._bar_start,
                open=self._current_open,
                high=self._current_high,
                low=self._current_low,
                close=self._current_close,
                volume=self._current_volume,
            )
            # Start new bar
            self._bar_start = bar_start
            self._current_open = price
            self._current_high = price
            self._current_low = price
            self._current_close = price
            self._current_volume = volume
            return completed

        # Same bar — update OHLCV
        self._current_high = max(self._current_high, price)
        self._current_low = min(self._current_low, price)
        self._current_close = price
        self._current_volume += volume
        return None


class TradingBot:
    """
    Main bot orchestrator.

    Lifecycle:
      bot = TradingBot()
      bot.start()   # blocks until shutdown
    """

    def __init__(self, config: Config | None = None):
        self.cfg = config or load_config()
        self.rest = ProjectXRest(self.cfg.projectx)
        self.ws = ProjectXWebSocket(self.cfg.projectx)
        self.strategy = ElderSupplyDemandStrategy(self.cfg.strategy, self.cfg.risk)
        self.telegram = TelegramNotifier(self.cfg.telegram)
        self.aggregator = BarAggregator(self.cfg.session.bar_interval_minutes)
        self.tz = pytz.timezone(self.cfg.session.timezone)

        # Trade state
        self.traded_today: bool = False
        self.last_trade_day: datetime | None = None
        self.in_position: bool = False
        self.position_direction: str = ""  # "long" | "short"
        self.position_qty: int = 0
        self.entry_price: float = 0
        self.stop_price: float = 0
        self.target_price: float = 0

        # Last known price for exit checks
        self._last_price: float = 0

        self._running = False
        self._bars_processed = 0

    # ── Startup ──────────────────────────────────────────────────────
    def start(self):
        """Authenticate, resolve contract, connect WS, run main loop."""
        self._running = True
        log.info("=" * 60)
        log.info("Elder S&D Trading Bot — Starting")
        log.info("=" * 60)

        try:
            # 1. Authenticate
            self.rest.login()

            # 2. Find account
            accounts = self.rest.get_accounts()
            if not accounts:
                raise RuntimeError("No accounts found")
            acct = accounts[0]
            acct_id = acct.get("accountId") or acct.get("id", 0)
            self.rest.set_account(acct_id)
            log.info("Account: %s", acct.get("name", acct_id))

            # 3. Find front-month contract
            contract_id = self.rest.find_front_month_contract(self.cfg.risk.symbol)
            self.cfg.projectx.contract_id = contract_id

            # 4. Connect WebSocket
            self.ws.connect(
                on_quote=self._on_quote,
                on_order_update=self._on_order_update,
            )
            self.ws.subscribe_quotes(contract_id)
            self.ws.subscribe_orders(acct_id)

            self.telegram.notify_status(
                f"Bot started | Account: {acct_id} | Contract: {contract_id}"
            )

            # 5. Main loop
            self._main_loop()

        except KeyboardInterrupt:
            log.info("Shutdown requested")
        except Exception:
            log.exception("Fatal error")
            self.telegram.notify_error("Bot crashed — check logs")
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown."""
        self._running = False
        log.info("Shutting down...")
        self.ws.disconnect()
        self.rest.close()
        self.telegram.notify_status("Bot stopped")
        self.telegram.close()
        log.info("Shutdown complete")

    # ── Main Loop ────────────────────────────────────────────────────
    def _main_loop(self):
        """
        Keep the main thread alive.
        Actual processing happens in _on_quote callback (SignalR thread).
        Periodic checks run here for EOD exit and daily reset.
        """
        log.info("Main loop started — waiting for market data...")
        while self._running:
            try:
                now = datetime.now(self.tz)

                # Daily reset
                self._daily_reset(now)

                # EOD exit check
                if self.in_position and now.time() >= self.cfg.session.eod_exit_time:
                    log.info("EOD exit triggered at %s", now.strftime("%H:%M:%S"))
                    self._exit_position("EOD_EXIT")

                _time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception:
                log.exception("Error in main loop")
                _time.sleep(5)

    def _daily_reset(self, now: datetime):
        today = now.date()
        if self.last_trade_day != today:
            self.last_trade_day = today
            self.traded_today = False
            self.strategy.reset_daily()
            log.info("New trading day: %s", today)

    # ── Quote Handler (SignalR callback) ─────────────────────────────
    def _on_quote(self, quote: dict):
        """
        Called by SignalR on each quote update.
        Extracts price, feeds to bar aggregator, processes completed bars.
        """
        # Extract price from quote — ProjectX uses various field names
        price = (
            quote.get("lastPrice")
            or quote.get("last")
            or quote.get("tradePrice")
            or quote.get("bestBid")  # fallback to bid
            or 0
        )
        if price <= 0:
            return

        volume = quote.get("lastSize") or quote.get("volume") or 1
        timestamp = _time.time()
        self._last_price = price

        # Check stop/target on every tick while in position
        if self.in_position:
            self._check_tick_exit(price)

        # Aggregate into bar
        bar = self.aggregator.on_tick(price, volume, timestamp)
        if bar is None:
            return

        # Got a completed 5-minute bar
        self._bars_processed += 1
        self._process_bar(bar)

    def _on_order_update(self, update: dict):
        """Handle order fill notifications from ProjectX."""
        status = update.get("status") or update.get("orderStatus", "")
        if status in ("Filled", "filled", "FILLED"):
            fill_price = update.get("fillPrice") or update.get("avgFillPrice", 0)
            log.info("Order FILLED @ %.2f | %s", fill_price, update)

    # ── Bar Processing ───────────────────────────────────────────────
    def _process_bar(self, bar: Bar):
        """Feed bar to strategy, execute signal if returned."""
        now = datetime.now(self.tz)
        current_time = now.time()

        log.debug(
            "Bar #%d | O:%.2f H:%.2f L:%.2f C:%.2f V:%.0f",
            self._bars_processed, bar.open, bar.high, bar.low, bar.close, bar.volume,
        )

        # Skip if already traded today or outside session
        if self.traded_today or self.in_position:
            return
        if current_time < self.cfg.session.no_entry_before:
            return
        if current_time > self.cfg.session.no_entry_after:
            return

        # Feed to strategy
        signal = self.strategy.on_bar(bar)
        if signal is None:
            return

        # Execute the trade
        self._execute_signal(signal)

    # ── Trade Execution ──────────────────────────────────────────────
    def _execute_signal(self, sig: Signal):
        """Place market entry with bracket stop/target orders."""
        log.info(
            "%s SIGNAL | Entry:%.2f Stop:%.2f Target:%.2f Qty:%d Score:%d/4",
            sig.direction.upper(), sig.entry, sig.stop, sig.target,
            sig.contracts, sig.score,
        )

        try:
            # Entry order
            side = "Buy" if sig.direction == "long" else "Sell"
            self.rest.place_market_order(side, sig.contracts)

            # Protective stop
            stop_side = "Sell" if sig.direction == "long" else "Buy"
            self.rest.place_stop_order(stop_side, sig.contracts, sig.stop)

            # Take-profit limit
            self.rest.place_limit_order(stop_side, sig.contracts, sig.target)

            # Update state
            self.in_position = True
            self.position_direction = sig.direction
            self.position_qty = sig.contracts
            self.entry_price = sig.entry
            self.stop_price = sig.stop
            self.target_price = sig.target
            self.traded_today = True

            rr = abs(sig.target - sig.entry) / abs(sig.entry - sig.stop)
            log.info(
                "TRADE ENTERED | %s x%d @ %.2f | SL:%.2f TP:%.2f | R:R %.1f",
                sig.direction.upper(), sig.contracts, sig.entry,
                sig.stop, sig.target, rr,
            )

            self.telegram.notify_entry(
                sig.direction, sig.entry, sig.stop, sig.target,
                sig.contracts, sig.score,
            )

        except Exception:
            log.exception("Order execution failed")
            self.telegram.notify_error("Order execution failed — check logs")

    # ── Exit Logic ───────────────────────────────────────────────────
    def _check_tick_exit(self, price: float):
        """Check stop/target on each tick for faster exit detection."""
        if not self.in_position:
            return

        hit_stop = False
        hit_target = False

        if self.position_direction == "long":
            if price <= self.stop_price:
                hit_stop = True
            if price >= self.target_price:
                hit_target = True
        else:
            if price >= self.stop_price:
                hit_stop = True
            if price <= self.target_price:
                hit_target = True

        if hit_target:
            self._exit_position("TARGET_HIT")
        elif hit_stop:
            self._exit_position("STOP_HIT")

    def _exit_position(self, reason: str):
        """Flatten position and cancel open orders."""
        if not self.in_position:
            return

        log.info("EXIT: %s | Price: %.2f", reason, self._last_price)

        try:
            self.rest.cancel_all_orders()
            self.rest.flatten_position()
        except Exception:
            log.exception("Error flattening position")

        # Calculate P&L
        if self.position_direction == "long":
            pnl = (self._last_price - self.entry_price) * self.position_qty * self.cfg.risk.es_point_value
        else:
            pnl = (self.entry_price - self._last_price) * self.position_qty * self.cfg.risk.es_point_value

        self.telegram.notify_exit(
            reason, self.position_direction, self.entry_price,
            self._last_price, self.position_qty, pnl,
        )

        log.info(
            "TRADE CLOSED | %s | Entry:%.2f Exit:%.2f | P&L: $%+,.0f",
            reason, self.entry_price, self._last_price, pnl,
        )

        # Reset position state
        self.in_position = False
        self.position_direction = ""
        self.position_qty = 0
        self.entry_price = 0
        self.stop_price = 0
        self.target_price = 0


# ── Entry Point ──────────────────────────────────────────────────────
def main():
    cfg = load_config()

    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    bot = TradingBot(cfg)

    # Graceful shutdown on SIGINT/SIGTERM
    def _shutdown(signum, frame):
        log.info("Signal %d received — shutting down", signum)
        bot._running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    bot.start()


if __name__ == "__main__":
    main()
