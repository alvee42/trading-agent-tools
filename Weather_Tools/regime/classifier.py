"""
Regime classification logic.

Implements the decision tree from weather.md to classify market regimes.
"""

import logging
from datetime import datetime, timezone
from typing import Tuple, Optional

from Weather_Tools.regime.models import (
    MarketFeatures, RegimeOutput,
    REGIME_BALANCED, REGIME_TREND, REGIME_TRANSITION, REGIME_EVENT_DISTORTED,
    TAG_TIGHT_BALANCE, TAG_NORMAL_BALANCE, TAG_MIGRATING_BALANCE,
    TAG_CLEAN_TREND, TAG_GRINDING_TREND, TAG_LIQUIDATION,
    VOLATILITY_COMPRESSING, VOLATILITY_NORMAL, VOLATILITY_EXPANDING, VOLATILITY_EXTREME,
    PARTICIPATION_THIN, PARTICIPATION_NORMAL, PARTICIPATION_HEAVY,
    BALANCE_BALANCED, BALANCE_TRANSITIONING, BALANCE_IMBALANCED,
    TREND_NONE, TREND_WEAK, TREND_CLEAN, TREND_EXTREME,
    NOISE_LOW, NOISE_MEDIUM, NOISE_HIGH,
    RELIABILITY_NOTES
)
from Weather_Tools.regime.calibration import CalibrationParams

logger = logging.getLogger(__name__)


