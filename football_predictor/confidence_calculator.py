import math
from typing import Dict, Tuple, Any


class ConfidenceCalculator:
    """
    Revised ConfidenceCalculator

    Key changes (vs previous implementation):
    - Confidence is now a measure of *certainty* about a probability estimate (not a re-scaling
      of the probability itself).
    - Uses information-theoretic base (binary entropy) to map probability -> base certainty.
    - Applies a single, interpretable reliability factor derived from context (data quality,
      predictability, injuries, rest, home-adv consistency) instead of additive "boosts".
    - Removes forced "predicted winner must have highest confidence" rule.
    - Keeps separate logic for BTTS/goal market confidence but uses consistent scaling and
      context-adjustment.
    - API-compatible: calculate_outcome_specific_confidence returns a dict of confidences
      and the context factors (same as before).
    """

    def __init__(self, injury_analyzer=None, home_advantage=None, debug: bool = False):
        self.injury_analyzer = injury_analyzer
        self.home_advantage = home_advantage
        self.debug = debug

        # Confidence weights (interpretable and tunable)
        self.confidence_weights = {
            'data_quality': 0.18,
            'predictability': 0.18,
            'injury_stability': 0.22,
            'rest_balance': 0.12,
            'home_advantage_consistency': 0.30
        }

    # --------- Public API -------------------------------------------------
    def calculate_outcome_specific_confidence(
        self,
        probabilities: Dict[str, float],
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Return outcome-specific confidence percentages (0-100) and context factors.

        probabilities expects keys: 'home_win', 'draw', 'away_win' with values in [0,1].
        """
        # Compute contextual reliability and factors (0..1 scale for factors)
        context_confidence_pct, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        context_reliability = context_confidence_pct / 100.0  # convert to 0..1

        if self.debug:
            print(f"🔍 CONTEXT CONFIDENCE: {context_confidence_pct:.1f}%")

        # Convert each raw probability -> base certainty via entropy mapping
        base_certs = {
            k: self._probability_to_certainty(v)
            for k, v in probabilities.items()
        }

        if self.debug:
            for k, v in probabilities.items():
                print(f"🔍 BASE: {k} prob={v:.3f} -> certainty={base_certs[k]:.2f}")

        # Combine base certainty with context reliability
        # Use a weighted mix: final = alpha * base_cert + (1-alpha) * (context_reliability*100)
        # alpha controls how much the probability itself drives the confidence. 0.6 is a reasonable default.
        alpha = 0.6

        outcome_confidences = {}
        for outcome, base_cert in base_certs.items():
            # Draws tend to be less certain even at the same probability; apply draw_penalty
            draw_penalty = 0.85 if outcome == 'draw' else 1.0

            final = alpha * base_cert * 100.0 * draw_penalty + (1 - alpha) * (context_reliability * 100.0)

            # Small adjustments for extremely low information (very small sample)
            # If data_quality factor is low (<0.4), reduce confidence further
            data_quality = factors.get('data_quality', 1.0)
            if data_quality < 0.4:
                final *= 0.85

            # Boundaries: allow 5..95 to avoid hard caps used previously; output is 0..100 but
            # we keep a conservative floor/ceiling.
            final = max(5.0, min(95.0, final))

            outcome_confidences[outcome] = round(final, 1)

        if self.debug:
            print(f"🔍 FINAL CONFIDENCES: {outcome_confidences}")

        return outcome_confidences, factors

    # --------- Helpers ----------------------------------------------------
    @staticmethod
    def _probability_to_certainty(p: float) -> float:
        """Map a probability p in [0,1] to a certainty score in [0,1].

        Uses normalized binary entropy: certainty = 1 - H(p)/H(0.5), where
        H(p) = -p log2 p - (1-p) log2 (1-p); H(0.5) = 1 bit. The result is 0 at p=0.5
        (maximum uncertainty) and approaches 1 as p->0 or p->1.
        """
        # clamp p away from 0/1 for numerical stability
        p = max(1e-9, min(1 - 1e-9, float(p)))
        entropy = -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
        # H(0.5) = 1.0, so normalized certainty is 1 - entropy
        certainty = 1.0 - entropy
        # certainty in [0,1]
        return max(0.0, min(1.0, certainty))

    def calculate_goal_market_confidence(self, total_goals: float, probability: float, market_type: str = "over_2.5") -> float:
        """Return a 0..100 confidence for goal markets using consistent scaling + context.

        This implementation preserves the user's previous thresholds but returns values
        that are comparable to the outcome-specific confidences and keeps a consistent
        floor/ceiling.
        """
        # Base mapping by thresholds (kept similar to the old logic but returned as 0..100)
        prob = probability
        if market_type == "over_1.5":
            if prob >= 0.90:
                conf = 82
            elif prob >= 0.80:
                conf = 75
            elif prob >= 0.65:
                conf = 68
            elif prob >= 0.50:
                conf = 60
            else:
                conf = 50
        elif market_type == "over_2.5":
            if prob >= 0.80:
                conf = 78
            elif prob >= 0.70:
                conf = 72
            elif prob >= 0.55:
                conf = 65
            elif prob >= 0.40:
                conf = 58
            else:
                conf = 48
        else:  # over_3.5
            if prob >= 0.70:
                conf = 75
            elif prob >= 0.60:
                conf = 68
            elif prob >= 0.45:
                conf = 60
            elif prob >= 0.30:
                conf = 52
            else:
                conf = 42

        # small adjustment by total goals expectation
        if total_goals > 4.0 and prob > 0.6:
            conf += 3
        elif total_goals < 2.0 and prob < 0.4:
            conf += 2

        # enforce conservative bounds
        conf = max(10, min(95, conf))
        return round(conf, 1)

    def calculate_btts_confidence(self, btts_probability: float, home_data: Dict[str, Any], away_data: Dict[str, Any], home_goal_exp: float = None, away_goal_exp: float = None) -> float:
        """Return BTTS confidence (0..100).

        Uses distance-from-0.5 signal strength but applies historical consistency and
        context reliability.
        """
        p = float(btts_probability)
        distance = abs(p - 0.5)

        # signal mapping (0..1)
        if distance > 0.25:
            base = 0.90
        elif distance > 0.15:
            base = 0.80
        elif distance > 0.08:
            base = 0.65
        elif distance > 0.03:
            base = 0.50
        else:
            base = 0.35

        # historical consistency adjustment
        hist_home = home_data.get("btts_pct", 50) / 100.0
        hist_away = away_data.get("btts_pct", 50) / 100.0
        hist_avg = (hist_home + hist_away) / 2.0
        if abs(hist_avg - p) > 0.2:
            base *= 0.85

        # context reliability
        # re-use context computation to get a reliability factor
        # (note: this is slightly heavier but keeps consistency)
        _, factors = self._calculate_context_confidence(home_data, away_data, {
            'home_injuries': 'None', 'away_injuries': 'None', 'home_rest': 0, 'away_rest': 0
        })
        reliability = factors.get('data_quality', 1.0) * 0.6 + factors.get('predictability', 1.0) * 0.4

        conf = base * reliability * 100.0
        conf = max(10.0, min(95.0, conf))
        if self.debug:
            print(f"🔍 BTTS: p={p:.2f} dist={distance:.3f} base={base:.2f} hist_avg={hist_avg:.2f} reliability={reliability:.2f} -> conf={conf:.1f}")
        return round(conf, 1)

    # --------- Context / internal calculators -----------------------------
    def _calculate_context_confidence(self, home_data: Dict[str, Any], away_data: Dict[str, Any], inputs: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate overall match context confidence (percentage) and return component factors.

        Returned factors are in 0..1
        """
        factors: Dict[str, float] = {}

        home_matches = max(1, int(home_data.get('matches_played', 5)))
        away_matches = max(1, int(away_data.get('matches_played', 5)))
        data_quality = min(home_matches / 5.0, away_matches / 5.0, 1.0)
        factors['data_quality'] = data_quality

        home_consistency = self._calculate_team_consistency(home_data)
        away_consistency = self._calculate_team_consistency(away_data)
        predictability = (home_consistency + away_consistency) / 2.0
        factors['predictability'] = predictability

        injury_stability = self._calculate_injury_stability(inputs.get('home_injuries', 'None'), inputs.get('away_injuries', 'None'))
        factors['injury_stability'] = injury_stability

        rest_balance = self._calculate_rest_balance(inputs.get('home_rest', 0), inputs.get('away_rest', 0))
        factors['rest_balance'] = rest_balance

        home_adv_consistency = self._calculate_home_advantage_consistency(home_data)
        factors['home_advantage_consistency'] = home_adv_consistency

        # Weighted context confidence (0..1) converted to percent
        ctx = (
            factors['data_quality'] * self.confidence_weights['data_quality'] +
            factors['predictability'] * self.confidence_weights['predictability'] +
            factors['injury_stability'] * self.confidence_weights['injury_stability'] +
            factors['rest_balance'] * self.confidence_weights['rest_balance'] +
            factors['home_advantage_consistency'] * self.confidence_weights['home_advantage_consistency']
        )

        context_confidence_pct = max(10.0, min(95.0, ctx * 100.0))
        return context_confidence_pct, factors

    def _calculate_team_consistency(self, team_data: Dict[str, Any]) -> float:
        clean_pct = team_data.get('clean_sheet_pct', 45) / 100.0
        btts_pct = team_data.get('btts_pct', 50)
        btts_consistency = 1.0 - abs(btts_pct - 50.0) / 50.0
        return max(0.0, min(1.0, (clean_pct + btts_consistency) / 2.0))

    def _calculate_injury_stability(self, home_injuries: str, away_injuries: str) -> float:
        impact = {
            "None": 1.0, "Minor": 0.9, "Moderate": 0.75,
            "Significant": 0.6, "Crisis": 0.4
        }
        home_stab = impact.get(home_injuries, 0.8)
        away_stab = impact.get(away_injuries, 0.8)
        return (home_stab + away_stab) / 2.0

    def _calculate_rest_balance(self, home_rest: int, away_rest: int) -> float:
        rest_diff = abs(int(home_rest) - int(away_rest))
        if rest_diff <= 2:
            return 1.0
        elif rest_diff <= 4:
            return 0.8
        else:
            return 0.6

    def _calculate_home_advantage_consistency(self, home_data: Dict[str, Any]) -> float:
        home_adv = home_data.get('home_advantage', {})
        strength = home_adv.get('strength', 'moderate') if isinstance(home_adv, dict) else home_adv
        if strength == 'strong':
            return 0.95
        elif strength == 'moderate':
            return 0.85
        else:
            return 0.7

    # backward compatible helper
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        return context_confidence, factors
