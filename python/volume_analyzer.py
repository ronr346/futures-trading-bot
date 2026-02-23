"""
Volume Analysis Module for Elder Santis Supply & Demand Strategy

This module implements Elder's volume analysis techniques:
- Volume Profile calculation (POC, value area)
- CVD (Cumulative Volume Delta) calculation and divergence detection
- Volume trend analysis (declining = bounce, increasing = break)
- Absorption detection using volume delta

Based on Elder's methodology: "Volume is showing me that we're going to break the level or not"
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class VolumeSignal(Enum):
    BOUNCE_EXPECTED = "bounce"
    BREAK_EXPECTED = "break"
    NEUTRAL = "neutral"

class DivergenceType(Enum):
    BULLISH = "bullish"  # Price lower low, CVD higher low
    BEARISH = "bearish"  # Price higher high, CVD lower high
    NONE = "none"

@dataclass
class VolumeProfile:
    """Volume Profile data structure"""
    price_levels: List[float]
    volumes: List[float]
    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    total_volume: float
    value_area_volume: float

@dataclass
class CVDAnalysis:
    """Cumulative Volume Delta analysis results"""
    cvd_values: pd.Series
    cvd_slope: float
    divergence_type: DivergenceType
    absorption_signal: bool
    exhaustion_signal: bool

@dataclass
class VolumeAbsorption:
    """Volume absorption analysis"""
    timestamp: pd.Timestamp
    price: float
    volume: float
    delta: float
    absorption_strength: float
    zone_type: str  # 'supply' or 'demand'

class VolumeAnalyzer:
    """
    Analyzes volume patterns according to Elder Santis's methodology

    Key concepts:
    - Declining volume into zone = expect bounce
    - Increasing volume into zone = expect break
    - CVD divergence = absorption (institutions absorbing retail)
    - Volume exhaustion at extremes = reversal signal
    """

    def __init__(
        self,
        volume_ma_period: int = 20,
        poc_resolution: int = 100,
        value_area_percentage: float = 0.68,
        cvd_lookback: int = 20,
        absorption_threshold: float = 2.0
    ):
        self.volume_ma_period = volume_ma_period
        self.poc_resolution = poc_resolution
        self.value_area_percentage = value_area_percentage
        self.cvd_lookback = cvd_lookback
        self.absorption_threshold = absorption_threshold

    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None
    ) -> VolumeProfile:
        """
        Calculate Volume Profile for the given data range

        Returns POC (Point of Control), VAH (Value Area High), VAL (Value Area Low)
        """
        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = len(df)

        data_slice = df.iloc[start_index:end_index]

        if len(data_slice) == 0:
            return None

        # Define price range and resolution
        price_min = data_slice['Low'].min()
        price_max = data_slice['High'].max()

        if price_max <= price_min:
            return None

        price_levels = np.linspace(price_min, price_max, self.poc_resolution)
        volume_at_price = np.zeros(len(price_levels))

        # Distribute volume across price levels for each candle
        for _, row in data_slice.iterrows():
            candle_low = row['Low']
            candle_high = row['High']
            candle_volume = row['Volume']

            # Find price levels within this candle's range
            in_range = (price_levels >= candle_low) & (price_levels <= candle_high)
            num_levels_in_range = np.sum(in_range)

            if num_levels_in_range > 0:
                # Distribute volume evenly across price levels in range
                volume_per_level = candle_volume / num_levels_in_range
                volume_at_price[in_range] += volume_per_level

        # Find POC (Point of Control) - price level with highest volume
        poc_index = np.argmax(volume_at_price)
        poc = price_levels[poc_index]

        # Calculate Value Area (68% of volume around POC)
        total_volume = np.sum(volume_at_price)
        target_volume = total_volume * self.value_area_percentage

        # Expand from POC until we capture target volume
        value_area_volume = volume_at_price[poc_index]
        val_index = poc_index
        vah_index = poc_index

        while value_area_volume < target_volume and (val_index > 0 or vah_index < len(price_levels) - 1):
            # Expand to the side with more volume
            val_volume = volume_at_price[val_index - 1] if val_index > 0 else 0
            vah_volume = volume_at_price[vah_index + 1] if vah_index < len(price_levels) - 1 else 0

            if val_volume >= vah_volume and val_index > 0:
                val_index -= 1
                value_area_volume += volume_at_price[val_index]
            elif vah_index < len(price_levels) - 1:
                vah_index += 1
                value_area_volume += volume_at_price[vah_index]
            else:
                break

        val = price_levels[val_index]
        vah = price_levels[vah_index]

        return VolumeProfile(
            price_levels=price_levels.tolist(),
            volumes=volume_at_price.tolist(),
            poc=poc,
            vah=vah,
            val=val,
            total_volume=total_volume,
            value_area_volume=value_area_volume
        )

    def calculate_daily_volume_profiles(self, df: pd.DataFrame) -> Dict[str, VolumeProfile]:
        """
        Calculate volume profiles for each trading session/day
        Following Elder's approach of daily volume profile boxes
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            return {}

        daily_profiles = {}

        # Group by date
        df['Date'] = df.index.date
        grouped = df.groupby('Date')

        for date, group in grouped:
            date_str = date.strftime('%Y-%m-%d')
            profile = self.calculate_volume_profile(group)
            if profile:
                daily_profiles[date_str] = profile

        return daily_profiles

    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Cumulative Volume Delta (CVD)

        Since we don't have tick data, we approximate using price-volume relationship:
        - If close > open: assume more buying pressure (positive delta)
        - If close < open: assume more selling pressure (negative delta)

        This is an approximation of what Elder sees on Bookmap
        """
        # Calculate per-candle delta (approximation)
        delta = np.where(
            df['Close'] > df['Open'],
            df['Volume'],  # Bullish candle = positive delta
            -df['Volume']  # Bearish candle = negative delta
        )

        # For doji candles, consider the wick direction
        doji_mask = np.abs(df['Close'] - df['Open']) < (df['High'] - df['Low']) * 0.1
        upper_wick = df['High'] - np.maximum(df['Open'], df['Close'])
        lower_wick = np.minimum(df['Open'], df['Close']) - df['Low']

        # For doji, assign delta based on wick dominance
        delta = np.where(
            doji_mask & (upper_wick > lower_wick),
            -df['Volume'] * 0.5,  # Upper wick dominance = selling
            np.where(
                doji_mask & (lower_wick > upper_wick),
                df['Volume'] * 0.5,   # Lower wick dominance = buying
                delta
            )
        )

        # Calculate cumulative delta
        cvd = pd.Series(delta, index=df.index).cumsum()

        return cvd

    def detect_cvd_divergence(
        self,
        df: pd.DataFrame,
        cvd: pd.Series,
        lookback: int = None
    ) -> DivergenceType:
        """
        Detect CVD divergence patterns that Elder uses for absorption signals

        Bullish divergence: Price making lower lows, but CVD making higher lows
        Bearish divergence: Price making higher highs, but CVD making lower highs
        """
        if lookback is None:
            lookback = self.cvd_lookback

        if len(df) < lookback + 5:
            return DivergenceType.NONE

        # Look at recent data
        recent_df = df.tail(lookback)
        recent_cvd = cvd.tail(lookback)

        # Find recent highs and lows
        price_high_idx = recent_df['High'].idxmax()
        price_low_idx = recent_df['Low'].idxmin()

        cvd_high_idx = recent_cvd.idxmax()
        cvd_low_idx = recent_cvd.idxmin()

        # Get the actual values
        price_high = recent_df.loc[price_high_idx, 'High']
        price_low = recent_df.loc[price_low_idx, 'Low']
        cvd_high = recent_cvd.loc[cvd_high_idx]
        cvd_low = recent_cvd.loc[cvd_low_idx]

        # Check for divergence patterns
        # For bearish divergence: new price high but CVD not making new high
        recent_price_high = df['High'].tail(5).max()
        recent_cvd_at_high = cvd.tail(5).max()

        if (recent_price_high >= price_high * 0.999 and
            recent_cvd_at_high < cvd_high * 0.99):
            return DivergenceType.BEARISH

        # For bullish divergence: new price low but CVD not making new low
        recent_price_low = df['Low'].tail(5).min()
        recent_cvd_at_low = cvd.tail(5).min()

        if (recent_price_low <= price_low * 1.001 and
            recent_cvd_at_low > cvd_low * 1.01):
            return DivergenceType.BULLISH

        return DivergenceType.NONE

    def analyze_cvd(self, df: pd.DataFrame) -> CVDAnalysis:
        """
        Complete CVD analysis including divergence and absorption detection
        """
        cvd = self.calculate_cvd(df)

        # Calculate CVD slope (trend)
        if len(cvd) >= 10:
            recent_cvd = cvd.tail(10)
            cvd_slope = (recent_cvd.iloc[-1] - recent_cvd.iloc[0]) / len(recent_cvd)
        else:
            cvd_slope = 0.0

        # Detect divergence
        divergence = self.detect_cvd_divergence(df, cvd)

        # Absorption signal (CVD divergence at key levels)
        absorption_signal = divergence != DivergenceType.NONE

        # Exhaustion signal (CVD flattening after strong trend)
        exhaustion_signal = abs(cvd_slope) < abs(cvd.tail(20).std()) * 0.1

        return CVDAnalysis(
            cvd_values=cvd,
            cvd_slope=cvd_slope,
            divergence_type=divergence,
            absorption_signal=absorption_signal,
            exhaustion_signal=exhaustion_signal
        )

    def analyze_volume_trend(
        self,
        df: pd.DataFrame,
        approaching_zone: str,
        zone_price: float,
        lookback: int = 5
    ) -> VolumeSignal:
        """
        Analyze volume trend as price approaches a zone

        Elder's rule:
        - Declining volume into zone = expect bounce
        - Increasing volume into zone = expect break

        Args:
            approaching_zone: 'supply' or 'demand'
            zone_price: The price level of the zone
        """
        if len(df) < lookback + 1:
            return VolumeSignal.NEUTRAL

        recent_df = df.tail(lookback)

        # Calculate volume trend
        volume_ma = recent_df['Volume'].rolling(3).mean()
        volume_trend = volume_ma.iloc[-1] - volume_ma.iloc[0]

        # Check if we're actually approaching the zone
        current_price = df['Close'].iloc[-1]
        price_direction_to_zone = zone_price - current_price

        # Determine expected behavior based on volume trend
        volume_increasing = volume_trend > recent_df['Volume'].std() * 0.5
        volume_decreasing = volume_trend < -recent_df['Volume'].std() * 0.5

        if volume_decreasing:
            return VolumeSignal.BOUNCE_EXPECTED
        elif volume_increasing:
            return VolumeSignal.BREAK_EXPECTED
        else:
            return VolumeSignal.NEUTRAL

    def detect_volume_exhaustion(
        self,
        df: pd.DataFrame,
        lookback: int = 10
    ) -> Dict[str, bool]:
        """
        Detect volume exhaustion at price extremes

        Elder's concept: Volume dying out at tops/bottoms = reversal signal
        """
        if len(df) < lookback:
            return {'bullish_exhaustion': False, 'bearish_exhaustion': False}

        recent_df = df.tail(lookback)

        # Check if we're at/near highs or lows
        current_high = df['High'].iloc[-1]
        current_low = df['Low'].iloc[-1]

        period_high = recent_df['High'].max()
        period_low = recent_df['Low'].min()

        at_high = current_high >= period_high * 0.999
        at_low = current_low <= period_low * 1.001

        # Check volume trend
        recent_volumes = recent_df['Volume'].tail(3)
        volume_declining = all(recent_volumes.iloc[i] > recent_volumes.iloc[i+1]
                              for i in range(len(recent_volumes)-1))

        return {
            'bullish_exhaustion': at_low and volume_declining,
            'bearish_exhaustion': at_high and volume_declining
        }

    def detect_absorption(
        self,
        df: pd.DataFrame,
        zone_price: float,
        zone_type: str
    ) -> Optional[VolumeAbsorption]:
        """
        Detect volume absorption at supply/demand zones

        Absorption occurs when:
        - Large volume but price doesn't move through zone
        - CVD shows divergence at the zone
        """
        if len(df) < 5:
            return None

        current_candle = df.iloc[-1]
        current_price = current_candle['Close']
        current_volume = current_candle['Volume']

        # Check if we're at the zone
        price_tolerance = abs(zone_price - current_price) / zone_price
        if price_tolerance > 0.005:  # More than 0.5% away
            return None

        # Calculate recent volume statistics
        avg_volume = df['Volume'].tail(10).mean()
        volume_spike = current_volume > avg_volume * self.absorption_threshold

        # Calculate approximate delta for current candle
        if current_candle['Close'] > current_candle['Open']:
            current_delta = current_volume
        else:
            current_delta = -current_volume

        # Check for absorption pattern
        absorption_detected = False
        absorption_strength = 0.0

        if zone_type == 'supply':
            # At supply zone, look for buying being absorbed
            if (current_delta > 0 and  # Positive delta (buying)
                current_candle['High'] <= zone_price * 1.002 and  # Price not breaking above
                volume_spike):  # High volume
                absorption_detected = True
                absorption_strength = current_volume / avg_volume

        elif zone_type == 'demand':
            # At demand zone, look for selling being absorbed
            if (current_delta < 0 and  # Negative delta (selling)
                current_candle['Low'] >= zone_price * 0.998 and  # Price not breaking below
                volume_spike):  # High volume
                absorption_detected = True
                absorption_strength = current_volume / avg_volume

        if absorption_detected:
            return VolumeAbsorption(
                timestamp=current_candle.name if hasattr(current_candle, 'name') else None,
                price=current_price,
                volume=current_volume,
                delta=current_delta,
                absorption_strength=absorption_strength,
                zone_type=zone_type
            )

        return None

    def calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate various volume indicators used in Elder's analysis
        """
        indicators = {}

        # Volume Moving Average
        indicators['volume_ma'] = df['Volume'].rolling(self.volume_ma_period).mean()

        # Volume Relative to Average
        indicators['volume_ratio'] = df['Volume'] / indicators['volume_ma']

        # CVD (Cumulative Volume Delta)
        indicators['cvd'] = self.calculate_cvd(df)

        # CVD Moving Average
        indicators['cvd_ma'] = indicators['cvd'].rolling(self.volume_ma_period).mean()

        # Volume Rate of Change
        indicators['volume_roc'] = df['Volume'].pct_change(5)

        # Price-Volume Trend
        price_change = df['Close'].pct_change()
        volume_change = df['Volume'].pct_change()
        indicators['pv_trend'] = price_change * volume_change

        # On Balance Volume (OBV) - alternative to CVD
        obv_values = []
        obv = 0
        for i, row in df.iterrows():
            if i == 0:
                obv_values.append(0)
                continue

            prev_close = df['Close'].iloc[df.index.get_loc(i) - 1]
            if row['Close'] > prev_close:
                obv += row['Volume']
            elif row['Close'] < prev_close:
                obv -= row['Volume']
            # If close == prev_close, OBV stays the same

            obv_values.append(obv)

        indicators['obv'] = pd.Series(obv_values, index=df.index)

        return indicators

    def get_volume_confluence_score(
        self,
        df: pd.DataFrame,
        zone_price: float,
        zone_type: str
    ) -> float:
        """
        Calculate a confluence score based on volume analysis
        Higher score = higher probability setup
        """
        score = 0.0

        # Analyze volume trend approaching zone
        volume_signal = self.analyze_volume_trend(df, zone_type, zone_price)

        if volume_signal == VolumeSignal.BOUNCE_EXPECTED:
            score += 2.0  # Strong positive signal
        elif volume_signal == VolumeSignal.BREAK_EXPECTED:
            score -= 1.0  # Negative for bounce plays

        # CVD analysis
        cvd_analysis = self.analyze_cvd(df)

        if cvd_analysis.absorption_signal:
            score += 3.0  # Very strong signal

        if cvd_analysis.exhaustion_signal:
            score += 1.0

        # Volume exhaustion at extremes
        exhaustion = self.detect_volume_exhaustion(df)

        if zone_type == 'demand' and exhaustion['bullish_exhaustion']:
            score += 2.0
        elif zone_type == 'supply' and exhaustion['bearish_exhaustion']:
            score += 2.0

        # Volume Profile confluence
        daily_profiles = self.calculate_daily_volume_profiles(df)
        if daily_profiles:
            latest_profile = list(daily_profiles.values())[-1]

            # Check if zone aligns with POC
            poc_distance = abs(zone_price - latest_profile.poc) / zone_price
            if poc_distance < 0.005:  # Within 0.5%
                score += 2.0

            # Check if zone is in value area
            if latest_profile.val <= zone_price <= latest_profile.vah:
                score += 1.0

        return max(0.0, score)  # Ensure non-negative score