"""
Feature calculation engine for regime detection.

Calculates all market features required for regime classification:
- VWAP and slope
- ATR and volatility metrics
- Bar overlap ratios
- Directional efficiency
- Volume analysis
- Range metrics
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from Weather_Tools.regime.models import MarketFeatures, OR_ABOVE_HIGH, OR_BELOW_LOW, OR_INSIDE
from Weather_Tools.regime.calibration import CalibrationParams, get_expected_volume
from Weather_Tools.utils.session import get_session_phase, minutes_since_session_open

logger = logging.getLogger(__name__)


class FeatureCalculator:
    """Calculate market features from price data."""

    def __init__(self, instrument: str, calibration: CalibrationParams):
        """
        Initialize feature calculator.

        Args:
            instrument: 'ES' or 'NQ'
            calibration: Calibration parameters for the instrument
        """
        self.instrument = instrument
        self.calibration = calibration

    def calculate_features(
        self,
        candles_1m: List[Dict],
        candles_5m: List[Dict],
        current_quote: Dict
    ) -> MarketFeatures:
        """
        Calculate all features required for regime classification.

        Args:
            candles_1m: List of 1-minute candles (OHLCV dicts)
            candles_5m: List of 5-minute candles (OHLCV dicts)
            current_quote: Current quote data with 'lastPrice'

        Returns:
            MarketFeatures dataclass with all calculated features

        Raises:
            ValueError: If insufficient data for calculations
        """
        if len(candles_5m) < 20:
            raise ValueError(f"Insufficient 5m candles for calculation: {len(candles_5m)} (need 20+)")

        if len(candles_1m) < 60:
            raise ValueError(f"Insufficient 1m candles for calculation: {len(candles_1m)} (need 60+)")

        logger.debug(f"Calculating features for {self.instrument}")

        # Current price
        current_price = current_quote.get('lastPrice', candles_5m[-1]['close'])

        # VWAP calculations
        vwap = self._calculate_vwap(candles_5m)
        vwap_series = self._calculate_vwap_series(candles_5m, window=20)
        vwap_slope = self._calculate_slope(vwap_series)
        vwap_distance = abs(current_price - vwap)

        # ATR calculations
        atr_14 = self._calculate_atr(candles_5m, period=14)
        atr_series = [self._calculate_atr(candles_5m[max(0, i-13):i+1], period=min(14, i+1))
                      for i in range(14, len(candles_5m))]
        atr_slope = self._calculate_slope(atr_series[-10:]) if len(atr_series) >= 10 else 0.0

        # Bar overlap ratio
        bar_overlap_ratio = self._calculate_bar_overlap_ratio(candles_5m)

        # Directional efficiency
        directional_efficiency = self._calculate_directional_efficiency(candles_5m)

        # Average pullback depth
        average_pullback_depth = self._calculate_average_pullback_depth(candles_5m)

        # Range metrics
        session_range = self._calculate_session_range(candles_5m)
        historical_range_zscore = self._calculate_range_zscore(candles_5m)
        opening_range_position = self._get_opening_range_position(candles_5m, current_price)

        # Volatility metrics
        rv_short = self._calculate_realized_volatility(candles_1m[-60:])  # 1 hour
        rv_long = self._calculate_realized_volatility(candles_1m[-240:] if len(candles_1m) >= 240 else candles_1m)  # 4 hours
        volatility_ratio = rv_short / rv_long if rv_long > 0 else 1.0

        # Volume metrics
        cumulative_volume = sum(c['volume'] for c in candles_5m)
        expected_volume = self._get_expected_volume_for_session(candles_5m)
        volume_ratio = cumulative_volume / expected_volume if expected_volume > 0 else 1.0
        volume_acceleration = self._calculate_volume_acceleration(candles_5m)
        range_per_volume = session_range / cumulative_volume if cumulative_volume > 0 else 0.0

        # Session context
        session_phase = get_session_phase()
        minutes = minutes_since_session_open()

        # Build features object
        features = MarketFeatures(
            vwap=vwap,
            vwap_slope=vwap_slope,
            vwap_distance=vwap_distance,
            atr_14=atr_14,
            atr_slope=atr_slope,
            bar_overlap_ratio=bar_overlap_ratio,
            directional_efficiency=directional_efficiency,
            average_pullback_depth=average_pullback_depth,
            session_range=session_range,
            historical_range_zscore=historical_range_zscore,
            opening_range_position=opening_range_position,
            realized_volatility_short=rv_short,
            realized_volatility_long=rv_long,
            volatility_ratio=volatility_ratio,
            cumulative_volume=cumulative_volume,
            expected_volume=expected_volume,
            volume_ratio=volume_ratio,
            volume_acceleration=volume_acceleration,
            range_per_volume=range_per_volume,
            session_phase=session_phase,
            minutes_since_open=minutes
        )

        logger.info(f"Features calculated: VWAP={vwap:.2f}, ATR={atr_14:.2f}, Efficiency={directional_efficiency:.2f}")

        return features

    def _calculate_vwap(self, candles: List[Dict]) -> float:
        """
        Calculate Volume-Weighted Average Price.

        VWAP = Σ(price × volume) / Σ(volume)
        Using typical price: (high + low + close) / 3
        """
        total_pv = 0.0
        total_volume = 0

        for candle in candles:
            typical_price = (candle['high'] + candle['low'] + candle['close']) / 3
            total_pv += typical_price * candle['volume']
            total_volume += candle['volume']

        return total_pv / total_volume if total_volume > 0 else candles[-1]['close']

    def _calculate_vwap_series(self, candles: List[Dict], window: int) -> List[float]:
        """Calculate rolling VWAP for last N periods."""
        vwap_series = []

        for i in range(window, len(candles) + 1):
            window_candles = candles[i-window:i]
            vwap = self._calculate_vwap(window_candles)
            vwap_series.append(vwap)

        return vwap_series

    def _calculate_slope(self, series: List[float]) -> float:
        """
        Calculate linear regression slope of a series.

        Returns slope normalized by the mean value.
        """
        if len(series) < 2:
            return 0.0

        x = np.arange(len(series))
        y = np.array(series)

        # Linear regression
        slope, _ = np.polyfit(x, y, 1)

        # Normalize by mean to get percentage slope
        mean_val = np.mean(y)
        normalized_slope = (slope / mean_val) if mean_val != 0 else 0.0

        return float(normalized_slope)

    def _calculate_atr(self, candles: List[Dict], period: int = 14) -> float:
        """
        Calculate Average True Range.

        TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = average of TR over period
        """
        if len(candles) < 2:
            return candles[0]['high'] - candles[0]['low'] if candles else 0.0

        true_ranges = []

        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Take last 'period' TRs
        recent_trs = true_ranges[-period:] if len(true_ranges) > period else true_ranges

        return float(np.mean(recent_trs)) if recent_trs else 0.0

    def _calculate_bar_overlap_ratio(self, candles: List[Dict], window: int = 20) -> float:
        """
        Calculate percentage of consecutive bars that overlap.

        Overlap exists when: min(high1, high2) > max(low1, low2)
        """
        if len(candles) < 2:
            return 0.0

        recent_candles = candles[-window:] if len(candles) > window else candles
        overlaps = 0
        total_pairs = len(recent_candles) - 1

        for i in range(1, len(recent_candles)):
            prev = recent_candles[i-1]
            curr = recent_candles[i]

            overlap_high = min(prev['high'], curr['high'])
            overlap_low = max(prev['low'], curr['low'])

            if overlap_high > overlap_low:
                overlaps += 1

        return overlaps / total_pairs if total_pairs > 0 else 0.0

    def _calculate_directional_efficiency(self, candles: List[Dict]) -> float:
        """
        Calculate directional efficiency.

        Efficiency = net_movement / total_movement
        Net = abs(last_close - first_open)
        Total = sum(high - low for all bars)
        """
        if not candles:
            return 0.0

        net_movement = abs(candles[-1]['close'] - candles[0]['open'])
        total_movement = sum(c['high'] - c['low'] for c in candles)

        return net_movement / total_movement if total_movement > 0 else 0.0

    def _calculate_average_pullback_depth(self, candles: List[Dict], window: int = 20) -> float:
        """
        Calculate average pullback depth.

        For upward moves: (high - low) / (high - open)
        For downward moves: (high - low) / (open - low)
        """
        recent = candles[-window:] if len(candles) > window else candles
        pullbacks = []

        for candle in recent:
            range_val = candle['high'] - candle['low']

            if candle['close'] > candle['open']:  # Up bar
                denominator = candle['high'] - candle['open']
            else:  # Down bar
                denominator = candle['open'] - candle['low']

            if denominator > 0:
                pullback = range_val / denominator
                pullbacks.append(pullback)

        return float(np.mean(pullbacks)) if pullbacks else 1.0

    def _calculate_session_range(self, candles: List[Dict]) -> float:
        """Calculate high-to-low range for the session."""
        if not candles:
            return 0.0

        session_high = max(c['high'] for c in candles)
        session_low = min(c['low'] for c in candles)

        return session_high - session_low

    def _calculate_range_zscore(self, candles: List[Dict], lookback: int = 20) -> float:
        """
        Calculate z-score of current session range vs historical ranges.

        Z-score = (current_range - mean_range) / std_range
        """
        if len(candles) < lookback:
            return 0.0

        # Calculate daily ranges for last N days
        # Approximate: group candles into day-sized chunks
        chunk_size = min(78, len(candles) // 5)  # ~6.5 hours of 5m bars
        ranges = []

        for i in range(0, len(candles) - chunk_size, chunk_size):
            chunk = candles[i:i+chunk_size]
            chunk_high = max(c['high'] for c in chunk)
            chunk_low = min(c['low'] for c in chunk)
            ranges.append(chunk_high - chunk_low)

        if len(ranges) < 2:
            return 0.0

        current_range = self._calculate_session_range(candles[-chunk_size:])
        mean_range = np.mean(ranges)
        std_range = np.std(ranges)

        if std_range == 0:
            return 0.0

        return float((current_range - mean_range) / std_range)

    def _get_opening_range_position(self, candles: List[Dict], current_price: float) -> str:
        """
        Determine if price is above/below/inside opening range.

        Opening range = first 30 minutes (6 five-minute candles)
        """
        if len(candles) < 6:
            return OR_INSIDE

        or_candles = candles[:6]
        or_high = max(c['high'] for c in or_candles)
        or_low = min(c['low'] for c in or_candles)

        if current_price > or_high:
            return OR_ABOVE_HIGH
        elif current_price < or_low:
            return OR_BELOW_LOW
        else:
            return OR_INSIDE

    def _calculate_realized_volatility(self, candles: List[Dict]) -> float:
        """
        Calculate realized volatility (standard deviation of log returns).

        RV = std(log(close[i] / close[i-1]))
        """
        if len(candles) < 2:
            return 0.0

        log_returns = []

        for i in range(1, len(candles)):
            if candles[i-1]['close'] > 0:
                log_return = np.log(candles[i]['close'] / candles[i-1]['close'])
                log_returns.append(log_return)

        return float(np.std(log_returns)) if log_returns else 0.0

    def _get_expected_volume_for_session(self, candles: List[Dict]) -> int:
        """
        Get expected cumulative volume based on time of day.

        Sums expected volume for each 15-minute bucket.
        """
        if not candles:
            return 50000

        # Rough estimate: assume 5m candles, count them and multiply by expected per bucket
        num_candles = len(candles)
        minutes_elapsed = num_candles * 5

        # Get current time bucket
        current_minute = minutes_since_session_open()

        # Round to 15-minute bucket
        bucket_minute = (current_minute // 15) * 15
        hour = 8 + (bucket_minute // 60)
        minute = bucket_minute % 60
        time_bucket = f"{hour:02d}:{minute:02d}"

        expected = get_expected_volume(self.instrument, time_bucket)

        # Scale by actual minutes elapsed
        # This is a simplification - ideally would sum actual buckets
        return int(expected * (minutes_elapsed / 15))

    def _calculate_volume_acceleration(self, candles: List[Dict], window: int = 10) -> float:
        """
        Calculate volume acceleration (recent vs earlier).

        Ratio of last N candles avg volume to previous N candles avg volume
        """
        if len(candles) < window * 2:
            return 1.0

        recent = candles[-window:]
        earlier = candles[-window*2:-window]

        recent_avg = np.mean([c['volume'] for c in recent])
        earlier_avg = np.mean([c['volume'] for c in earlier])

        return float(recent_avg / earlier_avg) if earlier_avg > 0 else 1.0
