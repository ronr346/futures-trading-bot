# Elder Santis — Supply & Demand Strategy
# QuantConnect LEAN Python | ES Futures 5M
# Target: $1,000+/month from $50K TopStep funded account
# Strategy: One & Done — max 1 trade/day
#
# READY TO RUN — paste into QuantConnect and hit Build & Backtest

from AlgorithmImports import *
from collections import deque
import numpy as np


class ElderSupplyDemandStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2025, 12, 31)
        self.SetCash(50000)

        # ── ES Continuous Futures (1-Minute data, consolidated to 5M) ─
        self.es = self.AddFuture(
            Futures.Indices.SP500EMini,
            Resolution.Minute,
            dataNormalizationMode=DataNormalizationMode.BackwardsRatio,
            dataMappingMode=DataMappingMode.LastTradingDay,
            contractDepthOffset=0
        )
        self.es.SetFilter(0, 90)
        self.symbol = None

        # ── Strategy Parameters ──────────────────────────────────────
        self.RISK_PCT        = 0.02       # 2% risk per trade
        self.ATR_PERIOD      = 14
        self.EXPLOSIVE_MULT  = 1.5        # body > ATR * this = explosive
        self.CONSOL_MULT     = 0.5        # body < ATR * this = consolidation
        self.EMA_PERIOD      = 50
        self.ZONE_MAX        = 20         # max active zones
        self.NO_ENTRY_BEFORE = time(10, 0)    # skip first 30 min
        self.NO_ENTRY_AFTER  = time(15, 0)    # no new entries after 3 PM
        self.EOD_EXIT_TIME   = time(15, 45)   # force close at 3:45 PM

        # ── State ────────────────────────────────────────────────────
        self.traded_today    = False
        self.last_trade_day  = None
        self.current_bars    = deque(maxlen=10)
        self.demand_zones    = []
        self.supply_zones    = []
        self.atr_values      = deque(maxlen=self.ATR_PERIOD * 3)
        self.ema_values      = deque(maxlen=self.EMA_PERIOD * 2)
        self.volume_ma       = deque(maxlen=20)
        self.bar_count       = 0

        # Zone detection state machines
        self.rally_state     = 0   # 0=idle, 1=found_rally, 2=in_base
        self.drop_state      = 0   # 0=idle, 1=found_drop,  2=in_base
        self.base_high_s     = 0.0
        self.base_low_s      = float('inf')
        self.base_high_d     = 0.0
        self.base_low_d      = float('inf')

        # Trade management
        self.entry_price     = None
        self.stop_price      = None
        self.target_price    = None
        self.trade_direction = None   # "long" | "short"

        # Stats
        self.total_trades    = 0
        self.winning_trades  = 0
        self.losing_trades   = 0

        # Consolidator map: contract symbol → consolidator
        self.consolidators   = {}

        self.SetWarmup(500, Resolution.Minute)  # 500 x 1min ≈ 100 x 5min bars
        self.Debug("Elder S&D Strategy initialized — ES 5M, $50K capital")

    # ══════════════════════════════════════════════════════════════════
    #  MAIN EVENT HANDLER (1-minute data → route to consolidator)
    # ══════════════════════════════════════════════════════════════════
    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return

        # Get front-month contract
        chain = data.FutureChains.get(self.es.Symbol)
        if chain is None:
            return
        contracts = sorted(chain, key=lambda c: c.Expiry)
        if not contracts:
            return

        contract_symbol = contracts[0].Symbol

        # Register a 5-minute consolidator for this contract (once)
        if contract_symbol not in self.consolidators:
            # Remove old consolidator if contract rolled
            for old_sym, old_con in list(self.consolidators.items()):
                self.SubscriptionManager.RemoveConsolidator(old_sym, old_con)
            self.consolidators.clear()

            consolidator = TradeBarConsolidator(timedelta(minutes=5))
            consolidator.DataConsolidated += self.OnFiveMinuteBar
            self.SubscriptionManager.AddConsolidator(contract_symbol, consolidator)
            self.consolidators[contract_symbol] = consolidator
            self.symbol = contract_symbol

        # Also check exit on every 1-minute bar for faster stop/target hits
        if self.symbol and self.Portfolio[self.symbol].Invested:
            if data.Bars.ContainsKey(self.symbol):
                self._check_exit_fast(data.Bars[self.symbol])

    # ══════════════════════════════════════════════════════════════════
    #  5-MINUTE BAR HANDLER (all strategy logic runs here)
    # ══════════════════════════════════════════════════════════════════
    def OnFiveMinuteBar(self, sender, bar):
        """Called every 5 minutes with a consolidated TradeBar."""
        if self.IsWarmingUp:
            return
        if self.symbol is None:
            return

        # ── Daily reset ──────────────────────────────────────────────
        today = self.Time.date()
        if self.last_trade_day != today:
            self.last_trade_day = today
            self.traded_today   = False

        # ── Manage open position ─────────────────────────────────────
        if self.Portfolio[self.symbol].Invested:
            self._check_exit(bar)
            return

        # ── Skip if already traded today or outside session ──────────
        if self.traded_today:
            return

        now = self.Time.time()
        if now < self.NO_ENTRY_BEFORE or now > self.NO_ENTRY_AFTER:
            return

        # ── Update indicators ────────────────────────────────────────
        self._update_indicators(bar)
        self.bar_count += 1

        if len(self.atr_values) < self.ATR_PERIOD:
            return

        # ── Zone detection ───────────────────────────────────────────
        self._detect_zones(bar)
        self._invalidate_zones(bar)

        # ── Entry signal ─────────────────────────────────────────────
        if len(self.ema_values) < self.EMA_PERIOD:
            return

        self._check_entry(bar)

    # ══════════════════════════════════════════════════════════════════
    #  INDICATORS
    # ══════════════════════════════════════════════════════════════════
    def _update_indicators(self, bar):
        """Update ATR (Wilder's), EMA, and volume MA on 5M bars."""
        self.current_bars.append(bar)
        self.volume_ma.append(float(bar.Volume))

        # ATR (Wilder's smoothing)
        if len(self.current_bars) >= 2:
            prev = self.current_bars[-2]
            tr = max(
                float(bar.High - bar.Low),
                abs(float(bar.High - prev.Close)),
                abs(float(bar.Low  - prev.Close))
            )
            if len(self.atr_values) == 0:
                self.atr_values.append(tr)
            else:
                smoothed = (self.atr_values[-1] * (self.ATR_PERIOD - 1) + tr) / self.ATR_PERIOD
                self.atr_values.append(smoothed)

        # EMA
        close = float(bar.Close)
        if len(self.ema_values) == 0:
            self.ema_values.append(close)
        else:
            k = 2.0 / (self.EMA_PERIOD + 1)
            ema = close * k + self.ema_values[-1] * (1 - k)
            self.ema_values.append(ema)

    def _atr(self):
        return self.atr_values[-1] if self.atr_values else 1.0

    def _ema(self):
        return self.ema_values[-1] if self.ema_values else 0.0

    def _is_explosive(self, bar):
        return abs(float(bar.Close - bar.Open)) > self._atr() * self.EXPLOSIVE_MULT

    def _is_consolidation(self, bar):
        return abs(float(bar.Close - bar.Open)) < self._atr() * self.CONSOL_MULT

    # ══════════════════════════════════════════════════════════════════
    #  ZONE DETECTION (State Machine)
    # ══════════════════════════════════════════════════════════════════
    def _detect_zones(self, bar):
        """
        Detect Supply (Rally-Base-Drop) and Demand (Drop-Base-Rally) zones.
        Each pattern is tracked by its own state machine.
        """
        # ── DEMAND zone: Drop → Base → Rally ─────────────────────────
        if self.drop_state == 0:
            if self._is_explosive(bar) and bar.Close < bar.Open:
                self.drop_state  = 1
                self.base_high_d = 0.0
                self.base_low_d  = float('inf')

        elif self.drop_state == 1:
            if self._is_consolidation(bar):
                self.drop_state  = 2
                self.base_high_d = max(self.base_high_d, float(bar.High))
                self.base_low_d  = min(self.base_low_d,  float(bar.Low))
            elif self._is_explosive(bar):
                self.drop_state = 0

        elif self.drop_state == 2:
            if self._is_consolidation(bar):
                self.base_high_d = max(self.base_high_d, float(bar.High))
                self.base_low_d  = min(self.base_low_d,  float(bar.Low))
            elif self._is_explosive(bar) and bar.Close > bar.Open:
                if len(self.demand_zones) < self.ZONE_MAX:
                    zone = {
                        "top":     self.base_high_d,
                        "bottom":  self.base_low_d,
                        "bar_idx": self.bar_count,
                    }
                    self.demand_zones.append(zone)
                    self.Debug(f"DEMAND zone: {zone['bottom']:.2f} – {zone['top']:.2f}")
                self.drop_state = 0
            else:
                self.drop_state = 0

        # ── SUPPLY zone: Rally → Base → Drop ─────────────────────────
        if self.rally_state == 0:
            if self._is_explosive(bar) and bar.Close > bar.Open:
                self.rally_state = 1
                self.base_high_s = 0.0
                self.base_low_s  = float('inf')

        elif self.rally_state == 1:
            if self._is_consolidation(bar):
                self.rally_state = 2
                self.base_high_s = max(self.base_high_s, float(bar.High))
                self.base_low_s  = min(self.base_low_s,  float(bar.Low))
            elif self._is_explosive(bar):
                self.rally_state = 0

        elif self.rally_state == 2:
            if self._is_consolidation(bar):
                self.base_high_s = max(self.base_high_s, float(bar.High))
                self.base_low_s  = min(self.base_low_s,  float(bar.Low))
            elif self._is_explosive(bar) and bar.Close < bar.Open:
                if len(self.supply_zones) < self.ZONE_MAX:
                    zone = {
                        "top":     self.base_high_s,
                        "bottom":  self.base_low_s,
                        "bar_idx": self.bar_count,
                    }
                    self.supply_zones.append(zone)
                    self.Debug(f"SUPPLY zone: {zone['bottom']:.2f} – {zone['top']:.2f}")
                self.rally_state = 0
            else:
                self.rally_state = 0

    def _invalidate_zones(self, bar):
        """Remove zones where price closed through them (Elder's rule)."""
        atr_buffer = self._atr() * 0.1
        close = float(bar.Close)

        self.demand_zones = [
            z for z in self.demand_zones
            if not (close < z["bottom"] - atr_buffer)
        ]
        self.supply_zones = [
            z for z in self.supply_zones
            if not (close > z["top"] + atr_buffer)
        ]

    # ══════════════════════════════════════════════════════════════════
    #  ENTRY LOGIC — Elder's A+ Setup Scoring
    # ══════════════════════════════════════════════════════════════════
    def _check_entry(self, bar):
        """Evaluate entry conditions — score-based A+ setup."""
        ema    = self._ema()
        atr    = self._atr()
        close  = float(bar.Close)
        open_  = float(bar.Open)
        high   = float(bar.High)
        low    = float(bar.Low)
        vol    = float(bar.Volume)
        vol_ma = np.mean(list(self.volume_ma)) if self.volume_ma else vol

        # ── LONG: price touching demand zone + bullish conditions ────
        matching_demand = next(
            (z for z in self.demand_zones if z["bottom"] <= low <= z["top"]),
            None
        )

        if matching_demand:
            score = 0
            if close > ema:                                             score += 1  # 1. Trend
            score += 1                                                              # 2. In zone
            if (close > open_ and len(self.current_bars) >= 2
                    and float(self.current_bars[-2].Low) < low):        score += 1  # 3. Structure
            if vol < vol_ma * 0.85:                                     score += 1  # 4. Dead volume

            if score >= 3:
                stop   = matching_demand["bottom"] - atr * 0.25
                risk   = close - stop
                if risk > 0:
                    qty    = self._position_size(close, stop)
                    target = close + risk * 2.0
                    self._enter_long(close, stop, target, qty, score)
                    return

        # ── SHORT: price touching supply zone + bearish conditions ───
        if self.Portfolio[self.symbol].Invested:
            return

        matching_supply = next(
            (z for z in self.supply_zones if z["bottom"] <= high <= z["top"]),
            None
        )

        if matching_supply:
            score = 0
            if close < ema:                                             score += 1  # 1. Trend
            score += 1                                                              # 2. In zone
            if (close < open_ and len(self.current_bars) >= 2
                    and float(self.current_bars[-2].High) > high):      score += 1  # 3. Structure
            if vol < vol_ma * 0.85:                                     score += 1  # 4. Dead volume

            if score >= 3:
                stop   = matching_supply["top"] + atr * 0.25
                risk   = stop - close
                if risk > 0:
                    qty    = self._position_size(close, stop)
                    target = close - risk * 2.0
                    self._enter_short(close, stop, target, qty, score)

    # ══════════════════════════════════════════════════════════════════
    #  POSITION SIZING
    # ══════════════════════════════════════════════════════════════════
    def _position_size(self, entry, stop):
        """2% risk position sizing → number of ES contracts."""
        equity    = float(self.Portfolio.TotalPortfolioValue)
        risk_usd  = equity * self.RISK_PCT
        stop_dist = abs(entry - stop)
        if stop_dist <= 0:
            return 1
        point_value = 50.0   # ES = $50 per index point
        contracts   = int(risk_usd / (stop_dist * point_value))
        return max(1, min(contracts, 10))

    # ══════════════════════════════════════════════════════════════════
    #  ORDER EXECUTION
    # ══════════════════════════════════════════════════════════════════
    def _enter_long(self, entry, stop, target, qty, score):
        self.MarketOrder(self.symbol, qty)
        self.entry_price     = entry
        self.stop_price      = stop
        self.target_price    = target
        self.trade_direction = "long"
        self.traded_today    = True
        self.total_trades   += 1
        rr = (target - entry) / (entry - stop) if (entry - stop) > 0 else 0
        self.Debug(
            f"LONG ENTRY | Price:{entry:.2f} | Stop:{stop:.2f} | "
            f"Target:{target:.2f} | Qty:{qty} | Score:{score}/4 | R:R {rr:.1f}"
        )

    def _enter_short(self, entry, stop, target, qty, score):
        self.MarketOrder(self.symbol, -qty)
        self.entry_price     = entry
        self.stop_price      = stop
        self.target_price    = target
        self.trade_direction = "short"
        self.traded_today    = True
        self.total_trades   += 1
        rr = (entry - target) / (stop - entry) if (stop - entry) > 0 else 0
        self.Debug(
            f"SHORT ENTRY | Price:{entry:.2f} | Stop:{stop:.2f} | "
            f"Target:{target:.2f} | Qty:{qty} | Score:{score}/4 | R:R {rr:.1f}"
        )

    # ══════════════════════════════════════════════════════════════════
    #  EXIT LOGIC
    # ══════════════════════════════════════════════════════════════════
    def _check_exit(self, bar):
        """Check stop loss, take profit, and EOD exit on 5M bars."""
        if not self.Portfolio[self.symbol].Invested:
            return

        high  = float(bar.High)
        low   = float(bar.Low)
        close = float(bar.Close)
        self._evaluate_exit(high, low, close)

    def _check_exit_fast(self, bar):
        """Check stop/target on every 1-minute bar for faster reaction."""
        if not self.Portfolio[self.symbol].Invested:
            return

        high  = float(bar.High)
        low   = float(bar.Low)
        close = float(bar.Close)
        self._evaluate_exit(high, low, close)

    def _evaluate_exit(self, high, low, close):
        """Shared exit logic for both 1M and 5M checks."""
        if not self.Portfolio[self.symbol].Invested:
            return

        hit_stop   = False
        hit_target = False

        if self.trade_direction == "long":
            hit_stop   = low  <= self.stop_price
            hit_target = high >= self.target_price
        else:
            hit_stop   = high >= self.stop_price
            hit_target = low  <= self.target_price

        eod = self.Time.time() >= self.EOD_EXIT_TIME

        if hit_target or hit_stop or eod:
            pnl = float(self.Portfolio[self.symbol].UnrealizedProfit)

            if hit_target:
                reason = "TARGET HIT"
                self.winning_trades += 1
            elif hit_stop:
                reason = "STOP HIT"
                self.losing_trades += 1
            else:
                reason = "EOD EXIT"
                if pnl >= 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

            self.Liquidate(self.symbol)
            self.Debug(f"{reason} | PnL: ${pnl:,.0f} | Close: {close:.2f}")

    # ══════════════════════════════════════════════════════════════════
    #  EVENTS
    # ══════════════════════════════════════════════════════════════════
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(
                f"Order filled | {orderEvent.Direction} | "
                f"Qty:{orderEvent.FillQuantity} | "
                f"Price:{orderEvent.FillPrice:.2f}"
            )

    def OnEndOfAlgorithm(self):
        equity = float(self.Portfolio.TotalPortfolioValue)
        net    = float(self.Portfolio.TotalNetProfit)
        wr     = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        self.Log("=" * 60)
        self.Log("ELDER S&D STRATEGY — FINAL RESULTS")
        self.Log("=" * 60)
        self.Log(f"Total Portfolio Value:  ${equity:,.0f}")
        self.Log(f"Total Net Profit:      ${net:,.0f}")
        self.Log(f"Total Return:          {net / 50000 * 100:.1f}%")
        self.Log(f"Total Trades:          {self.total_trades}")
        self.Log(f"Winning Trades:        {self.winning_trades}")
        self.Log(f"Losing Trades:         {self.losing_trades}")
        self.Log(f"Win Rate:              {wr:.1f}%")
        self.Log("=" * 60)
