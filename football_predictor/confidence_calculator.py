import math
from typing import Dict, Tuple, Any


class ConfidenceCalculator:
    """
    ConfidenceCalculator — Corrected, consistent, hybrid confidence model.

    Key features:
    - Separates and computes three related metrics:
      1) Outcome distribution sharpness (entropy-based) — how clear the winner is.
      2) Context reliability (data quality, predictability, injuries, rest, home adv) — how trustworthy inputs are.
      3) Outcome-specific confidences derived from each outcome's probability certainty combined with context reliability.

    - Does NOT use forced boosts or arbitrary caps that disconnect probabilities and confidence.
    - Returns:
        - outcome_confidences: dict of per-outcome confidences (0-100)
        - metrics: dict with distribution_sharpness_pct, context_reliability_pct, overall_confidence_pct and factors

    Interpretation guidance (recommended):
    - overall_confidence_pct = distribution_sharpness_pct * context_reliability_pct / 100
      This measures how much to *trust the most likely outcome*. Low when distribution is flat or data is poor.
    - outcome_confidences show per-outcome certainty (relative to other outcomes) scaled by data reliability.
    """

    def __init__(self, injury_analyzer=None, home_advantage=None, debug: bool = False):
        self.injury_analyzer = injury_analyzer
        self.home_advantage = home_advantage
        self.debug = debug

        # Interpret-able weights for context reliability (sum should be 1.0 but not required)
        self.confidence_weights = {
            'data_quality': 0.18,
            'predictability': 0.18,
            'injury_stability': 0.22,
            'rest_balance': 0.12,
            'home_advantage_consistency': 0.30
        }

    # ---------------- Public API -----------------------------------------
    def calculate_outcome_specific_confidence(
        self,
        probabilities: Dict[str, float],
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """Compute per-outcome confidences and context metrics.

        probabilities: {'home_win': p1, 'draw': p2, 'away_win': p3} (values in [0,1], sum ~1)

        Returns: (outcome_confidences, metrics)
          - outcome_confidences: dict outcome -> confidence % (0..100)
          - metrics: contains distribution_sharpness_pct, context_reliability_pct, overall_confidence_pct, factors
        """
        # 1) validate and normalize probabilities
        probs = {k: float(max(0.0, min(1.0, v))) for k, v in probabilities.items()}
        total = sum(probs.values())
        if total <= 0:
            # fallback to equal probs
            probs = {k: 1.0 / len(probs) for k in probs}
            total = 1.0
        probs = {k: v / total for k, v in probs.items()}

        # 2) compute entropy-based distribution sharpness (0..1)
        distribution_sharpness = self._distribution_sharpness(list(probs.values()))

        # 3) compute context reliability (0..1) and factors
        context_reliability, factors = self._context_reliability_and_factors(home_data, away_data, inputs)

        # 4) overall match-level confidence (0..100)
        overall_confidence_pct = round(distribution_sharpness * context_reliability * 100.0, 1)

        # 5) per-outcome confidence: map individual probability -> certainty and scale by context reliability
        outcome_confidences = {}
        for outcome, p in probs.items():
            certainty = self._probability_to_certainty(p)  # 0..1
            conf_pct = round(certainty * context_reliability * 100.0, 1)
            # draw uncertainty: draws are inherently more volatile — optional light penalty
            if outcome == 'draw':
                conf_pct *= 0.95
                conf_pct = round(conf_pct, 1)
            outcome_confidences[outcome] = conf_pct

        metrics = {
            'distribution_sharpness_pct': round(distribution_sharpness * 100.0, 1),
            'context_reliability_pct': round(context_reliability * 100.0, 1),
            'overall_confidence_pct': overall_confidence_pct,
            'factors': factors,
            'normalized_probabilities': probs
        }

        if self.debug:
            print("DEBUG: probs=", probs)
            print("DEBUG: distribution_sharpness=", metrics['distribution_sharpness_pct'])
            print("DEBUG: context_reliability=", metrics['context_reliability_pct'])
            print("DEBUG: overall_confidence=", metrics['overall_confidence_pct'])
            print("DEBUG: outcome_confidences=", outcome_confidences)

        return outcome_confidences, metrics

    # ---------------- Internal helpers ----------------------------------
    @staticmethod
    def _probability_to_certainty(p: float) -> float:
        """Map a single probability p to a certainty in [0,1] using normalized binary entropy.

        - p = 0.5 -> certainty 0 (max uncertainty)
        - p -> 0 or 1 -> certainty -> 1 (max certainty)
        """
        p = max(1e-9, min(1 - 1e-9, float(p)))
        entropy = -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
        # For a binary outcome, H_max = 1 bit. Normalized certainty = 1 - H(p)/1.
        certainty = 1.0 - entropy
        return max(0.0, min(1.0, certainty))

    @staticmethod
    def _distribution_sharpness(probs: list) -> float:
        """Compute sharpness of a distribution with n outcomes.

        Returns value in [0,1]: 0 = uniform (max uncertainty), 1 = one outcome has prob 1.
        Uses normalized Shannon entropy: sharpness = 1 - H(probs)/H_uniform
        """
        probs = [max(1e-12, min(1.0, float(p))) for p in probs]
        total = sum(probs)
        if total <= 0:
            return 0.0
        probs = [p / total for p in probs]

        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(len(probs))
        if max_entropy <= 0:
            return 1.0
        sharpness = 1.0 - (entropy / max_entropy)
        return max(0.0, min(1.0, sharpness))

    def _context_reliability_and_factors(self, home_data: Dict[str, Any], away_data: Dict[str, Any], inputs: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Compute a 0..1 reliability measure and return the component factors.

        Factors returned in 0..1 range (data_quality, predictability, injury_stability, rest_balance, home_adv_consistency)
        """
        factors: Dict[str, float] = {}

        # Data quality: at least 1 match; cap at 5 for full quality
        home_matches = max(1, int(home_data.get('matches_played', 5)))
        away_matches = max(1, int(away_data.get('matches_played', 5)))
        data_quality = min(home_matches / 5.0, away_matches / 5.0, 1.0)
        factors['data_quality'] = round(data_quality, 3)

        # Predictability: derived from team consistency
        home_cons = self._calculate_team_consistency(home_data)
        away_cons = self._calculate_team_consistency(away_data)
        predictability = (home_cons + away_cons) / 2.0
        factors['predictability'] = round(predictability, 3)

        # Injury stability: map injury labels to numbers
        injury_stability = self._calculate_injury_stability(inputs.get('home_injuries', 'None'), inputs.get('away_injuries', 'None'))
        factors['injury_stability'] = round(injury_stability, 3)

        # Rest balance
        rest_balance = self._calculate_rest_balance(inputs.get('home_rest', 0), inputs.get('away_rest', 0))
        factors['rest_balance'] = round(rest_balance, 3)

        # Home advantage consistency
        home_adv_consistency = self._calculate_home_advantage_consistency(home_data)
        factors['home_advantage_consistency'] = round(home_adv_consistency, 3)

        # Weighted combination -> reliability
        weights = self.confidence_weights
        reliability = (
            factors['data_quality'] * weights['data_quality'] +
            factors['predictability'] * weights['predictability'] +
            factors['injury_stability'] * weights['injury_stability'] +
            factors['rest_balance'] * weights['rest_balance'] +
            factors['home_advantage_consistency'] * weights['home_advantage_consistency']
        )
        reliability = max(0.0, min(1.0, reliability))

        return reliability, factors

    # ---------------- Small helpers -------------------------------------
    def _calculate_team_consistency(self, team_data: Dict[str, Any]) -> float:
        clean_pct = team_data.get('clean_sheet_pct', 45) / 100.0
        btts_pct = team_data.get('btts_pct', 50)
        btts_consistency = 1.0 - abs(btts_pct - 50.0) / 50.0
        val = (clean_pct + btts_consistency) / 2.0
        return max(0.0, min(1.0, val))

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

    # backward compatibility
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        context_confidence, factors = self._context_reliability_and_factors(home_data, away_data, inputs)
        return context_confidence, factors
