# ORB (Opening Range Breakout) Strategy — NQ Micro Futures (MNQ)
# QuantConnect LEAN Python | MNQ Futures 5M
# Long-only ORB with 200-day EMA trend filter, one trade per day
# Apex Trader Funding rules: ApexRiskManager (no daily limit, EOD trailing DD $2,500)
#
# Updated: 2026-02-25 — NQ→MNQ, TopStep→ApexRiskManager, dynamic sizing

from AlgorithmImports import *
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# ApexRiskManager — Inlined (no external module needed for QuantConnect)
# ═══════════════════════════════════════════════════════════════════
class ApexRiskManager:
    """
    Apex Trader Funding risk manager for QuantConnect LEAN strategies.
    Instantiate in Initialize(), call methods at entry and EOD.
    """

    def __init__(self, algorithm, start_equity=50000,
                 profit_target=3000, dd_buffer=2500, monthly_lock=3000):
        self.algo           = algorithm
        self.start_equity   = start_equity
        self.profit_target  = profit_target
        self.dd_buffer      = dd_buffer          # Apex: $2,500
        self.monthly_lock   = monthly_lock       # stop month at $3,000

        # Trailing DD floor (only moves up, never down)
        self.peak_equity    = float(start_equity)
        self.dd_floor       = float(start_equity) - dd_buffer  # $47,500
        self.dd_locked      = False              # True when floor stops moving

        # Monthly P&L tracking
        self.monthly_pnl    = {}                 # "YYYY-MM" -> float

        # Consistency cap: 30% of profit_target per day
        self.daily_cap      = profit_target * 0.30   # $900

    def update_equity(self, current_equity):
        """Update peak equity and DD floor (intraday, for monitoring)."""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            if not self.dd_locked:
                new_floor = self.peak_equity - self.dd_buffer
                if new_floor > self.dd_floor:
                    self.dd_floor = new_floor
        if not self.dd_locked and self.dd_floor >= self.start_equity:
            self.dd_locked = True
            self.algo.Debug(
                f"ApexRM: DD floor LOCKED at ${self.dd_floor:,.0f} "
                f"(equity ${self.peak_equity:,.0f})")

    def record_eod(self, eod_equity, month_key):
        """EOD update: advance DD floor from EOD balance (Apex uses EOD)."""
        self.update_equity(eod_equity)
        if month_key not in self.monthly_pnl:
            self.monthly_pnl[month_key] = 0.0

    def add_trade_pnl(self, pnl, month_key):
        """Record trade P&L for monthly tracking."""
        if month_key not in self.monthly_pnl:
            self.monthly_pnl[month_key] = 0.0
        self.monthly_pnl[month_key] += pnl

    def get_contract_size(self):
        """Returns 0-3 contracts based on cushion from DD floor."""
        equity  = float(self.algo.Portfolio.TotalPortfolioValue)
        cushion = equity - self.dd_floor
        if cushion > 1500:
            return 3
        elif cushion > 800:
            return 2
        elif cushion > 300:
            return 1
        else:
            self.algo.Debug(
                f"ApexRM: SKIP — cushion ${cushion:.0f} <= $300 "
                f"(equity ${equity:,.0f}, floor ${self.dd_floor:,.0f})")
            return 0

    def check_monthly_lock(self, month_key):
        """Returns True if monthly profit target already hit."""
        monthly = self.monthly_pnl.get(month_key, 0.0)
        if monthly >= self.monthly_lock:
            self.algo.Debug(
                f"ApexRM: MONTHLY LOCK — {month_key} P&L "
                f"${monthly:,.0f} >= ${self.monthly_lock:,.0f}")
            return True
        return False

    def check_daily_consistency(self, todays_pnl):
        """Returns True if today's P&L >= daily_cap ($900)."""
        if todays_pnl >= self.daily_cap:
            self.algo.Debug(
                f"ApexRM: DAILY CAP HIT — today P&L "
                f"${todays_pnl:.0f} >= ${self.daily_cap:.0f}")
            return True
        return False

    def should_trade(self, todays_pnl, month_key):
        """Returns True only if ALL conditions allow trading."""
        if self.check_monthly_lock(month_key):
            return False
        if self.check_daily_consistency(todays_pnl):
            return False
        if self.get_contract_size() == 0:
            return False
        return True

    def log_status(self, month_key):
        equity  = float(self.algo.Portfolio.TotalPortfolioValue)
        cushion = equity - self.dd_floor
        monthly = self.monthly_pnl.get(month_key, 0.0)
        self.algo.Debug(
            f"ApexRM Status | Equity: ${equity:,.0f} | "
            f"Floor: ${self.dd_floor:,.0f} | Cushion: ${cushion:.0f} | "
            f"Contracts: {self.get_contract_size()} | "
            f"Month {month_key}: ${monthly:.0f}")


class ORBNQStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2025, 11, 30)
        self.SetCash(50000)
        self.SetTimeZone("America/New_York")

        # ── MNQ Continuous Futures (1-min data, consolidated to 5M) ──
        self.nq = self.AddFuture(
            "MNQ",
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

        # ── Daily 200-period EMA (built-in indicator) ────────────────
        self.ema200 = self.EMA(self.nq.Symbol, 200, Resolution.Daily)

        # ── Apex Risk Manager ────────────────────────────────────────
        self.risk             = ApexRiskManager(self, start_equity=50000)
        self.today_pnl        = 0.0         # resets each day

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

        # ── Warmup 210 calendar days (built-in EMA handles its own warmup) ──
        self.SetWarmUp(timedelta(days=210))

        self.Debug("ORB NQ Strategy initialized — MNQ 5M, $50K, Long Only, ApexRM")

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

        # ── 15:30 cutoff — no new entries after this time ────────────
        if self.Time.time() >= time(15, 30) and self.entry_bar_time is not None:
            self.Debug(f"{self.Time} ENTRY CANCELLED — past 15:30 cutoff (overnight protection)")
            self.entry_bar_time = None

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
            self.today_pnl      = 0.0      # reset daily P&L for consistency check

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
        if not self.ema200.IsReady or float(bar.Close) <= self.ema200.Current.Value:
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
        """Place a long market order (dynamic MNQ contracts via ApexRiskManager).
        Stop & target are set in OnOrderEvent once the fill arrives."""
        if self.orb_high is None or self.orb_low is None:
            return

        month_key = self.Time.strftime("%Y-%m")

        # ── Apex risk gate: monthly lock, daily cap, cushion check ───
        if not self.risk.should_trade(self.today_pnl, month_key):
            self.traded_today = True   # skip day — don't retry
            return

        contracts = self.risk.get_contract_size()
        if contracts == 0:
            self.traded_today = True
            return

        self.MarketOrder(self.symbol, contracts)
        self.traded_today  = True
        self.total_trades += 1
        self.Debug(f"ENTRY: {contracts} MNQ contracts")

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
        if self.Portfolio[self.symbol].Invested:
            self._close_position("EOD EXIT 15:45", is_win=None)

        # Record EOD equity for Apex trailing DD (EOD-based, not intraday)
        month_key = self.Time.strftime("%Y-%m")
        self.risk.record_eod(float(self.Portfolio.TotalPortfolioValue), month_key)

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

        # Update Apex risk manager
        self.today_pnl += pnl
        self.risk.add_trade_pnl(pnl, month_key)

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
        """Update peak equity, max drawdown, and Apex risk manager on every bar."""
        equity = float(self.Portfolio.TotalPortfolioValue)
        if equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity
            if dd > self.max_drawdown:
                self.max_drawdown = dd
        # Keep Apex RM in sync (intraday monitoring)
        self.risk.update_equity(equity)

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
