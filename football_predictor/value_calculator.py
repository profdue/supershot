import numpy as np

class ValueCalculator:
    def __init__(self):
        # MORE CONSERVATIVE thresholds
        self.value_thresholds = {
            "excellent": {"ev": 0.12, "value_ratio": 1.18},
            "good": {"ev": 0.06, "value_ratio": 1.10},
            "fair": {"ev": 0.02, "value_ratio": 1.03},
            "poor": {"ev": 0.00, "value_ratio": 1.00}
        }

    def calculate_true_value(self, probability, odds):
        """PROFESSIONAL value calculation with safe Kelly"""
        
        # Input validation
        if not (0 <= probability <= 1) or odds <= 1.0:
            return self._invalid_output(probability, odds, reason="invalid_input")

        # Expected Value
        ev = (probability * (odds - 1)) - (1 - probability)

        # SAFE Kelly Criterion (Fractional + Capped)
        if probability * odds > 1:
            raw_kelly = (probability * odds - 1) / (odds - 1)
            # Fractional Kelly (25%) with 2% maximum stake
            kelly_fraction = min(0.02, raw_kelly * 0.25)
        else:
            kelly_fraction = 0

        # Value Ratio
        value_ratio = probability * odds

        # Rating
        rating = self._get_value_rating(ev, value_ratio)

        return {
            "ev": round(ev, 4),
            "kelly_fraction": round(kelly_fraction, 4),  # NOW SAFE
            "value_ratio": round(value_ratio, 4),
            "rating": rating,
            "implied_prob": round(1 / odds, 4),
            "model_prob": round(probability, 4),
        }

    def calculate_value_bets(self, probabilities, odds):
        value_bets = {}
        for market, prob in probabilities.items():
            if market in odds:
                value_bets[market] = self.calculate_true_value(prob, odds[market])
            else:
                value_bets[market] = self._invalid_output(prob, None, reason="missing_odds")
        return value_bets

    def _get_value_rating(self, ev, value_ratio):
        for level in ["excellent", "good", "fair"]:
            if ev >= self.value_thresholds[level]["ev"] and value_ratio >= self.value_thresholds[level]["value_ratio"]:
                return level
        return "poor"

    def _invalid_output(self, probability, odds, reason="invalid"):
        return {
            "ev": -1,
            "kelly_fraction": 0,
            "value_ratio": 0,
            "rating": reason,
            "implied_prob": 0 if not odds or odds <= 0 else round(1 / odds, 4),
            "model_prob": round(probability, 4),
        }
