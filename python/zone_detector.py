"""
Zone Detection Module for Elder Santis Supply & Demand Strategy

This module implements Elder's specific zone detection rules:
- Rally-Base-Drop (RBD) → Supply Zone
- Drop-Base-Rally (DBR) → Demand Zone
- Multi-timeframe zone stacking (4H -> 2H -> 1H -> 30M)
- Zone strength scoring and invalidation tracking

Based on comprehensive research of Elder Santis's methodology from his YouTube channel
and trading education materials.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class ZoneType(Enum):
    SUPPLY = "supply"
    DEMAND = "demand"

class ZoneStrength(Enum):
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4

@dataclass
class SupplyDemandZone:
    """Represents a Supply or Demand zone"""
    zone_type: ZoneType
    top: float
    bottom: float
    timeframe: str
    start_index: int
    end_index: int
    strength: ZoneStrength
    valid: bool = True
    test_count: int = 0
    volume_poc_confluence: bool = False
    creation_timestamp: pd.Timestamp = None
    last_test_timestamp: pd.Timestamp = None

    @property
    def mid_point(self) -> float:
        """Return the midpoint of the zone"""
        return (self.top + self.bottom) / 2

    @property
    def height(self) -> float:
        """Return the height of the zone"""
        return self.top - self.bottom

    def is_price_in_zone(self, price: float) -> bool:
        """Check if a price is within the zone"""
        return self.bottom <= price <= self.top

    def test_zone(self, timestamp: pd.Timestamp) -> None:
        """Record a test of this zone"""
        self.test_count += 1
        self.last_test_timestamp = timestamp

    def invalidate(self) -> None:
        """Invalidate this zone (30M close through zone)"""
        self.valid = False

class ZoneDetector:
    """
    Detects Supply & Demand zones using Elder Santis's methodology

    Key Rules:
    - Supply zone: consolidation before explosive move DOWN (Rally-Base-Drop)
    - Demand zone: consolidation before explosive move UP (Drop-Base-Rally)
    - Zone boundaries:
      - Demand: bottom wick to top body of consolidation
      - Supply: bottom body to top wick of consolidation
    - Multi-timeframe stacking for strength
    """

    def __init__(
        self,
        explosive_threshold: float = 0.7,  # ATR multiplier for explosive moves
        consolidation_threshold: float = 0.8,  # ATR multiplier for consolidation
        min_base_candles: int = 1,  # Minimum candles in base
        max_base_candles: int = 5,  # Maximum candles in base
        atr_period: int = 14
    ):
        self.explosive_threshold = explosive_threshold
        self.consolidation_threshold = consolidation_threshold
        self.min_base_candles = min_base_candles
        self.max_base_candles = max_base_candles
        self.atr_period = atr_period

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close_prev = np.abs(df['High'] - df['Close'].shift(1))
        low_close_prev = np.abs(df['Low'] - df['Close'].shift(1))

        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=self.atr_period).mean()

        return atr

    def is_explosive_move(self, df: pd.DataFrame, index: int, atr: pd.Series) -> Tuple[bool, str]:
        """
        Check if candle at index represents an explosive move
        Returns (is_explosive, direction)
        """
        if index >= len(df) or index < 0:
            return False, None

        candle_range = df.iloc[index]['High'] - df.iloc[index]['Low']
        candle_body = abs(df.iloc[index]['Close'] - df.iloc[index]['Open'])

        if pd.isna(atr.iloc[index]) or atr.iloc[index] == 0:
            return False, None

        is_explosive = candle_range > atr.iloc[index] * self.explosive_threshold

        if not is_explosive:
            return False, None

        # Determine direction based on candle body
        if df.iloc[index]['Close'] > df.iloc[index]['Open']:
            return True, "up"
        else:
            return True, "down"

    def is_consolidation_candle(self, df: pd.DataFrame, index: int, atr: pd.Series) -> bool:
        """Check if candle at index is a consolidation candle"""
        if index >= len(df) or index < 0:
            return False

        candle_range = df.iloc[index]['High'] - df.iloc[index]['Low']

        if pd.isna(atr.iloc[index]) or atr.iloc[index] == 0:
            return False

        return candle_range < atr.iloc[index] * self.consolidation_threshold

    def find_base_candles(
        self,
        df: pd.DataFrame,
        start_idx: int,
        end_idx: int,
        atr: pd.Series
    ) -> List[int]:
        """
        Find consolidation (base) candles between start and end indices
        """
        base_candles = []

        for i in range(start_idx, end_idx + 1):
            if self.is_consolidation_candle(df, i, atr):
                base_candles.append(i)

        return base_candles

    def create_supply_zone(
        self,
        df: pd.DataFrame,
        base_indices: List[int],
        timeframe: str
    ) -> SupplyDemandZone:
        """
        Create supply zone using Elder's rules:
        - Bottom of zone = Bottom BODY of consolidation candles
        - Top of zone = Top WICK of consolidation candles
        """
        if not base_indices:
            return None

        base_candles = df.iloc[base_indices]

        # Supply zone boundaries per Elder's rules
        zone_top = base_candles['High'].max()  # Top wick
        zone_bottom = base_candles[['Open', 'Close']].max().max()  # Top body

        # Ensure zone makes sense (top > bottom)
        if zone_top <= zone_bottom:
            zone_bottom = base_candles[['Open', 'Close']].min().min()  # Use bottom body if needed

        # Determine strength based on timeframe
        strength_map = {
            '4H': ZoneStrength.VERY_STRONG,
            '2H': ZoneStrength.STRONG,
            '1H': ZoneStrength.MEDIUM,
            '30M': ZoneStrength.WEAK
        }

        strength = strength_map.get(timeframe, ZoneStrength.WEAK)

        return SupplyDemandZone(
            zone_type=ZoneType.SUPPLY,
            top=zone_top,
            bottom=zone_bottom,
            timeframe=timeframe,
            start_index=base_indices[0],
            end_index=base_indices[-1],
            strength=strength,
            creation_timestamp=df.index[base_indices[-1]] if hasattr(df.index[base_indices[-1]], 'to_pydatetime') else None
        )

    def create_demand_zone(
        self,
        df: pd.DataFrame,
        base_indices: List[int],
        timeframe: str
    ) -> SupplyDemandZone:
        """
        Create demand zone using Elder's rules:
        - Bottom of zone = Bottom WICK of consolidation candles
        - Top of zone = Top BODY of consolidation candles
        """
        if not base_indices:
            return None

        base_candles = df.iloc[base_indices]

        # Demand zone boundaries per Elder's rules
        zone_bottom = base_candles['Low'].min()  # Bottom wick
        zone_top = base_candles[['Open', 'Close']].min().min()  # Bottom body

        # Ensure zone makes sense (top > bottom)
        if zone_top <= zone_bottom:
            zone_top = base_candles[['Open', 'Close']].max().max()  # Use top body if needed

        # Determine strength based on timeframe
        strength_map = {
            '4H': ZoneStrength.VERY_STRONG,
            '2H': ZoneStrength.STRONG,
            '1H': ZoneStrength.MEDIUM,
            '30M': ZoneStrength.WEAK
        }

        strength = strength_map.get(timeframe, ZoneStrength.WEAK)

        return SupplyDemandZone(
            zone_type=ZoneType.DEMAND,
            top=zone_top,
            bottom=zone_bottom,
            timeframe=timeframe,
            start_index=base_indices[0],
            end_index=base_indices[-1],
            strength=strength,
            creation_timestamp=df.index[base_indices[-1]] if hasattr(df.index[base_indices[-1]], 'to_pydatetime') else None
        )

    def detect_zones(
        self,
        df: pd.DataFrame,
        timeframe: str = '30M',
        lookback: int = 100
    ) -> List[SupplyDemandZone]:
        """
        Main zone detection function

        Looks for:
        1. Rally-Base-Drop (RBD) → Supply Zone
        2. Drop-Base-Rally (DBR) → Demand Zone

        Following Elder's methodology exactly
        """
        if len(df) < self.atr_period + 10:
            return []

        zones = []
        atr = self.calculate_atr(df)

        # Only look at recent data (lookback period)
        start_idx = max(0, len(df) - lookback)

        i = start_idx + self.atr_period
        while i < len(df) - 2:  # Need at least 2 candles ahead

            # Check if current candle is explosive
            is_exp, exp_dir = self.is_explosive_move(df, i, atr)

            if is_exp:
                # Pattern 1: Rally-Base-Drop (Supply Zone)
                # Current candle is explosive UP → look for base → then explosive DOWN
                if exp_dir == "up":
                    base_start = i + 1
                    base_end = -1

                    for j in range(i + 1, min(i + 1 + self.max_base_candles, len(df))):
                        if self.is_consolidation_candle(df, j, atr):
                            base_end = j
                        else:
                            break

                    if base_end >= base_start and (base_end - base_start + 1) >= self.min_base_candles:
                        # Look for explosive move down after base
                        next_idx = base_end + 1
                        if next_idx < len(df):
                            exp_down, down_dir = self.is_explosive_move(df, next_idx, atr)
                            if exp_down and down_dir == "down":
                                base_indices = list(range(base_start, base_end + 1))
                                supply_zone = self.create_supply_zone(df, base_indices, timeframe)
                                if supply_zone and supply_zone.height > 0:
                                    zones.append(supply_zone)
                                    i = next_idx + 1
                                    continue

                # Pattern 2: Drop-Base-Rally (Demand Zone)  
                # Current candle is explosive DOWN → look for base → then explosive UP
                if exp_dir == "down":
                    base_start = i + 1
                    base_end = -1

                    for j in range(i + 1, min(i + 1 + self.max_base_candles, len(df))):
                        if self.is_consolidation_candle(df, j, atr):
                            base_end = j
                        else:
                            break

                    if base_end >= base_start and (base_end - base_start + 1) >= self.min_base_candles:
                        next_idx = base_end + 1
                        if next_idx < len(df):
                            exp_up, up_dir = self.is_explosive_move(df, next_idx, atr)

                            if exp_up and up_dir == "up":
                                # Found complete DBR pattern - create demand zone
                                base_indices = list(range(base_start, base_end + 1))
                                demand_zone = self.create_demand_zone(df, base_indices, timeframe)

                                if demand_zone and demand_zone.height > 0:
                                    zones.append(demand_zone)
                                    i = next_idx + 1
                                    continue

            i += 1

        # Remove overlapping zones (keep strongest)
        zones = self._remove_overlapping_zones(zones)

        return zones

    def _remove_overlapping_zones(self, zones: List[SupplyDemandZone]) -> List[SupplyDemandZone]:
        """Remove overlapping zones, keeping the strongest ones"""
        if not zones:
            return zones

        # Sort by strength (strongest first)
        strength_order = {
            ZoneStrength.VERY_STRONG: 4,
            ZoneStrength.STRONG: 3,
            ZoneStrength.MEDIUM: 2,
            ZoneStrength.WEAK: 1
        }

        zones.sort(key=lambda z: strength_order[z.strength], reverse=True)

        filtered_zones = []

        for zone in zones:
            overlaps = False
            for existing_zone in filtered_zones:
                # Check if zones overlap
                if (zone.bottom <= existing_zone.top and zone.top >= existing_zone.bottom):
                    overlaps = True
                    break

            if not overlaps:
                filtered_zones.append(zone)

        return filtered_zones

    def invalidate_zones(
        self,
        zones: List[SupplyDemandZone],
        df: pd.DataFrame,
        current_index: int
    ) -> List[SupplyDemandZone]:
        """
        Invalidate zones based on Elder's 30M close through zone rule
        """
        if current_index < 1:
            return zones

        current_close = df.iloc[current_index]['Close']

        for zone in zones:
            if zone.valid:
                # Check if 30M candle closed through zone
                if zone.zone_type == ZoneType.SUPPLY and current_close > zone.top:
                    zone.invalidate()
                elif zone.zone_type == ZoneType.DEMAND and current_close < zone.bottom:
                    zone.invalidate()

        # Return only valid zones
        return [zone for zone in zones if zone.valid]

    def get_zones_near_price(
        self,
        zones: List[SupplyDemandZone],
        price: float,
        tolerance: float = 0.002  # 0.2% tolerance
    ) -> List[SupplyDemandZone]:
        """Get zones that are near the current price"""
        nearby_zones = []

        for zone in zones:
            if zone.valid:
                # Check if price is within zone or nearby
                price_in_zone = zone.is_price_in_zone(price)
                price_near_zone = (
                    abs(price - zone.top) <= zone.top * tolerance or
                    abs(price - zone.bottom) <= zone.bottom * tolerance
                )

                if price_in_zone or price_near_zone:
                    nearby_zones.append(zone)

        return nearby_zones

    def detect_multi_timeframe_zones(
        self,
        data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[SupplyDemandZone]]:
        """
        Detect zones across multiple timeframes

        Args:
            data_dict: Dictionary with timeframe as key, DataFrame as value
                      e.g., {'4H': df_4h, '2H': df_2h, '1H': df_1h, '30M': df_30m}

        Returns:
            Dictionary with zones for each timeframe
        """
        all_zones = {}

        # Process timeframes in order of strength (highest first)
        timeframe_order = ['4H', '2H', '1H', '30M', '15M', '5M']

        for tf in timeframe_order:
            if tf in data_dict:
                zones = self.detect_zones(data_dict[tf], tf)
                all_zones[tf] = zones

        return all_zones

    def score_zone_confluence(
        self,
        zone: SupplyDemandZone,
        all_zones: Dict[str, List[SupplyDemandZone]],
        volume_poc_levels: Optional[List[float]] = None
    ) -> float:
        """
        Score zone based on confluence factors:
        - Multi-timeframe alignment
        - Volume Profile POC confluence
        - Zone freshness (test count)
        """
        score = 0.0

        # Base score from timeframe strength
        strength_scores = {
            ZoneStrength.VERY_STRONG: 4.0,
            ZoneStrength.STRONG: 3.0,
            ZoneStrength.MEDIUM: 2.0,
            ZoneStrength.WEAK: 1.0
        }
        score += strength_scores[zone.strength]

        # Multi-timeframe confluence (if zones from other timeframes overlap)
        for tf, zones in all_zones.items():
            if tf != zone.timeframe:
                for other_zone in zones:
                    if other_zone.valid and other_zone.zone_type == zone.zone_type:
                        # Check for overlap
                        overlap = (zone.bottom <= other_zone.top and zone.top >= other_zone.bottom)
                        if overlap:
                            score += 1.0

        # Volume POC confluence
        if volume_poc_levels:
            for poc in volume_poc_levels:
                if zone.is_price_in_zone(poc):
                    score += 2.0  # High weight for volume confluence
                    zone.volume_poc_confluence = True
                    break

        # Freshness bonus (untested zones are stronger)
        if zone.test_count == 0:
            score += 1.0
        elif zone.test_count <= 2:
            score += 0.5
        else:
            score -= 0.5  # Penalty for over-tested zones

        return score