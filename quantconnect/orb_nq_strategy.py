# ORB (Opening Range Breakout) Strategy — NQ E-mini Futures
# QuantConnect LEAN Python | NQ Futures 5M
# Long-only ORB with 200-day EMA trend filter, one trade per day
#
# READY TO RUN — paste into QuantConnect and hit Build & Backtest

from AlgorithmImports import *
from collections import defaultdict


class ORBNQStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2025, 11, 30)
        self.SetCash(50000)
        self.SetTimeZone("America/New_York")

        # ── NQ Continuous Futures (1-min data, consolidated to 5M) ───
        self.nq = self.AddFuture(
            Futures.Indices.NASDAQ100EMini,
            Resolution.Minute,
            dataNormalizationMode=DataNormalizationMode.BackwardsRatio,
            dataMappingMode=DataMappingMode.LastTradingDay,
            contractDepthOffset=0
        )
        self.nq.SetFilter(0, 90)
        self.symbol = None

        # ── Strategy Parameters ──────────────────────────────────────
        self.ORB_START        = time(9, 30)
        self.ORB_END          = time(9, 45)
        self.EOD_EXIT_TIME    = time(15, 45)
        self.ORB_SIZE_LIMIT   = 0.008       # 0.8% max ORB width
        self.MAX_STOP_POINTS  = 50          # 50 NQ pts = $1,000 max loss
        self.TARGET_MULT      = 0.50        # profit target = 50% of ORB range
        self.EMA_PERIOD       = 200

        # ── ORB State (reset every trading day) ──────────────────────
        self.orb_high         = None
        self.orb_low          = None
        self.orb_open_price   = None
        self.orb_defined      = False
        self.orb_skip_day     = False
        self.traded_today     = False
        self.entry_bar_time   = None        # timestamp of breakout bar
        self.last_trade_day   = None

        # ── Trade Management ─────────────────────────────────────────
        self.entry_price      = None
        self.stop_price       = None
        self.target_price     = None

        # ── Daily 200-period EMA ─────────────────────────────────────
        self.daily_closes_buf = []          # buffer until we have 200 closes
        self.daily_ema        = None
        self.last_daily_close = None
        self.last_daily_date  = None
        self.trend_bullish    = False

        # ── Trade Statistics ─────────────────────────────────────────
        self.total_trades     = 0
        self.winning_trades   = 0
        self.losing_trades    = 0
        self.trade_pnls       = []          # list of per-trade P&L values
        self.peak_equity      = 50000.0
        self.max_drawdown     = 0.0
        self.monthly_pnl      = defaultdict(float)   # "YYYY-MM" -> $

        # ── Consolidator tracking (contract → consolidator) ──────────
        self.consolidators    = {}

        # ── Schedule EOD exit at 15:45 ET ────────────────────────────
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.At(15, 45),
            self._eod_exit
        )

        # ── Warmup 300 calendar days (~200+ trading days for EMA) ────
        self.SetWarmUp(timedelta(days=300))

        self.Debug("ORB NQ Strategy initialized — NQ 5M, $50K, Long Only")

    # ══════════════════════════════════════════════════════════════════
    #  MAIN DATA HANDLER  (fires every 1-minute bar)
    # ══════════════════════════════════════════════════════════════════
    def OnData(self, data: Slice):
        # ── Get front-month contract from futures chain ──────────────
        chain = data.FutureChains.get(self.nq.Symbol)
        if chain is None:
            return
        contracts = sorted(chain, key=lambda c: c.Expiry)
        if not contracts:
            return

        contract_symbol = contracts[0].Symbol

        # ── Track daily closes for 200 EMA (always, even warmup) ─────
        if data.Bars.ContainsKey(contract_symbol):
            self._track_daily_close(float(data.Bars[contract_symbol].Close))

        if self.IsWarmingUp:
            return

        # ── Register 5-min consolidator when contract rolls ──────────
        if contract_symbol not in self.consolidators:
            for old_sym, old_con in list(self.consolidators.items()):
                self.SubscriptionManager.RemoveConsolidator(old_sym, old_con)
            self.consolidators.clear()

            consolidator = TradeBarConsolidator(timedelta(minutes=5))
            consolidator.DataConsolidated += self.OnFiveMinuteBar
            self.SubscriptionManager.AddConsolidator(contract_symbol, consolidator)
            self.consolidators[contract_symbol] = consolidator
            self.symbol = contract_symbol

        if self.symbol is None or not data.Bars.ContainsKey(self.symbol):
            return

        bar = data.Bars[self.symbol]

        # ── Track ORB high/low on 1-minute bars for accuracy ─────────
        self._track_orb(bar)

        # ── Execute pending entry (next bar after breakout signal) ────
        if (self.entry_bar_time is not None
                and self.Time > self.entry_bar_time
                and not self.Portfolio[self.symbol].Invested
                and not self.traded_today
                and not self.orb_skip_day):
            self.entry_bar_time = None
            self._execute_entry()

        # ── Check stop / target on every 1-min bar ───────────────────
        if self.Portfolio[self.symbol].Invested:
            self._check_exit_minute(bar)

        # ── Drawdown tracking on every bar while invested ────────────
        self._update_drawdown()

    # ══════════════════════════════════════════════════════════════════
    #  ORB TRACKING  (called on every 1-minute bar)
    # ══════════════════════════════════════════════════════════════════
    def _track_orb(self, bar):
        """Accumulate high/low during the 9:30-9:45 ET opening range."""
        today = self.Time.date()
        now   = self.Time.time()

        # ── Daily reset ──────────────────────────────────────────────
        if self.last_trade_day != today:
            self.last_trade_day = today
            self.orb_high       = None
            self.orb_low        = None
            self.orb_open_price = None
            self.orb_defined    = False
            self.orb_skip_day   = False
            self.traded_today   = False
            self.entry_bar_time = None
            self.entry_price    = None
            self.stop_price     = None
            self.target_price   = None

        # ── Accumulate during ORB window (9:30 <= t < 9:45) ──────────
        if self.ORB_START <= now < self.ORB_END:
            h = float(bar.High)
            l = float(bar.Low)
            if self.orb_high is None:
                self.orb_high       = h
                self.orb_low        = l
                self.orb_open_price = float(bar.Open)
            else:
                self.orb_high = max(self.orb_high, h)
                self.orb_low  = min(self.orb_low, l)

        # ── Finalize ORB once the window closes ──────────────────────
        if now >= self.ORB_END and not self.orb_defined and self.orb_high is not None:
            self.orb_defined = True
            orb_range = self.orb_high - self.orb_low
            orb_pct   = (orb_range / self.orb_open_price
                         if self.orb_open_price > 0 else 0)

            if orb_pct > self.ORB_SIZE_LIMIT:
                self.orb_skip_day = True
                self.Debug(
                    f"{today} ORB SKIP — range {orb_range:.2f} pts "
                    f"({orb_pct * 100:.2f}%) > 0.8% limit")
            else:
                self.Debug(
                    f"{today} ORB SET — H={self.orb_high:.2f}  "
                    f"L={self.orb_low:.2f}  Range={orb_range:.2f}")

    # ══════════════════════════════════════════════════════════════════
    #  DAILY 200 EMA
    # ══════════════════════════════════════════════════════════════════
    def _track_daily_close(self, close):
        """Record the last close of each calendar day for EMA updates."""
        today = self.Time.date()

        if self.last_daily_date is None:
            self.last_daily_date  = today
            self.last_daily_close = close
            return

        if today != self.last_daily_date:
            # New calendar day → commit previous day's final close
            self._update_daily_ema(self.last_daily_close)
            self.last_daily_date = today

        self.last_daily_close = close

    def _update_daily_ema(self, close):
        """Update the 200-period daily EMA (SMA seed then exponential)."""
        if self.daily_ema is None:
            self.daily_closes_buf.append(close)
            if len(self.daily_closes_buf) >= self.EMA_PERIOD:
                # Seed with SMA of first 200 daily closes
                self.daily_ema = (sum(self.daily_closes_buf)
                                  / len(self.daily_closes_buf))
                self.trend_bullish = close > self.daily_ema
                self.daily_closes_buf = []          # free memory
        else:
            k = 2.0 / (self.EMA_PERIOD + 1)
            self.daily_ema = close * k + self.daily_ema * (1 - k)
            self.trend_bullish = close > self.daily_ema

    # ══════════════════════════════════════════════════════════════════
    #  5-MINUTE BAR HANDLER  (breakout / downside-break detection)
    # ══════════════════════════════════════════════════════════════════
    def OnFiveMinuteBar(self, sender, bar):
        """Detect ORB breakout or downside break on each 5-min close."""
        if self.IsWarmingUp or self.symbol is None:
            return
        if not self.orb_defined or self.orb_skip_day or self.traded_today:
            return
        if self.Portfolio[self.symbol].Invested:
            return
        if not self.trend_bullish:
            return

        now   = self.Time.time()
        close = float(bar.Close)

        # Ignore bars during or before the ORB window
        if now <= self.ORB_END:
            return

        # Rule 5 & 9 — downside break first → done for the day
        if close < self.orb_low:
            self.orb_skip_day = True
            self.traded_today = True
            self.Debug(
                f"{self.Time.date()} ORB DOWNSIDE BREAK at {close:.2f} "
                f"< ORB low {self.orb_low:.2f} — day skipped")
            return

        # Rule 4 — 5-min candle closes above ORB high → entry next bar
        if close > self.orb_high:
            self.entry_bar_time = self.Time
            self.Debug(
                f"{self.Time.date()} ORB BREAKOUT SIGNAL — close {close:.2f} "
                f"> ORB high {self.orb_high:.2f}")

    # ══════════════════════════════════════════════════════════════════
    #  ENTRY EXECUTION
    # ══════════════════════════════════════════════════════════════════
    def _execute_entry(self):
        """Place a long market order (1 NQ contract).
        Stop & target are set in OnOrderEvent once the fill arrives."""
        if self.orb_high is None or self.orb_low is None:
            return

        self.MarketOrder(self.symbol, 1)
        self.traded_today  = True
        self.total_trades += 1

    # ══════════════════════════════════════════════════════════════════
    #  EXIT CHECKS  (1-minute granularity)
    # ══════════════════════════════════════════════════════════════════
    def _check_exit_minute(self, bar):
        """Check stop loss and take profit on every 1-minute bar."""
        if not self.Portfolio[self.symbol].Invested:
            return
        if self.stop_price is None or self.target_price is None:
            return

        low  = float(bar.Low)
        high = float(bar.High)

        # Check stop first (conservative — assume worst case)
        if low <= self.stop_price:
            self._close_position("STOP HIT", is_win=False)
            return

        if high >= self.target_price:
            self._close_position("TARGET HIT", is_win=True)

    def _eod_exit(self):
        """Scheduled EOD exit at 15:45 ET — force close any open position."""
        if self.IsWarmingUp:
            return
        if self.symbol is None:
            return
        if not self.Portfolio[self.symbol].Invested:
            return
        self._close_position("EOD EXIT 15:45", is_win=None)

    def _close_position(self, reason, is_win=None):
        """Liquidate and record trade statistics."""
        if self.symbol is None or not self.Portfolio[self.symbol].Invested:
            return

        pnl = float(self.Portfolio[self.symbol].UnrealizedProfit)

        if is_win is None:
            is_win = pnl >= 0

        if is_win:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        self.trade_pnls.append(pnl)

        # Monthly P&L bucket
        month_key = self.Time.strftime("%Y-%m")
        self.monthly_pnl[month_key] += pnl

        self.Liquidate(self.symbol)

        entry_str = f"{self.entry_price:.2f}" if self.entry_price else "N/A"
        self.Debug(
            f"{reason} | PnL: ${pnl:,.0f} | Entry: {entry_str} | "
            f"Time: {self.Time}")

        # Reset trade state
        self.entry_price  = None
        self.stop_price   = None
        self.target_price = None

    # ══════════════════════════════════════════════════════════════════
    #  DRAWDOWN TRACKING
    # ══════════════════════════════════════════════════════════════════
    def _update_drawdown(self):
        """Update peak equity and max drawdown on every bar."""
        equity = float(self.Portfolio.TotalPortfolioValue)
        if equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity
            if dd > self.max_drawdown:
                self.max_drawdown = dd

    # ══════════════════════════════════════════════════════════════════
    #  ORDER EVENTS
    # ══════════════════════════════════════════════════════════════════
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status != OrderStatus.Filled:
            return

        fill_price = float(orderEvent.FillPrice)

        # ── Entry fill → compute stop & target from actual fill ──────
        if (orderEvent.Direction == OrderDirection.Buy
                and self.orb_high is not None
                and self.orb_low is not None
                and self.entry_price is None):

            self.entry_price = fill_price
            orb_range = self.orb_high - self.orb_low

            # Stop: ORB Low, capped at 50 NQ points below fill
            stop = self.orb_low
            if fill_price - stop > self.MAX_STOP_POINTS:
                stop = fill_price - self.MAX_STOP_POINTS
            self.stop_price = stop

            # Target: fill + 50% of ORB range
            self.target_price = fill_price + orb_range * self.TARGET_MULT

            self.Debug(
                f"LONG FILLED | Entry:{fill_price:.2f} | "
                f"Stop:{stop:.2f} | Target:{self.target_price:.2f} | "
                f"ORB Range:{orb_range:.2f}")

        self.Log(
            f"Order filled | {orderEvent.Direction} | "
            f"Qty:{orderEvent.FillQuantity} | "
            f"Price:{fill_price:.2f}")

    # ══════════════════════════════════════════════════════════════════
    #  END-OF-BACKTEST STATISTICS
    # ══════════════════════════════════════════════════════════════════
    def OnEndOfAlgorithm(self):
        equity = float(self.Portfolio.TotalPortfolioValue)
        net    = float(self.Portfolio.TotalNetProfit)
        wr     = ((self.winning_trades / self.total_trades * 100)
                  if self.total_trades > 0 else 0)

        wins   = [p for p in self.trade_pnls if p >= 0]
        losses = [p for p in self.trade_pnls if p < 0]
        avg_win  = sum(wins) / len(wins)     if wins   else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        gross_profit = sum(wins)
        gross_loss   = abs(sum(losses))
        profit_factor = (gross_profit / gross_loss
                         if gross_loss > 0 else float('inf'))

        # Max consecutive losses
        max_consec = 0
        current    = 0
        for p in self.trade_pnls:
            if p < 0:
                current += 1
                max_consec = max(max_consec, current)
            else:
                current = 0

        self.Log("=" * 60)
        self.Log("ORB NQ STRATEGY — FINAL RESULTS")
        self.Log("=" * 60)
        self.Log(f"Total Portfolio Value:    ${equity:,.0f}")
        self.Log(f"Total Net P&L:           ${net:,.0f}")
        self.Log(f"Total Return:            {net / 50000 * 100:.1f}%")
        self.Log("-" * 40)
        self.Log(f"Total Trades:            {self.total_trades}")
        self.Log(f"Winning Trades:          {self.winning_trades}")
        self.Log(f"Losing Trades:           {self.losing_trades}")
        self.Log(f"Win Rate:                {wr:.1f}%")
        self.Log("-" * 40)
        self.Log(f"Average Win:             ${avg_win:,.0f}")
        self.Log(f"Average Loss:            ${avg_loss:,.0f}")
        self.Log(f"Profit Factor:           {profit_factor:.2f}")
        self.Log(f"Max Consecutive Losses:  {max_consec}")
        self.Log(f"Max Drawdown:            {self.max_drawdown * 100:.1f}%")
        self.Log("=" * 60)
        self.Log("MONTHLY P&L TABLE")
        self.Log("-" * 40)
        for month in sorted(self.monthly_pnl.keys()):
            pnl = self.monthly_pnl[month]
            marker = "+" if pnl >= 0 else "-"
            self.Log(f"  {month}:  {marker}${abs(pnl):>10,.0f}")
        self.Log("=" * 60)
