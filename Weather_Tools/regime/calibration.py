"""
ES and NQ calibration parameters for regime detection.

Different instruments require different thresholds due to varying volatility
and market structure characteristics.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class CalibrationParams:
    """Instrument-specific calibration parameters for regime detection."""

    instrument: str

    # Balance/Imbalance Classification Thresholds
    balance_threshold: float        # Score threshold to classify as "Balanced"
    imbalance_threshold: float      # Score threshold to classify as "Trend/Initiative"

    # ATR (Average True Range) Baselines
    atr_baseline: float             # Typical ATR value for "normal" volatility
    atr_extreme_zscore: float       # Z-score threshold for "extreme" volatility state

    # Directional Efficiency Thresholds (for trend quality)
    efficiency_trend_clean: float   # Efficiency threshold for "clean" trend
    efficiency_trend_weak: float    # Efficiency threshold for "weak" trend

    # Bar Overlap Thresholds (for balance detection)
    overlap_balanced_high: float    # High overlap indicates strong balance
    overlap_balanced_low: float     # Low overlap indicates imbalance

    # Volume Participation Thresholds
    volume_thin_threshold: float    # Volume ratio below this = "thin" participation
    volume_heavy_threshold: float   # Volume ratio above this = "heavy" participation

    # Volatility Ratio Thresholds (short-term RV / long-term RV)
    volatility_compressing: float   # Ratio below this = compressing
    volatility_expanding: float     # Ratio above this = expanding

    # VWAP Distance Threshold (for balance scoring)
    vwap_distance_threshold: float  # Price distance from VWAP (in points)

    # Confidence Scoring Parameters
    confidence_high_separation: float   # Score separation for high confidence
    confidence_medium_separation: float # Score separation for medium confidence


# ES Calibration (E-mini S&P 500)
# ES characteristics: Cleaner balance behavior, more reliable structure
ES_CALIBRATION = CalibrationParams(
    instrument="ES",

    # Classification thresholds
    balance_threshold=60.0,
    imbalance_threshold=60.0,

    # ATR baselines (ES typical range)
    atr_baseline=15.0,              # ~15 points typical ATR(14)
    atr_extreme_zscore=2.5,         # 2.5 standard deviations = extreme

    # Efficiency thresholds (ES accepts cleaner trends)
    efficiency_trend_clean=0.70,    # 70% efficiency = clean trend
    efficiency_trend_weak=0.50,     # 50-70% = weak trend

    # Overlap thresholds
    overlap_balanced_high=0.60,     # 60%+ overlap = strong balance
    overlap_balanced_low=0.30,      # <30% overlap = trending

    # Volume participation
    volume_thin_threshold=0.70,     # <70% of expected = thin
    volume_heavy_threshold=1.30,    # >130% of expected = heavy

    # Volatility ratios
    volatility_compressing=0.80,    # RV ratio <0.80 = compressing
    volatility_expanding=1.20,      # RV ratio >1.20 = expanding

    # VWAP distance (ES points)
    vwap_distance_threshold=5.0,    # Within 5 points = near VWAP

    # Confidence scoring
    confidence_high_separation=30.0,    # 30+ point separation = high confidence
    confidence_medium_separation=15.0   # 15-30 point separation = medium
)


# NQ Calibration (E-mini NASDAQ-100)
# NQ characteristics: Higher volatility, more false breakouts, requires stricter confirmation
NQ_CALIBRATION = CalibrationParams(
    instrument="NQ",

    # Classification thresholds (stricter than ES)
    balance_threshold=65.0,         # Require stronger evidence for balance
    imbalance_threshold=65.0,       # Require stronger evidence for trend

    # ATR baselines (NQ has higher volatility)
    atr_baseline=50.0,              # ~50 points typical ATR(14)
    atr_extreme_zscore=2.5,

    # Efficiency thresholds (NQ requires higher efficiency for trend confirmation)
    efficiency_trend_clean=0.75,    # 75% efficiency = clean trend (stricter)
    efficiency_trend_weak=0.55,     # 55-75% = weak trend

    # Overlap thresholds (NQ has more noise, so higher thresholds)
    overlap_balanced_high=0.65,     # 65%+ overlap = strong balance
    overlap_balanced_low=0.35,      # <35% overlap = trending

    # Volume participation
    volume_thin_threshold=0.70,
    volume_heavy_threshold=1.30,

    # Volatility ratios
    volatility_compressing=0.80,
    volatility_expanding=1.20,

    # VWAP distance (NQ points - wider range due to higher volatility)
    vwap_distance_threshold=15.0,   # Within 15 points = near VWAP

    # Confidence scoring (require more separation for NQ)
    confidence_high_separation=35.0,    # 35+ point separation = high confidence
    confidence_medium_separation=20.0   # 20-35 point separation = medium
)


def get_calibration(instrument: str) -> CalibrationParams:
    """
    Get calibration parameters for the specified instrument.

    Args:
        instrument: 'ES' or 'NQ'

    Returns:
        CalibrationParams for the instrument

    Raises:
        ValueError: If instrument is not supported
    """
    instrument_upper = instrument.upper()

    if instrument_upper == "ES":
        return ES_CALIBRATION
    elif instrument_upper == "NQ":
        return NQ_CALIBRATION
    else:
        raise ValueError(
            f"Unsupported instrument: {instrument}. "
            f"Supported instruments: ES, NQ"
        )


# Volume percentile curves (expected volume by time of day)
# These are placeholder values - should be calibrated from historical data
# Format: time bucket (15-min intervals) -> expected volume
ES_VOLUME_CURVE = {
    "08:30": 100000,  # Opening range - high volume
    "08:45": 90000,
    "09:00": 80000,
    "09:15": 70000,
    "09:30": 65000,   # Mid-morning
    "09:45": 60000,
    "10:00": 55000,
    "10:15": 50000,
    "10:30": 50000,
    "10:45": 50000,
    "11:00": 48000,
    "11:15": 45000,
    "11:30": 40000,   # Lunch - lower volume
    "11:45": 38000,
    "12:00": 35000,
    "12:15": 35000,
    "12:30": 35000,
    "12:45": 38000,
    "13:00": 45000,   # Mid-afternoon pickup
    "13:15": 50000,
    "13:30": 52000,
    "13:45": 55000,
    "14:00": 58000,
    "14:15": 60000,
    "14:30": 65000,
    "14:45": 70000,
    "15:00": 85000,   # Power hour - high volume
    "15:15": 90000,
    "15:30": 95000,
    "15:45": 100000,
    "16:00": 80000,   # Close
}

NQ_VOLUME_CURVE = {
    "08:30": 120000,  # NQ typically has higher volume
    "08:45": 105000,
    "09:00": 95000,
    "09:15": 85000,
    "09:30": 78000,
    "09:45": 72000,
    "10:00": 68000,
    "10:15": 65000,
    "10:30": 62000,
    "10:45": 60000,
    "11:00": 58000,
    "11:15": 55000,
    "11:30": 50000,
    "11:45": 48000,
    "12:00": 45000,
    "12:15": 45000,
    "12:30": 45000,
    "12:45": 48000,
    "13:00": 55000,
    "13:15": 60000,
    "13:30": 63000,
    "13:45": 67000,
    "14:00": 70000,
    "14:15": 73000,
    "14:30": 78000,
    "14:45": 85000,
    "15:00": 100000,
    "15:15": 110000,
    "15:30": 115000,
    "15:45": 120000,
    "16:00": 95000,
}


def get_expected_volume(instrument: str, time_bucket: str) -> int:
    """
    Get expected volume for a given time bucket.

    Args:
        instrument: 'ES' or 'NQ'
        time_bucket: Time in HH:MM format (15-minute buckets)

    Returns:
        Expected volume for that time period
    """
    instrument_upper = instrument.upper()

    if instrument_upper == "ES":
        return ES_VOLUME_CURVE.get(time_bucket, 50000)  # Default fallback
    elif instrument_upper == "NQ":
        return NQ_VOLUME_CURVE.get(time_bucket, 60000)  # Default fallback
    else:
        return 50000  # Generic fallback
