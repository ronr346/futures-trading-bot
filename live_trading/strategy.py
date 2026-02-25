"""
Elder Santis Supply & Demand Strategy — Live Trading Port.

Ported from quantconnect/elder_sd_strategy.py.
Pure logic: receives bar data, returns trade signals.
No broker dependencies — the bot orchestrator handles execution.

Zone detection state machine:
  Demand = Drop (explosive down) → Base (consolidation) → Rally (explosive up)
  Supply = Rally (explosive up) → Base (consolidation) → Drop (explosive down)

Entry scoring (need 3 of 4):
  1. Trend — price vs EMA-50
  2. Zone — price touching a valid S/D zone
  3. Structure shift — bullish/bearish candle confirmation
  4. Dead volume — low volume on the pullback into the zone
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Optional

from live_trading.config import StrategyConfig, RiskConfig

log = logging.getLogger(__name__)


@dataclass
class Bar:
    """OHLCV bar aggregated from tick data."""
    timestamp: float  # epoch seconds
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    """Trade signal emitted by the strategy."""
    direction: str    # "long" or "short"
    entry: float
    stop: float
    target: float
    contracts: int
    score: int        # out of 4
    zone_top: float
    zone_bottom: float


class ElderSupplyDemandStrategy:
    """
    Self-contained S&D strategy.

    Feed it bars via on_bar(). It returns a Signal when entry conditions are met.
    Call reset_daily() at the start of each trading day.
    """

    def __init__(self, strategy_cfg: StrategyConfig, risk_cfg: RiskConfig):
        self.cfg = strategy_cfg
        self.risk = risk_cfg

        # Indicator state
        self.current_bars: deque[Bar] = deque(maxlen=10)
        self.atr_values: deque[float] = deque(maxlen=self.cfg.atr_period * 3)
        self.ema_values: deque[float] = deque(maxlen=self.cfg.ema_period * 2)
        self.volume_ma: deque[float] = deque(maxlen=20)
        self.bar_count: int = 0

        # Zones
        self.demand_zones: list[dict] = []
        self.supply_zones: list[dict] = []

        # Pattern detection — demand (Drop-Base-Rally)
        self.drop_state: int = 0     # 0=idle, 1=found_drop, 2=in_base
        self.drop_start_bar: int = 0
        self.base_high_d: float = 0
        self.base_low_d: float = float("inf")

        # Pattern detection — supply (Rally-Base-Drop)
        self.rally_state: int = 0
        self.rally_start_bar: int = 0
        self.base_high_s: float = 0
        self.base_low_s: float = float("inf")

        self._warmed_up = False

    # ── Public interface ─────────────────────────────────────────────
    def on_bar(self, bar: Bar) -> Optional[Signal]:
        """
        Process a new 5-minute bar.
        Returns a Signal if entry conditions are met, else None.
        """
        self._update_indicators(bar)
        self.bar_count += 1

        if len(self.atr_values) < self.cfg.atr_period:
            return None

        self._detect_zones(bar)
        self._invalidate_zones(bar)

        if len(self.ema_values) < self.cfg.ema_period:
            return None

        self._warmed_up = True
        return self._check_entry(bar)

    @property
    def is_warmed_up(self) -> bool:
        return self._warmed_up

    def reset_daily(self):
        """Reset per-day state. Keep zones and indicators across days."""
        log.info(
            "Daily reset | demand_zones=%d supply_zones=%d",
            len(self.demand_zones), len(self.supply_zones),
        )

    # ── Indicators ───────────────────────────────────────────────────
    def _update_indicators(self, bar: Bar):
        self.current_bars.append(bar)
        self.volume_ma.append(bar.volume)

        # ATR (Wilder's smoothing)
        if len(self.current_bars) >= 2:
            prev = self.current_bars[-2]
            tr = max(
                bar.high - bar.low,
                abs(bar.high - prev.close),
                abs(bar.low - prev.close),
            )
            if len(self.atr_values) == 0:
                self.atr_values.append(tr)
            else:
                atr = (
                    self.atr_values[-1] * (self.cfg.atr_period - 1) + tr
                ) / self.cfg.atr_period
                self.atr_values.append(atr)

        # EMA
        if len(self.ema_values) == 0:
            self.ema_values.append(bar.close)
        else:
            k = 2 / (self.cfg.ema_period + 1)
            ema = bar.close * k + self.ema_values[-1] * (1 - k)
            self.ema_values.append(ema)

    def _atr(self) -> float:
        return self.atr_values[-1] if self.atr_values else 1.0

    def _ema(self) -> float:
        return self.ema_values[-1] if self.ema_values else 0.0

    def _is_explosive(self, bar: Bar) -> bool:
        return abs(bar.close - bar.open) > self._atr() * self.cfg.explosive_mult

    def _is_consolidation(self, bar: Bar) -> bool:
        return abs(bar.close - bar.open) < self._atr() * self.cfg.consol_mult

    # ── Zone Detection ───────────────────────────────────────────────
    def _detect_zones(self, bar: Bar):
        """
        State machine for S&D zone detection.
        Demand = Drop → Base → Rally
        Supply = Rally → Base → Drop
        """
        # ── DEMAND: Drop → Base → Rally ──────────────────────────────
        if self.drop_state == 0:
            if self._is_explosive(bar) and bar.close < bar.open:
                self.drop_state = 1
                self.drop_start_bar = self.bar_count
                self.base_high_d = 0
                self.base_low_d = float("inf")

        elif self.drop_state == 1:
            if self._is_consolidation(bar):
                self.drop_state = 2
                self.base_high_d = max(self.base_high_d, bar.high)
                self.base_low_d = min(self.base_low_d, bar.low)
            elif self._is_explosive(bar):
                self.drop_state = 0

        elif self.drop_state == 2:
            if self._is_consolidation(bar):
                self.base_high_d = max(self.base_high_d, bar.high)
                self.base_low_d = min(self.base_low_d, bar.low)
            elif self._is_explosive(bar) and bar.close > bar.open:
                if len(self.demand_zones) < self.cfg.zone_max:
                    zone = {
                        "top": self.base_high_d,
                        "bottom": self.base_low_d,
                        "valid": True,
                        "bar_idx": self.bar_count,
                        "tests": 0,
                    }
                    self.demand_zones.append(zone)
                    log.info(
                        "DEMAND zone detected: %.2f - %.2f",
                        zone["bottom"], zone["top"],
                    )
                self.drop_state = 0
            else:
                self.drop_state = 0

        # ── SUPPLY: Rally → Base → Drop ──────────────────────────────
        if self.rally_state == 0:
            if self._is_explosive(bar) and bar.close > bar.open:
                self.rally_state = 1
                self.rally_start_bar = self.bar_count
                self.base_high_s = 0
                self.base_low_s = float("inf")

        elif self.rally_state == 1:
            if self._is_consolidation(bar):
                self.rally_state = 2
                self.base_high_s = max(self.base_high_s, bar.high)
                self.base_low_s = min(self.base_low_s, bar.low)
            elif self._is_explosive(bar):
                self.rally_state = 0

        elif self.rally_state == 2:
            if self._is_consolidation(bar):
                self.base_high_s = max(self.base_high_s, bar.high)
                self.base_low_s = min(self.base_low_s, bar.low)
            elif self._is_explosive(bar) and bar.close < bar.open:
                if len(self.supply_zones) < self.cfg.zone_max:
                    zone = {
                        "top": self.base_high_s,
                        "bottom": self.base_low_s,
                        "valid": True,
                        "bar_idx": self.bar_count,
                        "tests": 0,
                    }
                    self.supply_zones.append(zone)
                    log.info(
                        "SUPPLY zone detected: %.2f - %.2f",
                        zone["bottom"], zone["top"],
                    )
                self.rally_state = 0
            else:
                self.rally_state = 0

    def _invalidate_zones(self, bar: Bar):
        """Remove zones that price has closed through."""
        atr = self._atr()
        thresh = atr * self.cfg.zone_invalidation_mult
        self.demand_zones = [
            z for z in self.demand_zones
            if not (bar.close < z["bottom"] - thresh)
        ]
        self.supply_zones = [
            z for z in self.supply_zones
            if not (bar.close > z["top"] + thresh)
        ]

    # ── Entry Scoring ────────────────────────────────────────────────
    def _check_entry(self, bar: Bar) -> Optional[Signal]:
        ema = self._ema()
        atr = self._atr()
        vol_ma = (
            sum(self.volume_ma) / len(self.volume_ma)
            if self.volume_ma
            else bar.volume
        )

        # ── LONG: price in demand zone ───────────────────────────────
        demand_zone = next(
            (z for z in self.demand_zones
             if z["valid"] and z["bottom"] <= bar.low <= z["top"]),
            None,
        )
        if demand_zone:
            score = 0
            if bar.close > ema:                                          score += 1  # 1. Trend
            score += 1                                                                # 2. Zone
            if (bar.close > bar.open
                    and len(self.current_bars) >= 2
                    and self.current_bars[-2].low < bar.low):            score += 1  # 3. Structure
            if bar.volume < vol_ma * self.cfg.volume_dead_mult:          score += 1  # 4. Dead vol

            if score >= self.cfg.min_score:
                stop = demand_zone["bottom"] - atr * self.cfg.stop_buffer_mult
                risk = bar.close - stop
                if risk > 0:
                    target = bar.close + risk * self.cfg.rr_ratio
                    qty = self._position_size(bar.close, stop)
                    return Signal(
                        direction="long",
                        entry=bar.close,
                        stop=stop,
                        target=target,
                        contracts=qty,
                        score=score,
                        zone_top=demand_zone["top"],
                        zone_bottom=demand_zone["bottom"],
                    )

        # ── SHORT: price in supply zone ──────────────────────────────
        supply_zone = next(
            (z for z in self.supply_zones
             if z["valid"] and z["bottom"] <= bar.high <= z["top"]),
            None,
        )
        if supply_zone:
            score = 0
            if bar.close < ema:                                          score += 1
            score += 1
            if (bar.close < bar.open
                    and len(self.current_bars) >= 2
                    and self.current_bars[-2].high > bar.high):          score += 1
            if bar.volume < vol_ma * self.cfg.volume_dead_mult:          score += 1

            if score >= self.cfg.min_score:
                stop = supply_zone["top"] + atr * self.cfg.stop_buffer_mult
                risk = stop - bar.close
                if risk > 0:
                    target = bar.close - risk * self.cfg.rr_ratio
                    qty = self._position_size(bar.close, stop)
                    return Signal(
                        direction="short",
                        entry=bar.close,
                        stop=stop,
                        target=target,
                        contracts=qty,
                        score=score,
                        zone_top=supply_zone["top"],
                        zone_bottom=supply_zone["bottom"],
                    )

        return None

    # ── Position Sizing ──────────────────────────────────────────────
    def _position_size(self, entry: float, stop: float) -> int:
        """2% risk position sizing → number of contracts."""
        risk_usd = self.risk.account_equity * self.risk.risk_pct
        stop_dist = abs(entry - stop)
        if stop_dist <= 0:
            return self.risk.min_contracts
        contracts = int(risk_usd / (stop_dist * self.risk.es_point_value))
        return max(self.risk.min_contracts, min(contracts, self.risk.max_contracts))
