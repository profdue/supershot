class ValueCalculator:
    def __init__(self):
        # Thresholds can later be calibrated empirically (based on ROI history)
        self.value_thresholds = {
            "excellent": {"ev": 0.08, "value_ratio": 1.12},
            "good": {"ev": 0.04, "value_ratio": 1.06},
            "fair": {"ev": 0.01, "value_ratio": 1.02},
            "poor": {"ev": 0.00, "value_ratio": 1.00}
        }

    # ---------------------- CORE CALCULATION ---------------------- #
    def calculate_true_value(self, probability, odds):
        """Calculate true value, expected value, and Kelly fraction for a single market."""

        # --- Input validation --- #
        if not (0 <= probability <= 1):
            return self._invalid_output(probability, odds, reason="invalid_probability")
        if odds <= 1.0:
            return self._invalid_output(probability, odds, reason="invalid_odds")

        # --- Expected Value (EV) --- #
        ev = (probability * (odds - 1)) - (1 - probability)

        # --- Kelly Criterion --- #
        if probability * odds > 1:
            kelly_fraction = (probability * odds - 1) / (odds - 1)
        else:
            kelly_fraction = 0

        # --- Value Ratio (simple heuristic indicator) --- #
        value_ratio = probability * odds

        # --- Rating logic (threshold-based) --- #
        rating = self._get_value_rating(ev, value_ratio)

        # --- Final dictionary output --- #
        return {
            "ev": round(ev, 4),
            "kelly_fraction": round(max(0, kelly_fraction), 4),
            "value_ratio": round(value_ratio, 4),
            "rating": rating,
            "implied_prob": round(1 / odds, 4),
            "model_prob": round(probability, 4),
        }

    # ---------------------- BULK CALCULATION ---------------------- #
    def calculate_value_bets(self, probabilities, odds):
        """
        Calculate value metrics for all markets in parallel.
        Automatically handles missing markets and invalid data gracefully.
        """
        value_bets = {}

        for market, prob in probabilities.items():
            if market not in odds:
                # Missing odds for this market
                value_bets[market] = self._invalid_output(prob, None, reason="missing_odds")
            else:
                value_bets[market] = self.calculate_true_value(prob, odds[market])

        return value_bets

    # ---------------------- INTERNAL HELPERS ---------------------- #
    def _get_value_rating(self, ev, value_ratio):
        """Return qualitative rating based on EV and value ratio thresholds."""
        for level in ["excellent", "good", "fair"]:
            if ev >= self.value_thresholds[level]["ev"] and value_ratio >= self.value_thresholds[level]["value_ratio"]:
                return level
        return "poor"

    def _invalid_output(self, probability, odds, reason="invalid"):
        """Standardized invalid output for consistency."""
        return {
            "ev": -1,
            "kelly_fraction": 0,
            "value_ratio": 0,
            "rating": reason,
            "implied_prob": 0 if not odds or odds <= 0 else round(1 / odds, 4),
            "model_prob": round(probability, 4),
        }
