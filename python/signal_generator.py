"""
Signal Generator for Elder Santis Supply & Demand Strategy

This module combines zone detection, volume analysis, and trend analysis to generate
A+ setup signals according to Elder's methodology.

A+ Setup Requirements (ALL must be present):
1. 4H trend direction confirmed
2. Price at valid S&D zone
3. 5M structure shift in trend direction
4. Volume confirmation (declining into zone OR absorption)
5. No red folder news
6. "Will I be mad if I lose?" check passes

Based on Elder's complete methodology from comprehensive research.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, time
import warnings

try:
    from .zone_detector import ZoneDetector, SupplyDemandZone, ZoneType, ZoneStrength
    from .volume_analyzer import VolumeAnalyzer, VolumeSignal, DivergenceType
except ImportError:
    from zone_detector import ZoneDetector, SupplyDemandZone, ZoneType, ZoneStrength
    from volume_analyzer import VolumeAnalyzer, VolumeSignal, DivergenceType

warnings.filterwarnings('ignore')

class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGE = "range"

class SetupQuality(Enum):
    A_PLUS = "A+"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B_MINUS = "B-"
    C = "C"

class SignalDirection(Enum):
    LONG = "long"
    SHORT = "short"

@dataclass
class StructureShift:
    """5-minute structure shift detection"""
    direction: SignalDirection
    confirmation_price: float
    timestamp: pd.Timestamp
    higher_high: Optional[float] = None
    higher_low: Optional[float] = None
    lower_high: Optional[float] = None
    lower_low: Optional[float] = None

@dataclass
class TradingSignal:
    """Complete trading signal with all confluence factors"""
    signal_id: str
    timestamp: pd.Timestamp
    direction: SignalDirection
    quality: SetupQuality
    confidence_score: float

    # Entry details
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float

    # Zone information
    zone: SupplyDemandZone
    zone_strength: ZoneStrength

    # Confluence factors
    trend_direction: TrendDirection
    structure_shift: StructureShift
    volume_signal: VolumeSignal
    volume_score: float

    # Risk management
    position_size: Optional[float] = None
    risk_amount: Optional[float] = None

    # Additional context
    notes: str = ""
    invalidated: bool = False

class SignalGenerator:
    """
    Generates A+ trading signals using Elder Santis's complete methodology

    Integrates:
    - Zone detection (supply/demand levels)
    - Volume analysis (CVD, volume profile, absorption)
    - Trend analysis (4H direction)
    - Structure shifts (5M execution)
    - Risk management (position sizing, R:R)
    """

    def __init__(
        self,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        min_rr_ratio: float = 2.0,     # Minimum 2:1 R:R
        max_daily_trades: int = 1,     # One & Done
        trading_start_time: str = "09:30",  # Market open
        trading_end_time: str = "16:00",    # Market close
        news_buffer_minutes: int = 30       # Minutes to avoid before/after news
    ):
        self.risk_per_trade = risk_per_trade
        self.min_rr_ratio = min_rr_ratio
        self.max_daily_trades = max_daily_trades
        self.trading_start_time = time.fromisoformat(trading_start_time)
        self.trading_end_time = time.fromisoformat(trading_end_time)
        self.news_buffer_minutes = news_buffer_minutes

        # Initialize analyzers
        self.zone_detector = ZoneDetector()
        self.volume_analyzer = VolumeAnalyzer()

        # Track daily trades (One & Done enforcement)
        self.daily_trade_count = {}

    def analyze_trend(self, df: pd.DataFrame, timeframe: str = "4H") -> TrendDirection:
        """
        Analyze 4-hour trend direction using Elder's methodology

        Bullish: Series of Higher Highs (HH) and Higher Lows (HL)
        Bearish: Series of Lower Lows (LL) and Lower Highs (LH)
        Range: No clear trend structure
        """
        if len(df) < 50:
            return TrendDirection.RANGE

        # Use EMA and price action to determine trend
        ema_50 = df['Close'].ewm(span=50).mean()
        ema_20 = df['Close'].ewm(span=20).mean()

        current_price = df['Close'].iloc[-1]
        current_ema_20 = ema_20.iloc[-1]
        current_ema_50 = ema_50.iloc[-1]

        # Find recent swing highs and lows
        recent_data = df.tail(30)

        # Simple swing detection using rolling max/min
        swing_high_period = 5
        swing_low_period = 5

        highs = recent_data['High'].rolling(swing_high_period*2+1, center=True).max()
        lows = recent_data['Low'].rolling(swing_low_period*2+1, center=True).min()

        swing_highs = recent_data[recent_data['High'] == highs]['High'].dropna()
        swing_lows = recent_data[recent_data['Low'] == lows]['Low'].dropna()

        # Analyze trend structure
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs.tail(2)
            recent_lows = swing_lows.tail(2)

            higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[0]
            higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[0]

            lower_highs = recent_highs.iloc[-1] < recent_highs.iloc[0]
            lower_lows = recent_lows.iloc[-1] < recent_lows.iloc[0]

            # Determine trend
            if higher_highs and higher_lows and current_price > current_ema_50:
                return TrendDirection.BULLISH
            elif lower_lows and lower_highs and current_price < current_ema_50:
                return TrendDirection.BEARISH

        return TrendDirection.RANGE

    def detect_structure_shift(
        self,
        df: pd.DataFrame,
        zone: SupplyDemandZone,
        trend: TrendDirection
    ) -> Optional[StructureShift]:
        """
        Detect 5-minute structure shift as per Elder's rules

        For LONGS (at demand): Wait for HH + HL formation
        For SHORTS (at supply): Wait for LL + LH formation
        """
        if len(df) < 20:
            return None

        # Get recent data for structure analysis
        recent_df = df.tail(15)

        # Find pivot highs and lows
        highs = []
        lows = []

        for i in range(2, len(recent_df)-2):
            if (recent_df['High'].iloc[i] > recent_df['High'].iloc[i-1] and
                recent_df['High'].iloc[i] > recent_df['High'].iloc[i+1] and
                recent_df['High'].iloc[i] > recent_df['High'].iloc[i-2] and
                recent_df['High'].iloc[i] > recent_df['High'].iloc[i+2]):
                highs.append((recent_df.index[i], recent_df['High'].iloc[i]))

            if (recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i-1] and
                recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i+1] and
                recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i-2] and
                recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i+2]):
                lows.append((recent_df.index[i], recent_df['Low'].iloc[i]))

        if len(highs) < 2 or len(lows) < 2:
            return None

        # Get the two most recent highs and lows
        recent_highs = sorted(highs, key=lambda x: x[0])[-2:]
        recent_lows = sorted(lows, key=lambda x: x[0])[-2:]

        # Check for bullish structure shift (HH + HL)
        if (zone.zone_type == ZoneType.DEMAND and
            trend == TrendDirection.BULLISH and
            len(recent_highs) >= 2 and len(recent_lows) >= 2):

            higher_high = recent_highs[-1][1] > recent_highs[0][1]
            higher_low = recent_lows[-1][1] > recent_lows[0][1]

            if higher_high and higher_low:
                return StructureShift(
                    direction=SignalDirection.LONG,
                    confirmation_price=recent_highs[-1][1],
                    timestamp=recent_highs[-1][0],
                    higher_high=recent_highs[-1][1],
                    higher_low=recent_lows[-1][1]
                )

        # Check for bearish structure shift (LL + LH)
        if (zone.zone_type == ZoneType.SUPPLY and
            trend == TrendDirection.BEARISH and
            len(recent_highs) >= 2 and len(recent_lows) >= 2):

            lower_low = recent_lows[-1][1] < recent_lows[0][1]
            lower_high = recent_highs[-1][1] < recent_highs[0][1]

            if lower_low and lower_high:
                return StructureShift(
                    direction=SignalDirection.SHORT,
                    confirmation_price=recent_lows[-1][1],
                    timestamp=recent_lows[-1][0],
                    lower_low=recent_lows[-1][1],
                    lower_high=recent_highs[-1][1]
                )

        return None

    def calculate_entry_levels(
        self,
        df: pd.DataFrame,
        zone: SupplyDemandZone,
        structure_shift: StructureShift,
        trend: TrendDirection
    ) -> Tuple[float, float, float]:
        """
        Calculate entry, stop loss, and take profit levels

        Entry: At zone edge or structure shift confirmation
        Stop: Below HL (longs) or above LH (shorts)
        Target: VWAP or next S&D zone
        """
        current_price = df['Close'].iloc[-1]

        # Calculate VWAP as primary target
        vwap = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        current_vwap = vwap.iloc[-1]

        if structure_shift.direction == SignalDirection.LONG:
            # Long setup
            entry_price = max(current_price, zone.bottom)

            # Stop loss below the higher low that confirmed structure shift
            if structure_shift.higher_low is not None:
                stop_loss = structure_shift.higher_low * 0.999  # Small buffer
            else:
                stop_loss = zone.bottom * 0.995

            # Take profit at VWAP (if above entry) or calculated target
            if current_vwap > entry_price:
                take_profit = current_vwap
            else:
                # Use 2:1 R:R minimum
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * self.min_rr_ratio)

        else:  # SHORT setup
            # Short setup
            entry_price = min(current_price, zone.top)

            # Stop loss above the lower high that confirmed structure shift
            if structure_shift.lower_high is not None:
                stop_loss = structure_shift.lower_high * 1.001  # Small buffer
            else:
                stop_loss = zone.top * 1.005

            # Take profit at VWAP (if below entry) or calculated target
            if current_vwap < entry_price:
                take_profit = current_vwap
            else:
                # Use 2:1 R:R minimum
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * self.min_rr_ratio)

        return entry_price, stop_loss, take_profit

    def calculate_setup_quality(
        self,
        zone: SupplyDemandZone,
        trend: TrendDirection,
        volume_score: float,
        structure_shift: StructureShift,
        confluence_factors: Dict
    ) -> Tuple[SetupQuality, float]:
        """
        Calculate setup quality and confidence score based on Elder's A+ criteria

        A+ Setup Requirements:
        - 4H trend aligned
        - Strong zone (4H preferred)
        - Volume confirmation
        - Structure shift confirmed
        - No news conflicts
        """
        score = 0.0

        # Zone strength scoring
        zone_scores = {
            ZoneStrength.VERY_STRONG: 4.0,  # 4H zones
            ZoneStrength.STRONG: 3.0,       # 2H zones
            ZoneStrength.MEDIUM: 2.0,       # 1H zones
            ZoneStrength.WEAK: 1.0          # 30M zones
        }
        score += zone_scores[zone.strength]

        # Trend alignment
        zone_trend_aligned = (
            (zone.zone_type == ZoneType.DEMAND and trend == TrendDirection.BULLISH) or
            (zone.zone_type == ZoneType.SUPPLY and trend == TrendDirection.BEARISH)
        )

        if zone_trend_aligned:
            score += 3.0
        elif trend == TrendDirection.RANGE:
            score += 1.0  # Can trade ranges but lower quality
        else:
            score -= 2.0  # Against trend

        # Volume analysis scoring
        score += min(volume_score, 5.0)  # Cap volume score at 5

        # Structure shift confirmation
        if structure_shift is not None:
            score += 2.0

        # Zone freshness (untested zones are stronger)
        if zone.test_count == 0:
            score += 1.0
        elif zone.test_count <= 2:
            score += 0.5
        else:
            score -= 0.5

        # Volume Profile confluence
        if zone.volume_poc_confluence:
            score += 2.0

        # News/time filters
        if confluence_factors.get('no_news', True):
            score += 1.0
        else:
            score -= 2.0

        if confluence_factors.get('good_time', True):
            score += 0.5

        # Determine setup quality
        if score >= 10.0:
            quality = SetupQuality.A_PLUS
        elif score >= 8.0:
            quality = SetupQuality.A_MINUS
        elif score >= 6.0:
            quality = SetupQuality.B_PLUS
        elif score >= 4.0:
            quality = SetupQuality.B_MINUS
        else:
            quality = SetupQuality.C

        # Confidence score (0-100)
        confidence = min(100.0, (score / 12.0) * 100.0)

        return quality, confidence

    def is_good_trading_time(self, timestamp: pd.Timestamp) -> bool:
        """
        Check if current time is good for trading (Elder's session preferences)

        Best times: 9:30-11:30 AM ET (market open)
        Good times: 1:30-3:00 PM ET (afternoon session)
        Avoid: Lunch 11:30-1:30 PM ET
        """
        if not hasattr(timestamp, 'time'):
            return True  # Default to True if no time info

        current_time = timestamp.time()

        # Best session: Market open
        if time(9, 30) <= current_time <= time(11, 30):
            return True

        # Good session: Afternoon
        if time(13, 30) <= current_time <= time(15, 0):
            return True

        # Outside good trading hours
        return False

    def can_trade_today(self, timestamp: pd.Timestamp) -> bool:
        """
        Check if we can take another trade today (One & Done enforcement)
        """
        if not hasattr(timestamp, 'date'):
            return True

        date_key = timestamp.date()
        trades_today = self.daily_trade_count.get(date_key, 0)

        return trades_today < self.max_daily_trades

    def record_trade(self, timestamp: pd.Timestamp):
        """Record that we took a trade today"""
        if hasattr(timestamp, 'date'):
            date_key = timestamp.date()
            self.daily_trade_count[date_key] = self.daily_trade_count.get(date_key, 0) + 1

    def generate_signals(
        self,
        df: pd.DataFrame,
        zones: List[SupplyDemandZone],
        account_size: float = 50000.0,
        current_timestamp: Optional[pd.Timestamp] = None
    ) -> List[TradingSignal]:
        """
        Main signal generation function

        Analyzes current market conditions and generates A+ setup signals
        according to Elder's complete methodology
        """
        signals = []

        if len(df) < 50 or not zones:
            return signals

        if current_timestamp is None:
            current_timestamp = df.index[-1] if hasattr(df.index[-1], 'to_pydatetime') else pd.Timestamp.now()

        # Check One & Done constraint
        if not self.can_trade_today(current_timestamp):
            return signals

        # Analyze overall market trend (4H equivalent)
        trend = self.analyze_trend(df)

        # Get current price for zone filtering
        current_price = df['Close'].iloc[-1]

        # Find zones near current price
        nearby_zones = []
        for zone in zones:
            if zone.valid:
                distance_to_zone = min(
                    abs(current_price - zone.top) / current_price,
                    abs(current_price - zone.bottom) / current_price
                )
                # Only consider zones within 1% of current price
                if distance_to_zone <= 0.01 or zone.is_price_in_zone(current_price):
                    nearby_zones.append(zone)

        # Analyze each nearby zone for potential setups
        for zone in nearby_zones:
            try:
                # Check trend alignment
                if ((zone.zone_type == ZoneType.DEMAND and trend == TrendDirection.BEARISH) or
                    (zone.zone_type == ZoneType.SUPPLY and trend == TrendDirection.BULLISH)):
                    continue  # Skip counter-trend setups for A+ signals

                # Detect structure shift
                structure_shift = self.detect_structure_shift(df, zone, trend)

                # Analyze volume
                zone_price = zone.mid_point
                zone_type_str = 'demand' if zone.zone_type == ZoneType.DEMAND else 'supply'

                volume_signal = self.volume_analyzer.analyze_volume_trend(
                    df, zone_type_str, zone_price
                )

                volume_score = self.volume_analyzer.get_volume_confluence_score(
                    df, zone_price, zone_type_str
                )

                # Check confluence factors
                confluence_factors = {
                    'no_news': True,  # TODO: Integrate news feed
                    'good_time': self.is_good_trading_time(current_timestamp)
                }

                # Only proceed if we have structure shift confirmation
                if structure_shift is None:
                    continue

                # Calculate entry levels
                entry_price, stop_loss, take_profit = self.calculate_entry_levels(
                    df, zone, structure_shift, trend
                )

                # Validate R:R ratio
                if structure_shift.direction == SignalDirection.LONG:
                    risk = entry_price - stop_loss
                    reward = take_profit - entry_price
                else:
                    risk = stop_loss - entry_price
                    reward = entry_price - take_profit

                if risk <= 0 or reward <= 0:
                    continue

                rr_ratio = reward / risk
                if rr_ratio < self.min_rr_ratio:
                    continue

                # Calculate setup quality and confidence
                quality, confidence = self.calculate_setup_quality(
                    zone, trend, volume_score, structure_shift, confluence_factors
                )

                # Only generate A- and A+ signals (high quality only)
                if quality not in [SetupQuality.A_PLUS, SetupQuality.A_MINUS]:
                    continue

                # Calculate position size (risk management)
                risk_amount = account_size * self.risk_per_trade
                position_size = risk_amount / risk

                # Generate signal
                signal_id = f"{zone_type_str}_{current_timestamp.strftime('%Y%m%d_%H%M%S')}_{len(signals)}"

                signal = TradingSignal(
                    signal_id=signal_id,
                    timestamp=current_timestamp,
                    direction=structure_shift.direction,
                    quality=quality,
                    confidence_score=confidence,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward_ratio=rr_ratio,
                    zone=zone,
                    zone_strength=zone.strength,
                    trend_direction=trend,
                    structure_shift=structure_shift,
                    volume_signal=volume_signal,
                    volume_score=volume_score,
                    position_size=position_size,
                    risk_amount=risk_amount,
                    notes=f"Trend: {trend.value}, Volume: {volume_signal.value}, Zone: {zone.timeframe}"
                )

                signals.append(signal)

            except Exception as e:
                # Log error and continue with next zone
                print(f"Error processing zone: {e}")
                continue

        # Sort signals by confidence score (highest first)
        signals.sort(key=lambda s: s.confidence_score, reverse=True)

        # For One & Done, only return the best signal
        if signals and self.max_daily_trades == 1:
            signals = [signals[0]]

        return signals

    def validate_signal(
        self,
        signal: TradingSignal,
        df: pd.DataFrame,
        news_events: Optional[List] = None
    ) -> bool:
        """
        Final validation before signal execution

        Elder's pre-trade question: "Will I be mad if I lose this trade?"
        """
        # Check if zone is still valid
        if not signal.zone.valid:
            return False

        # Check if we're still near the zone
        current_price = df['Close'].iloc[-1]
        if not signal.zone.is_price_in_zone(current_price):
            distance = min(
                abs(current_price - signal.zone.top) / current_price,
                abs(current_price - signal.zone.bottom) / current_price
            )
            if distance > 0.01:  # More than 1% away
                return False

        # Check news events (red folder news = avoid)
        if news_events:
            for event in news_events:
                if event.get('impact') == 'high':  # Red folder event
                    return False

        # Check position sizing (Elder's risk check)
        if signal.risk_amount is None or signal.risk_amount <= 0:
            return False

        # Ensure we won't be "mad" if we lose (reasonable risk)
        risk_percentage = (signal.risk_amount / 50000.0) * 100  # Assuming $50K account
        if risk_percentage > self.risk_per_trade * 100:
            return False

        return True