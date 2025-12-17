"""
Data models for regime detection and market features.

Uses dataclasses for type safety and validation.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class MarketFeatures:
    """Calculated market features for regime detection."""

    # Price structure
    vwap: float
    vwap_slope: float
    vwap_distance: float                # Current price distance from VWAP
    atr_14: float
    atr_slope: float
    bar_overlap_ratio: float            # Percentage of bars with overlap
    directional_efficiency: float       # Net move / total movement
    average_pullback_depth: float

    # Range metrics
    session_range: float
    historical_range_zscore: float      # Session range vs N-day average
    opening_range_position: str         # "above_orh", "below_orl", "inside"

    # Volatility
    realized_volatility_short: float    # 1-hour RV
    realized_volatility_long: float     # 4-hour RV
    volatility_ratio: float             # Short / Long

    # Participation
    cumulative_volume: int
    expected_volume: int                # Based on time-of-day curve
    volume_ratio: float                 # Actual / Expected
    volume_acceleration: float
    range_per_volume: float             # Thin vs heavy participation proxy

    # Session context
    session_phase: str
    minutes_since_open: int

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class RegimeOutput:
    """
    Regime classification output matching weather.md specification.

    This is the final output contract for the Weather Agent.
    """

    instrument: str                         # "ES" or "NQ"
    timestamp: str                          # ISO 8601 format
    primary_regime: str                     # Main regime classification
    secondary_tag: Optional[str]            # Regime subtype
    confidence: int                         # 0-100
    volatility_state: str                   # "compressing", "normal", "expanding", "extreme"
    participation_state: str                # "thin", "normal", "heavy"
    balance_state: str                      # "balanced", "transitioning", "imbalanced"
    trend_quality: str                      # "none", "weak", "clean", "extreme"
    noise_level: str                        # "low", "medium", "high"
    session_phase: str                      # Session phase from session.py
    order_flow_reliability_note: str        # Human-readable guidance

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, pretty: bool = False) -> str:
        """
        Convert to JSON string.

        Args:
            pretty: If True, format with indentation

        Returns:
            JSON string representation
        """
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        else:
            return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> 'RegimeOutput':
        """Create RegimeOutput from dictionary."""
        return cls(**data)


# Regime type constants
REGIME_BALANCED = "Balanced / Rotational"
REGIME_TREND = "Trend / Initiative"
REGIME_TRANSITION = "Transition / Breakout Attempt"
REGIME_EVENT_DISTORTED = "Event-Distorted"

# Secondary tags for Balanced regime
TAG_TIGHT_BALANCE = "tight"
TAG_NORMAL_BALANCE = "normal"
TAG_MIGRATING_BALANCE = "migrating"

# Secondary tags for Trend regime
TAG_CLEAN_TREND = "clean"
TAG_GRINDING_TREND = "grinding"
TAG_LIQUIDATION = "liquidation"

# Volatility states
VOLATILITY_COMPRESSING = "compressing"
VOLATILITY_NORMAL = "normal"
VOLATILITY_EXPANDING = "expanding"
VOLATILITY_EXTREME = "extreme"

# Participation states
PARTICIPATION_THIN = "thin"
PARTICIPATION_NORMAL = "normal"
PARTICIPATION_HEAVY = "heavy"

# Balance states
BALANCE_BALANCED = "balanced"
BALANCE_TRANSITIONING = "transitioning"
BALANCE_IMBALANCED = "imbalanced"

# Trend quality
TREND_NONE = "none"
TREND_WEAK = "weak"
TREND_CLEAN = "clean"
TREND_EXTREME = "extreme"

# Noise levels
NOISE_LOW = "low"
NOISE_MEDIUM = "medium"
NOISE_HIGH = "high"

# Opening range positions
OR_ABOVE_HIGH = "above_orh"
OR_BELOW_LOW = "below_orl"
OR_INSIDE = "inside"


# Reliability notes by regime type
RELIABILITY_NOTES = {
    REGIME_BALANCED: "Reliable only at range extremes; unreliable mid-range.",
    REGIME_TREND: "Continuation signals favored; fading less reliable.",
    REGIME_TRANSITION: "Signals unreliable until acceptance or failure.",
    REGIME_EVENT_DISTORTED: "All microstructure warped; interpretation degraded."
}
