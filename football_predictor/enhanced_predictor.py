import math
from typing import Tuple, Dict, Any
import numpy as np
from scipy.stats import poisson


class EnhancedPredictor:
    """
    Enhanced predictor combining Poisson (xG) and ELO, with injury and league damping,
    and improved probability normalization and confidence scoring.

    Usage:
        predictor = EnhancedPredictor(data_integrator)
        out = predictor.predict_winner_enhanced(home_team, away_team, home_xg, away_xg, home_xga, away_xga, home_injuries, away_injuries)
    """

    def __init__(self, data_integrator):
        self.data_integrator = data_integrator

    def _get_correct_team_data(self, team_key: str, is_home: bool) -> dict:
        """✅ FIXED: Get correct home/away team data based on context"""
        base_name = self.data_integrator._extract_base_name(team_key)
        
        if is_home:
            correct_key = f"{base_name} Home"
        else:
            correct_key = f"{base_name} Away"
        
        # Debug info
        print(f"🔍 ENHANCED PREDICTOR: Requested '{team_key}', is_home={is_home}, Using '{correct_key}'")
        
        data = self.data_integrator.get_comprehensive_team_data(correct_key)
        
        # Fallback if specific home/away data not found
        if data is None or data.get('xg_total', 0) == 0:
            fallback_key = f"{base_name} Home"  # Default to home data
            print(f"⚠️  ENHANCED PREDICTOR: Using fallback data for {correct_key} -> {fallback_key}")
            data = self.data_integrator.get_comprehensive_team_data(fallback_key)
            
        return data

    # -------------------------
    # Public prediction methods
    # -------------------------
    def predict_winner_enhanced(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,
        away_xg: float,
        home_xga: float,
        away_xga: float,
        home_injuries: str = "None",
        away_injuries: str = "None",
    ) -> Dict[str, Any]:
        """
        Returns blended probabilities for home/draw/away, confidence and expected goals.
        """

        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", away_data.get("league", "Premier League"))

        # Debug team data
        print(f"🔍 ENHANCED PREDICTOR - Home: {home_data['base_name']} - xG: {home_data['xg_per_match']:.2f}, Location: {home_data.get('location', 'unknown')}")
        print(f"🔍 ENHANCED PREDICTOR - Away: {away_data['base_name']} - xG: {away_data['xg_per_match']:.2f}, Location: {away_data.get('location', 'unknown')}")

        # 1) compute base expected goals (apply quality + home advantage)
        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        # 2) apply injury adjustments to goal expectancies (attack multipliers)
        inj_adj = self._calculate_injury_adjustment(home_injuries, away_injuries)
        home_goal_exp *= inj_adj["home_attack"]
        away_goal_exp *= inj_adj["away_attack"]

        # 3) apply league soft damping if totals are high
        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)

        # 4) Poisson-based probabilities
        poisson_home_win, poisson_draw, poisson_away_win = self._calculate_poisson_match_probs(
            home_goal_exp, away_goal_exp
        )

        # 5) ELO-based probabilities
        elo_home_win, elo_draw, elo_away_win = self._calculate_elo_probabilities(home_data, away_data)

        # 6) Dynamic blending weights (more xG signal -> higher Poisson weight)
        poisson_weight = self._compute_dynamic_poisson_weight(home_xg, away_xg)
        
        # 🚨 FIXED: Apply quality-based adjustment to reduce Poisson weight for elite teams
        poisson_weight = self._compute_quality_adjusted_weight(home_data, away_data, poisson_weight)
        elo_weight = 1.0 - poisson_weight

        home_prob = poisson_weight * poisson_home_win + elo_weight * elo_home_win
        draw_prob = poisson_weight * poisson_draw + elo_weight * elo_draw
        away_prob = poisson_weight * poisson_away_win + elo_weight * elo_away_win

        # 7) Normalise to ensure numeric stability
        home_prob, draw_prob, away_prob = self._normalize_triple(home_prob, draw_prob, away_prob)

        # 8) Confidence and package result
        confidence = self._calculate_winner_confidence(home_prob, draw_prob, away_prob, home_data, away_data)
        result = {
            "home_win": round(home_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_prob, 4),
            "confidence": int(confidence),
            "expected_goals": {"home": round(home_goal_exp, 3), "away": round(away_goal_exp, 3)},
            "key_factors": {
                "poisson_weight": round(poisson_weight, 3),
                "elo_weight": round(elo_weight, 3),
                "elo_diff": home_data["base_quality"]["elo"] - away_data["base_quality"]["elo"],
                "injury_home": home_injuries,
                "injury_away": away_injuries,
                "league": league,
            },
        }
        return result

    def predict_over_under_enhanced(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,
        away_xg: float,
        home_xga: float,
        away_xga: float,
    ) -> Dict[str, Any]:
        """
        Predicts over/under markets (1.5, 2.5, 3.5). Returns probabilities, expected total, and confidence.
        """
        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", away_data.get("league", "Premier League"))

        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        # Apply soft damping and no injuries here (this function expects adjusted inputs if needed)
        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)
        total_lambda = home_goal_exp + away_goal_exp

        # Use integer cdf values: Over 2.5 = 1 - P(X <= 2)
        over_15 = 1.0 - poisson.cdf(1, total_lambda)
        over_25 = 1.0 - poisson.cdf(2, total_lambda)
        over_35 = 1.0 - poisson.cdf(3, total_lambda)

        # Defensive consistency adjustment (lower over-prob if both teams strong defensively)
        defense_consistency = (home_data.get("clean_sheet_pct", 0) + away_data.get("clean_sheet_pct", 0)) / 200.0
        consistency_factor = 1.0 + (0.5 - defense_consistency) * 0.35
        over_25 *= consistency_factor
        over_25 = float(np.clip(over_25, 0.02, 0.98))
        over_15 = float(np.clip(over_15 * consistency_factor, 0.02, 0.995))
        over_35 = float(np.clip(over_35 * consistency_factor, 0.01, 0.95))

        confidence = self._calculate_over_under_confidence(total_lambda, home_data, away_data)

        return {
            "over_1.5": round(over_15, 4),
            "over_2.5": round(over_25, 4),
            "over_3.5": round(over_35, 4),
            "under_1.5": round(1 - over_15, 4),
            "under_2.5": round(1 - over_25, 4),
            "under_3.5": round(1 - over_35, 4),
            "expected_total_goals": round(total_lambda, 3),
            "confidence": int(confidence),
            "key_factors": {"total_lambda": round(total_lambda, 3), "defense_consistency": round(defense_consistency, 3)},
        }

    def predict_btts_enhanced(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,
        away_xg: float,
        home_xga: float,
        away_xga: float,
    ) -> Dict[str, Any]:
        """
        Predict BTTS (both teams to score) using Poisson and historical BTTS blend.
        """
        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)

        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        prob_home_scores = 1.0 - poisson.cdf(0, home_goal_exp)
        prob_away_scores = 1.0 - poisson.cdf(0, away_goal_exp)
        poisson_btts = prob_home_scores * prob_away_scores

        historical_home = home_data.get("btts_pct", 50) / 100.0
        historical_away = away_data.get("btts_pct", 50) / 100.0
        historical_avg = (historical_home + historical_away) / 2.0

        # Dynamic blend: if xG signal is strong (both > 1.2) rely more on Poisson
        blend_weight_hist = 0.6 if (home_goal_exp < 1.2 or away_goal_exp < 1.2) else 0.4
        btts_prob = blend_weight_hist * historical_avg + (1 - blend_weight_hist) * poisson_btts
        btts_prob = float(np.clip(btts_prob, 0.05, 0.95))

        confidence = self._calculate_btts_confidence(home_data, away_data, home_goal_exp, away_goal_exp)

        return {
            "btts_yes": round(btts_prob, 4),
            "btts_no": round(1.0 - btts_prob, 4),
            "confidence": int(confidence),
            "key_factors": {"historical_btts": round(historical_avg, 3), "poisson_btts": round(poisson_btts, 3)},
        }

    # -------------------------
    # Internal helper methods
    # -------------------------
    def _calculate_elo_probabilities(self, home_data: dict, away_data: dict) -> Tuple[float, float, float]:
        """
        Converts ELO difference into a three-way (home/draw/away) probability.
        Uses logistic for win expectation and a simple calibrated draw factor that increases when teams are close.
        """
        home_elo = home_data["base_quality"].get("elo", 1600)
        away_elo = away_data["base_quality"].get("elo", 1600)

        # Home advantage in ELO points (calibrated)
        HOME_ADV_ELO = 80
        elo_diff = (home_elo - away_elo) + HOME_ADV_ELO

        # Home win raw using logistic-style conversion (Elo->win)
        home_win_raw = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))

        # Draw probability increases when teams are close
        closeness = max(0.0, 1.0 - abs(elo_diff) / 600.0)  # closeness in [0,1]
        base_draw = 0.20  # baseline draw probability
        draw_prob = base_draw * (0.6 + 0.4 * closeness)  # boost draw when close

        # Split remaining mass between home and away (proportional to raw)
        remaining = 1.0 - draw_prob
        away_win_raw = 1.0 - home_win_raw
        # Normalize raw pair to remaining
        denom = home_win_raw + away_win_raw
        if denom <= 0:
            home_win = remaining / 2
            away_win = remaining / 2
        else:
            home_win = remaining * (home_win_raw / denom)
            away_win = remaining * (away_win_raw / denom)

        # Safety clamp & normalize final triple
        home_win, draw_prob, away_win = self._normalize_triple(home_win, draw_prob, away_win)
        return home_win, draw_prob, away_win

    def _calculate_enhanced_goal_expectancy(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,
        away_xg: float,
        home_xga: float,
        away_xga: float,
    ) -> Tuple[float, float]:
        """
        Calculate quality-adjusted expected goals for each side based on integrated metrics.
        """
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league_avg = self.data_integrator._get_league_avg_xg(home_data.get("league", "Premier League"))

        # Avoid division by zero
        league_avg = max(0.1, league_avg)
        # Base adjustment: scale by opponent defensive xGA relative to league average, and by attack strength
        home_goal_exp = max(0.01, home_xg * (away_xga / league_avg) * float(home_data.get("attack_strength", 1.0)))
        away_goal_exp = max(0.01, away_xg * (home_xga / league_avg) * float(away_data.get("attack_strength", 1.0)))

        # Home advantage boost (small additive, calibrated to typical values)
        home_adv = float(home_data.get("home_advantage", {}).get("goals_boost", 0.0))
        home_goal_exp += home_adv

        return home_goal_exp, away_goal_exp

    def _apply_league_damping(self, home_goal_exp: float, away_goal_exp: float, league: str) -> Tuple[float, float]:
        """
        Soft damping for very-high total-goal estimates. Uses league-specific baseline but applies smoothly.
        """
        league_base = {
            "Premier League": 0.95,
            "La Liga": 0.92,
            "Bundesliga": 1.00,
            "Serie A": 0.90,
            "Ligue 1": 0.93,
            "RFPL": 0.88,
        }
        base = league_base.get(league, 0.95)
        total = home_goal_exp + away_goal_exp

        # Only moderate damping when total > 3.5; scale smoothly with total
        if total <= 3.5:
            return home_goal_exp, away_goal_exp

        # Soft damping factor that declines slowly with larger totals, but bounded
        excess = total - 3.5
        damping = base - 0.03 * min(excess, 3.0)  # reduce up to ~0.09 for +3 goals excess
        damping = float(np.clip(damping, 0.75, 1.0))

        return home_goal_exp * damping, away_goal_exp * damping

    def _calculate_poisson_match_probs(self, home_lambda: float, away_lambda: float) -> Tuple[float, float, float]:
        """
        Compute probabilities of home win / draw / away win by summing grid of Poisson pmfs.
        Reasonable goal limit is 0..8 for each side for completeness.
        """
        max_goals = 8
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        # Precompute pmfs for speed
        home_pmf = [poisson.pmf(i, home_lambda) for i in range(max_goals + 1)]
        away_pmf = [poisson.pmf(j, away_lambda) for j in range(max_goals + 1)]

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = home_pmf[i] * away_pmf[j]
                if i > j:
                    home_win += p
                elif i == j:
                    draw += p
                else:
                    away_win += p

        # Add tail mass for goals > max_goals (very small, approximate by remaining probability)
        home_tail = 1.0 - sum(home_pmf)
        away_tail = 1.0 - sum(away_pmf)
        # Approximate tail: if both tails exist, distribute small amount to high-scoring outcomes (counts minimally)
        tail_mass = home_tail * away_tail
        away_win += tail_mass * 0.5
        home_win += tail_mass * 0.5

        return self._normalize_triple(home_win, draw, away_win)

    def _calculate_injury_adjustment(self, home_injuries: str, away_injuries: str) -> Dict[str, float]:
        """
        Returns multipliers for attack and defense for home and away (multiplicative).
        Accepts qualitative labels: "None", "Minor", "Moderate", "Significant", "Crisis".
        """
        injury_weights = {
            "None": {"attack_mult": 1.00, "defense_mult": 1.00},
            "Minor": {"attack_mult": 0.97, "defense_mult": 0.96},
            "Moderate": {"attack_mult": 0.92, "defense_mult": 0.88},
            "Significant": {"attack_mult": 0.85, "defense_mult": 0.78},
            "Crisis": {"attack_mult": 0.75, "defense_mult": 0.65},
        }
        home_adj = injury_weights.get(home_injuries, injury_weights["None"])
        away_adj = injury_weights.get(away_injuries, injury_weights["None"])
        return {
            "home_attack": float(home_adj["attack_mult"]),
            "home_defense": float(home_adj["defense_mult"]),
            "away_attack": float(away_adj["attack_mult"]),
            "away_defense": float(away_adj["defense_mult"]),
        }

    # 🚨 FIXED: Critical weight adjustment methods
    @staticmethod
    def _compute_dynamic_poisson_weight(home_xg: float, away_xg: float) -> float:
        """
        🚨 FIXED: Produce a dynamic Poisson weight in [0.3, 0.65] - REDUCED RANGE
        Give more weight to Elo for quality differentiation
        """
        base = 0.45  # REDUCED from 0.55
        signal = min(home_xg, away_xg)
        # scale: signal 0.0 -> base -0.15, signal 1.5+ -> base +0.2 (REDUCED)
        w = base + (signal / 1.5) * 0.2  # REDUCED multiplier
        return float(np.clip(w, 0.3, 0.65))  # REDUCED range

    def _compute_quality_adjusted_weight(self, home_data: dict, away_data: dict, base_weight: float) -> float:
        """
        🚨 NEW: Reduce Poisson weight when there's a big quality difference
        """
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        home_elo = home_data['base_quality']['elo']
        away_elo = away_data['base_quality']['elo']
        
        # Reduce Poisson weight for elite vs strong/weak teams
        if (home_tier == 'elite' and away_tier != 'elite') or (away_tier == 'elite' and home_tier != 'elite'):
            print(f"🔍 QUALITY ADJUSTMENT: Elite team detected. Reducing Poisson weight by 30%")
            return base_weight * 0.7  # 30% reduction for elite teams
        
        # Additional reduction for very large ELO differences (>200)
        elo_diff = abs(home_elo - away_elo)
        if elo_diff > 200:
            reduction = min(0.2, (elo_diff - 200) / 1000)  # Up to 20% additional reduction
            print(f"🔍 ELO ADJUSTMENT: Large ELO difference {elo_diff}. Reducing Poisson weight by {reduction:.1%}")
            return base_weight * (1 - reduction)
        
        return base_weight

    # -------------------------
    # Utility & scoring helpers
    # -------------------------
    @staticmethod
    def _normalize_triple(a: float, b: float, c: float) -> Tuple[float, float, float]:
        """Normalize three positive numbers so they sum to 1. Avoid division by zero."""
        vals = np.array([float(a), float(b), float(c)], dtype=float)
        vals = np.clip(vals, 0.0, None)
        s = vals.sum()
        if s <= 0:
            return 1 / 3, 1 / 3, 1 / 3
        return float(vals[0] / s), float(vals[1] / s), float(vals[2] / s)

    def _calculate_winner_confidence(self, home_prob: float, draw_prob: float, away_prob: float, home_data: dict, away_data: dict) -> float:
        """
        Confidence scoring from spread, ELO difference, and sample size signals.
        Returns integer 0..95 (cap).
        """
        max_prob = max(home_prob, draw_prob, away_prob)
        diff = max_prob - sorted([home_prob, draw_prob, away_prob])[1]  # gap to next
        # Base confidence from max_prob and gap
        base = 40.0
        base += (max_prob - 0.33) * 90.0  # if max_prob 0.6 -> +24
        base += diff * 80.0  # reward wide gaps

        # Adjust for ELO gap (bigger gap -> more confidence)
        elo_gap = abs(home_data["base_quality"]["elo"] - away_data["base_quality"]["elo"])
        base += min(12.0, (elo_gap / 80.0))  # up to +12 points

        # Adjust for sample quality (matches played)
        matches_home = max(1, home_data.get("matches_played", 5))
        matches_away = max(1, away_data.get("matches_played", 5))
        sample_factor = min(1.2, math.log10(matches_home + matches_away + 1) / 1.0)
        base *= sample_factor

        # Bound and cap
        base = float(np.clip(base, 20.0, 95.0))
        return base

    @staticmethod
    def _calculate_over_under_confidence(total_goals: float, home_data: dict, away_data: dict) -> float:
        """
        Confidence that over/under predictions are stable. Based on distance from threshold
        and defensive consistency.
        """
        dist = abs(total_goals - 2.5)
        if dist >= 1.0:
            conf = 80.0
        elif dist >= 0.6:
            conf = 70.0
        elif dist >= 0.3:
            conf = 60.0
        else:
            conf = 50.0

        # Slight boost if both teams have many matches played
        matches = min(50, max(1, home_data.get("matches_played", 5) + away_data.get("matches_played", 5)))
        conf += min(10.0, math.log(matches) * 2.0)
        return float(np.clip(conf, 30.0, 95.0))

    @staticmethod
    def _calculate_btts_confidence(home_data: dict, away_data: dict, home_goal_exp: float, away_goal_exp: float) -> float:
        """
        Confidence for BTTS: based on how far the poisson estimate is from 50%-level and historical stability.
        """
        prob_home = 1.0 - poisson.cdf(0, home_goal_exp)
        prob_away = 1.0 - poisson.cdf(0, away_goal_exp)
        poisson_btts = prob_home * prob_away
        dist = abs(poisson_btts - 0.5)
        base = 45.0 + dist * 90.0  # large distance -> higher confidence
        # historical consistency (clean sheet % near 50% indicates variable)
        hist = (home_data.get("btts_pct", 50) + away_data.get("btts_pct", 50)) / 2.0
        base += (abs(hist - 50.0) / 50.0) * 10.0
        return float(np.clip(base, 30.0, 95.0))