class RegimeClassifier:
    """Classify market regime from calculated features."""

    def __init__(self, instrument: str, calibration: CalibrationParams):
        """
        Initialize regime classifier.

        Args:
            instrument: 'ES' or 'NQ'
            calibration: Calibration parameters for the instrument
        """
        self.instrument = instrument
        self.calibration = calibration

    def classify(self, features: MarketFeatures) -> RegimeOutput:
        """
        Classify market regime from features.

        This is the main classification pipeline implementing weather.md logic.

        Args:
            features: Calculated market features

        Returns:
            RegimeOutput with full classification
        """
        logger.debug(f"Classifying regime for {self.instrument}")

        # Step 1: Calculate balance and imbalance scores
        balance_score = self._calculate_balance_score(features)
        imbalance_score = self._calculate_imbalance_score(features)

        logger.debug(f"Balance score: {balance_score:.1f}, Imbalance score: {imbalance_score:.1f}")

        # Step 2: Classify primary regime and secondary tag
        primary_regime, secondary_tag = self._classify_primary_regime(
            balance_score, imbalance_score, features
        )

        # Step 3: Classify volatility state
        volatility_state = self._classify_volatility_state(features)

        # Step 4: Classify participation state
        participation_state = self._classify_participation_state(features)

        # Step 5: Classify balance state
        balance_state = self._classify_balance_state(balance_score, imbalance_score)

        # Step 6: Classify trend quality
        trend_quality = self._classify_trend_quality(features, primary_regime)

        # Step 7: Calculate confidence
        confidence = self._calculate_confidence(balance_score, imbalance_score, features)

        # Step 8: Classify noise level
        noise_level = self._classify_noise_level(features, confidence)

        # Step 9: Generate reliability note
        reliability_note = self._generate_reliability_note(primary_regime, features)

        # Build output
        output = RegimeOutput(
            instrument=self.instrument,
            timestamp=datetime.now(timezone.utc).isoformat(),
            primary_regime=primary_regime,
            secondary_tag=secondary_tag,
            confidence=confidence,
            volatility_state=volatility_state,
            participation_state=participation_state,
            balance_state=balance_state,
            trend_quality=trend_quality,
            noise_level=noise_level,
            session_phase=features.session_phase,
            order_flow_reliability_note=reliability_note
        )

        logger.info(
            f"Regime classified: {primary_regime} ({secondary_tag or 'N/A'}) "
            f"- Confidence: {confidence}%"
        )

        return output

    def _calculate_balance_score(self, features: MarketFeatures) -> float:
        """
        Calculate balance score (0-100).

        High score indicates balanced/rotational market.

        Components:
        - High bar overlap (30%)
        - Low VWAP distance (20%)
        - Low directional efficiency (30%)
        - Low range expansion (20%)
        """
        # Bar overlap component (higher overlap = more balanced)
        overlap_score = min(features.bar_overlap_ratio / self.calibration.overlap_balanced_high, 1.0) * 30

        # VWAP distance component (closer to VWAP = more balanced)
        vwap_distance_normalized = 1.0 - min(features.vwap_distance / self.calibration.vwap_distance_threshold, 1.0)
        vwap_score = vwap_distance_normalized * 20

        # Directional efficiency component (lower efficiency = more balanced)
        efficiency_score = (1.0 - features.directional_efficiency) * 30

        # Range expansion component (normal range = more balanced)
        range_score = max(0, 20 - abs(features.historical_range_zscore) * 5)

        total_score = overlap_score + vwap_score + efficiency_score + range_score

        logger.debug(
            f"Balance score components: overlap={overlap_score:.1f}, "
            f"vwap={vwap_score:.1f}, efficiency={efficiency_score:.1f}, range={range_score:.1f}"
        )

        return min(100.0, total_score)

    def _calculate_imbalance_score(self, features: MarketFeatures) -> float:
        """
        Calculate imbalance score (0-100).

        High score indicates trending/initiative market.

        Components:
        - High directional efficiency (40%)
        - High VWAP slope magnitude (30%)
        - Low pullback depth (20%)
        - Range expansion (10%)
        """
        # Directional efficiency component
        efficiency_score = features.directional_efficiency * 40

        # VWAP slope component
        vwap_slope_score = min(abs(features.vwap_slope) * 100, 1.0) * 30

        # Pullback depth component (low pullbacks = clean trend)
        pullback_score = max(0, (2.0 - features.average_pullback_depth) / 2.0) * 20

        # Range expansion component
        range_score = max(0, min(features.historical_range_zscore, 2.0)) * 5

        total_score = efficiency_score + vwap_slope_score + pullback_score + range_score

        logger.debug(
            f"Imbalance score components: efficiency={efficiency_score:.1f}, "
            f"vwap_slope={vwap_slope_score:.1f}, pullback={pullback_score:.1f}, range={range_score:.1f}"
        )

        return min(100.0, total_score)

    def _classify_primary_regime(
        self,
        balance_score: float,
        imbalance_score: float,
        features: MarketFeatures
    ) -> Tuple[str, Optional[str]]:
        """
        Classify primary regime and secondary tag.

        Returns:
            Tuple of (primary_regime, secondary_tag)
        """
        # Check for event distortion first (would override other regimes)
        # For now, we don't have event detection, so skip this

        # Determine primary regime based on scores
        if balance_score > self.calibration.balance_threshold and balance_score > imbalance_score:
            # Balanced / Rotational
            primary = REGIME_BALANCED
            secondary = self._determine_balance_subtype(features)

        elif imbalance_score > self.calibration.imbalance_threshold and imbalance_score > balance_score:
            # Trend / Initiative
            primary = REGIME_TREND
            secondary = self._determine_trend_subtype(features)

        else:
            # Transition / Breakout Attempt
            primary = REGIME_TRANSITION
            secondary = None  # No subtypes for transition

        return primary, secondary

    def _determine_balance_subtype(self, features: MarketFeatures) -> str:
        """
        Determine subtype for Balanced regime.

        Returns: "tight", "normal", or "migrating"
        """
        # Tight balance: very high overlap, low ATR
        if features.bar_overlap_ratio > 0.70 and features.atr_14 < self.calibration.atr_baseline * 0.8:
            return TAG_TIGHT_BALANCE

        # Migrating balance: moderate overlap but directional VWAP slope
        elif abs(features.vwap_slope) > 0.001:
            return TAG_MIGRATING_BALANCE

        # Normal balance
        else:
            return TAG_NORMAL_BALANCE

    def _determine_trend_subtype(self, features: MarketFeatures) -> str:
        """
        Determine subtype for Trend regime.

        Returns: "clean", "grinding", or "liquidation"
        """
        # Liquidation: extreme efficiency + extreme volatility
        if features.directional_efficiency > 0.85 and features.historical_range_zscore > 2.0:
            return TAG_LIQUIDATION

        # Clean trend: high efficiency, good VWAP slope
        elif features.directional_efficiency > self.calibration.efficiency_trend_clean:
            return TAG_CLEAN_TREND

        # Grinding trend: moderate efficiency
        else:
            return TAG_GRINDING_TREND

    def _classify_volatility_state(self, features: MarketFeatures) -> str:
        """
        Classify volatility state.

        Returns: "compressing", "normal", "expanding", or "extreme"
        """
        # Check for extreme first
        if features.historical_range_zscore > self.calibration.atr_extreme_zscore:
            return VOLATILITY_EXTREME

        # Check volatility ratio and ATR slope
        if (features.volatility_ratio < self.calibration.volatility_compressing and
            features.atr_slope < 0):
            return VOLATILITY_COMPRESSING

        elif (features.volatility_ratio > self.calibration.volatility_expanding and
              features.atr_slope > 0):
            return VOLATILITY_EXPANDING

        else:
            return VOLATILITY_NORMAL

    def _classify_participation_state(self, features: MarketFeatures) -> str:
        """
        Classify participation state based on volume.

        Returns: "thin", "normal", or "heavy"
        """
        if features.volume_ratio < self.calibration.volume_thin_threshold:
            return PARTICIPATION_THIN

        elif features.volume_ratio > self.calibration.volume_heavy_threshold:
            return PARTICIPATION_HEAVY

        else:
            return PARTICIPATION_NORMAL

    def _classify_balance_state(
        self,
        balance_score: float,
        imbalance_score: float
    ) -> str:
        """
        Classify balance state.

        Returns: "balanced", "transitioning", or "imbalanced"
        """
        score_diff = abs(balance_score - imbalance_score)

        if balance_score > imbalance_score and score_diff > 15:
            return BALANCE_BALANCED

        elif imbalance_score > balance_score and score_diff > 15:
            return BALANCE_IMBALANCED

        else:
            return BALANCE_TRANSITIONING

    def _classify_trend_quality(
        self,
        features: MarketFeatures,
        primary_regime: str
    ) -> str:
        """
        Classify trend quality.

        Returns: "none", "weak", "clean", or "extreme"
        """
        # Only relevant for trend regimes
        if primary_regime != REGIME_TREND:
            if features.directional_efficiency > self.calibration.efficiency_trend_weak:
                return TREND_WEAK
            else:
                return TREND_NONE

        # Extreme trend
        if features.directional_efficiency > 0.85 and features.historical_range_zscore > 2.0:
            return TREND_EXTREME

        # Clean trend
        elif features.directional_efficiency > self.calibration.efficiency_trend_clean:
            return TREND_CLEAN

        # Weak trend
        elif features.directional_efficiency > self.calibration.efficiency_trend_weak:
            return TREND_WEAK

        else:
            return TREND_NONE

    def _calculate_confidence(
        self,
        balance_score: float,
        imbalance_score: float,
        features: MarketFeatures
    ) -> int:
        """
        Calculate confidence score (0-100).

        Higher confidence when:
        - Scores are clearly separated
        - Features agree
        - Normal session phase (not lunch, not extended)
        """
        # Base confidence from score separation
        score_separation = abs(balance_score - imbalance_score)

        if score_separation > self.calibration.confidence_high_separation:
            base_confidence = 80
        elif score_separation > self.calibration.confidence_medium_separation:
            base_confidence = 60
        else:
            base_confidence = 40

        # Adjust for feature agreement
        # High overlap + low efficiency = agreement for balance
        # Low overlap + high efficiency = agreement for trend
        if features.bar_overlap_ratio > 0.6 and features.directional_efficiency < 0.5:
            base_confidence += 10  # Features agree on balance
        elif features.bar_overlap_ratio < 0.4 and features.directional_efficiency > 0.7:
            base_confidence += 10  # Features agree on trend

        # Reduce confidence during transitional session phases
        if features.session_phase in ["lunch", "extended", "pre_open"]:
            base_confidence -= 10

        # Reduce confidence if conflicting volatility signals
        if features.volatility_ratio > 1.2 and features.atr_slope < 0:
            base_confidence -= 5

        return max(0, min(100, base_confidence))

    def _classify_noise_level(
        self,
        features: MarketFeatures,
        confidence: int
    ) -> str:
        """
        Classify noise level.

        Returns: "low", "medium", or "high"
        """
        # High confidence + normal volatility = low noise
        if confidence > 75 and features.historical_range_zscore < 1.5:
            return NOISE_LOW

        # Low confidence or extreme volatility = high noise
        elif confidence < 50 or features.historical_range_zscore > 2.5:
            return NOISE_HIGH

        else:
            return NOISE_MEDIUM

    def _generate_reliability_note(
        self,
        primary_regime: str,
        features: MarketFeatures
    ) -> str:
        """
        Generate human-readable reliability note.

        Returns guidance based on regime type.
        """
        # Get base note from regime type
        base_note = RELIABILITY_NOTES.get(primary_regime, "Conditions unclear; exercise caution.")

        # Add session-specific context if relevant
        if features.session_phase == "lunch":
            base_note += " Lunch session: lower liquidity increases noise."
        elif features.session_phase == "opening_range":
            base_note += " Opening range: wait for acceptance."
        elif features.session_phase == "power_hour":
            base_note += " Power hour: increased volatility and volume."

        return base_note
