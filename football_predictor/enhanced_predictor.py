import math
from typing import Tuple, Dict, Any
import numpy as np
from scipy.stats import poisson


class EnhancedPredictor:
    """
    Enhanced predictor with COMPLETE SEPARATION of goal counting (pure xG) and win probabilities (blended).
    ELO only influences who wins, not how many goals are scored.
    """

    def __init__(self, data_integrator):
        self.data_integrator = data_integrator
        self.confidence_calculator = None  # Will be set by engine

    def _get_correct_team_data(self, team_key: str, is_home: bool) -> dict:
        """✅ FIXED: Get correct home/away team data based on context"""
        base_name = self.data_integrator._extract_base_name(team_key)
        
        if is_home:
            correct_key = f"{base_name} Home"
        else:
            correct_key = f"{base_name} Away"
        
        data = self.data_integrator.get_comprehensive_team_data(correct_key)
        
        # Fallback if specific home/away data not found
        if data is None or data.get('xg_total', 0) == 0:
            fallback_key = f"{base_name} Home"
            data = self.data_integrator.get_comprehensive_team_data(fallback_key)
            
        return data

    # -------------------------
    # Public prediction methods
    # -------------------------
    def predict_winner_enhanced(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,      # PER MATCH values
        away_xg: float,      # PER MATCH values
        home_xga: float,     # PER MATCH values
        away_xga: float,     # PER MATCH values
        home_injuries: str = "None",
        away_injuries: str = "None",
    ) -> Dict[str, Any]:
        """
        Returns blended probabilities for home/draw/away, confidence and expected goals.
        GOAL COUNTING: Pure xG-based (NO ELO influence)
        WIN PROBABILITIES: Blended Poisson + ELO
        """

        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", away_data.get("league", "Premier League"))

        print(f"🔍 ENHANCED PREDICTOR - Home: {home_data['base_name']} - Input xG: {home_xg:.2f}")
        print(f"🔍 ENHANCED PREDICTOR - Away: {away_data['base_name']} - Input xG: {away_xg:.2f}")

        # 🚨 CRITICAL FIX: COMPLETE SEPARATION OF CONCERNS

        # 1) GOAL COUNTING: Pure xG-based (NO ELO influence)
        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        print(f"🔍 PURE XG GOALS - Base: Home {home_goal_exp:.2f}, Away {away_goal_exp:.2f}")

        # 2) Apply injury adjustments to goal expectancies
        inj_adj = self._calculate_injury_adjustment(home_injuries, away_injuries)
        home_goal_exp *= inj_adj["home_attack"]
        away_goal_exp *= inj_adj["away_attack"]

        print(f"🔍 AFTER INJURIES - Home {home_goal_exp:.2f}, Away {away_goal_exp:.2f}")

        # 3) Apply league damping and reality checks
        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)
        home_goal_exp, away_goal_exp = self._apply_final_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)

        print(f"🔍 FINAL GOALS - Home {home_goal_exp:.2f}, Away {away_goal_exp:.2f}, Total: {home_goal_exp + away_goal_exp:.2f}")

        # 4) Poisson-based probabilities FROM PURE GOAL COUNTS
        poisson_home_win, poisson_draw, poisson_away_win = self._calculate_poisson_match_probs(
            home_goal_exp, away_goal_exp
        )

        # 5) ELO-based probabilities (completely separate calculation)
        elo_home_win, elo_draw, elo_away_win = self._calculate_elo_probabilities(home_data, away_data)

        # 6) 🚨 BLEND FOR WIN PROBABILITIES ONLY (goal counting is already pure xG)
        poisson_weight = 0.60  # Poisson dominates for win probabilities from actual performance
        elo_weight = 0.40     # ELO adjusts for team quality differences

        print(f"🔍 WIN PROB BLENDING - Poisson: {poisson_weight:.3f}, Elo: {elo_weight:.3f}")

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
        home_xg: float,      # PER MATCH values
        away_xg: float,      # PER MATCH values
        home_xga: float,     # PER MATCH values
        away_xga: float,     # PER MATCH values
    ) -> Dict[str, Any]:
        """
        Predicts over/under markets using PURE xG-based goal counting.
        """
        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", away_data.get("league", "Premier League"))

        # 🚨 PURE XG-BASED GOAL COUNTING (NO ELO)
        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        # Apply damping and reality checks
        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)
        home_goal_exp, away_goal_exp = self._apply_final_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)
        
        total_lambda = home_goal_exp + away_goal_exp

        print(f"🔍 OVER/UNDER - Pure xG total lambda: {total_lambda:.2f}")

        # Use integer cdf values: Over 2.5 = 1 - P(X <= 2)
        over_15 = 1.0 - poisson.cdf(1, total_lambda)
        over_25 = 1.0 - poisson.cdf(2, total_lambda)
        over_35 = 1.0 - poisson.cdf(3, total_lambda)

        # Defensive consistency adjustment
        defense_consistency = (home_data.get("clean_sheet_pct", 0) + away_data.get("clean_sheet_pct", 0)) / 200.0
        consistency_factor = 1.0 + (0.5 - defense_consistency) * 0.35
        over_25 *= consistency_factor
        over_25 = float(np.clip(over_25, 0.02, 0.98))
        over_15 = float(np.clip(over_15 * consistency_factor, 0.02, 0.995))
        over_35 = float(np.clip(over_35 * consistency_factor, 0.01, 0.95))

        # 🚨 CRITICAL FIX: Use the enhanced confidence calculator
        if self.confidence_calculator:
            confidence_15 = self.confidence_calculator.calculate_goal_market_confidence(total_lambda, over_15, "over_1.5")
            confidence_25 = self.confidence_calculator.calculate_goal_market_confidence(total_lambda, over_25, "over_2.5")
            confidence_35 = self.confidence_calculator.calculate_goal_market_confidence(total_lambda, over_35, "over_3.5")
        else:
            # Fallback to basic confidence
            confidence_15 = self._calculate_over_under_confidence(total_lambda, over_15, "over_1.5")
            confidence_25 = self._calculate_over_under_confidence(total_lambda, over_25, "over_2.5")
            confidence_35 = self._calculate_over_under_confidence(total_lambda, over_35, "over_3.5")

        # Use over_2.5 as the main confidence for backward compatibility
        confidence = confidence_25

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
        home_xg: float,      # PER MATCH values
        away_xg: float,      # PER MATCH values
        home_xga: float,     # PER MATCH values
        away_xga: float,     # PER MATCH values
    ) -> Dict[str, Any]:
        """
        Predict BTTS using PURE xG-based goal counting.
        """
        # ✅ FIXED: Get correct home/away team data
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)

        # 🚨 PURE XG-BASED GOAL COUNTING (NO ELO)
        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        # Apply reality checks
        home_goal_exp, away_goal_exp = self._apply_final_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)

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

        # 🚨 USE THE ENHANCED CONFIDENCE CALCULATOR
        if self.confidence_calculator and hasattr(self.confidence_calculator, 'calculate_btts_confidence'):
            confidence = self.confidence_calculator.calculate_btts_confidence(
                btts_prob, home_data, away_data, home_goal_exp, away_goal_exp
            )
        else:
            confidence = self._calculate_btts_confidence(home_data, away_data, home_goal_exp, away_goal_exp)

        return {
            "btts_yes": round(btts_prob, 4),
            "btts_no": round(1.0 - btts_prob, 4),
            "confidence": int(confidence),
            "key_factors": {"historical_btts": round(historical_avg, 3), "poisson_btts": round(poisson_btts, 3)},
        }

    # -------------------------
    # 🚨 CORE FIXED METHODS
    # -------------------------
    def _calculate_pure_xg_goal_expectancy(
        self,
        home_team: str,
        away_team: str,
        home_xg: float,      # PER MATCH values
        away_xg: float,      # PER MATCH values
        home_xga: float,     # PER MATCH values
        away_xga: float,     # PER MATCH values
    ) -> Tuple[float, float]:
        """
        🚨 PURE xG-based goal counting - NO ELO INFLUENCE
        HOME ADVANTAGE IS ALREADY IN THE xG DATA - DO NOT ADD AGAIN!
        """
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league_avg = self.data_integrator._get_league_avg_xg(home_data.get("league", "Premier League"))

        # Avoid division by zero
        league_avg = max(0.1, league_avg)
        
        # Pure xG calculation: team attack × opponent defense weakness
        home_goal_exp = home_xg * (away_xga / league_avg)
        away_goal_exp = away_xg * (home_xga / league_avg)

        # 🚨 CRITICAL FIX: COMPLETELY REMOVE HOME ADVANTAGE BOOST
        # home_adv = float(home_data.get("home_advantage", {}).get("goals_boost", 0.0))
        # home_goal_exp += home_adv  # ← THIS WAS CAUSING DOUBLE COUNTING

        # Ensure realistic minimums
        home_goal_exp = max(0.1, home_goal_exp)
        away_goal_exp = max(0.1, away_goal_exp)

        # Debug output to verify no double home advantage
        print(f"🔍 PURE XG - Home: {home_xg:.2f} → {home_goal_exp:.2f}, Away: {away_xg:.2f} → {away_goal_exp:.2f}")

        return home_goal_exp, away_goal_exp

    def _apply_final_reality_check(self, home_goal_exp: float, away_goal_exp: float, home_data: dict, away_data: dict) -> Tuple[float, float]:
        """
        🚨 FINAL REALITY CHECK: Ensure goal expectancies are realistic
        """
        total_goals = home_goal_exp + away_goal_exp
        
        # Premier League reality: matches rarely exceed 4.0 expected goals
        if total_goals > 4.0:
            print(f"🚨 FINAL REALITY CHECK: Total goals {total_goals:.2f} > 4.0. Applying correction.")
            damping = 4.0 / total_goals
            home_goal_exp *= damping
            away_goal_exp *= damping
        
        # Individual team limits based on team quality
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        
        # Elite teams can score more
        if home_tier == 'elite' and home_goal_exp > 2.5:
            home_goal_exp = min(home_goal_exp, 2.8)  # Allow elite home teams to 2.8
            print(f"🚨 FINAL REALITY CHECK: Elite home goals capped at 2.8")
        elif home_goal_exp > 2.2:
            home_goal_exp = min(home_goal_exp, 2.2)
            print(f"🚨 FINAL REALITY CHECK: Home goals capped at 2.2")
        
        if away_tier == 'elite' and away_goal_exp > 2.0:
            away_goal_exp = min(away_goal_exp, 2.3)  # Allow elite away teams to 2.3
            print(f"🚨 FINAL REALITY CHECK: Elite away goals capped at 2.3")
        elif away_goal_exp > 1.7:
            away_goal_exp = min(away_goal_exp, 1.7)
            print(f"🚨 FINAL REALITY CHECK: Away goals capped at 1.7")
        
        return home_goal_exp, away_goal_exp

    def _calculate_elo_probabilities(self, home_data: dict, away_data: dict) -> Tuple[float, float, float]:
        """
        ELO probabilities for WIN PROBABILITIES only (completely separate from goal counting)
        """
        home_elo = home_data["base_quality"].get("elo", 1600)
        away_elo = away_data["base_quality"].get("elo", 1600)

        # Home advantage in ELO points
        HOME_ADV_ELO = 80
        elo_diff = (home_elo - away_elo) + HOME_ADV_ELO

        # Home win raw using logistic-style conversion
        home_win_raw = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))

        # Draw probability increases when teams are close
        closeness = max(0.0, 1.0 - abs(elo_diff) / 600.0)
        base_draw = 0.20
        draw_prob = base_draw * (0.6 + 0.4 * closeness)

        # Split remaining mass between home and away
        remaining = 1.0 - draw_prob
        away_win_raw = 1.0 - home_win_raw
        denom = home_win_raw + away_win_raw
        if denom <= 0:
            home_win = remaining / 2
            away_win = remaining / 2
        else:
            home_win = remaining * (home_win_raw / denom)
            away_win = remaining * (away_win_raw / denom)

        return self._normalize_triple(home_win, draw_prob, away_win)

    def _apply_league_damping(self, home_goal_exp: float, away_goal_exp: float, league: str) -> Tuple[float, float]:
        """
        Soft damping for very-high total-goal estimates.
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

        # Only moderate damping when total > 3.2
        if total <= 3.2:
            return home_goal_exp, away_goal_exp

        excess = total - 3.2
        damping = base - 0.03 * min(excess, 3.0)
        damping = float(np.clip(damping, 0.75, 1.0))

        return home_goal_exp * damping, away_goal_exp * damping

    def _calculate_poisson_match_probs(self, home_lambda: float, away_lambda: float) -> Tuple[float, float, float]:
        """
        Compute probabilities of home win / draw / away win from pure goal counts.
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

        # Add tail mass for goals > max_goals
        home_tail = 1.0 - sum(home_pmf)
        away_tail = 1.0 - sum(away_pmf)
        tail_mass = home_tail * away_tail
        away_win += tail_mass * 0.5
        home_win += tail_mass * 0.5

        return self._normalize_triple(home_win, draw, away_win)

    def _calculate_injury_adjustment(self, home_injuries: str, away_injuries: str) -> Dict[str, float]:
        """
        Returns multipliers for attack and defense.
        """
        injury_weights = {
            "None": {"attack_mult": 1.00, "defense_mult": 1.00},
            "Minor": {"attack_mult": 0.97, "defense_mult": 0.96},
            "Moderate": {"attack_mult": 0.92, "defense_mult": 0.88},
            "Significant": {"attack_mult": 0.85, "defense_mult": 0.82},
            "Crisis": {"attack_mult": 0.75, "defense_mult": 0.72},
        }
        home_adj = injury_weights.get(home_injuries, injury_weights["None"])
        away_adj = injury_weights.get(away_injuries, injury_weights["None"])
        return {
            "home_attack": float(home_adj["attack_mult"]),
            "home_defense": float(home_adj["defense_mult"]),
            "away_attack": float(away_adj["attack_mult"]),
            "away_defense": float(away_adj["defense_mult"]),
        }

    # 🚨 UPDATED CONFIDENCE METHODS - Now use the enhanced calculator when available
    def _calculate_over_under_confidence(self, total_goals: float, probability: float, market_type: str = "over_2.5") -> float:
        """Fallback confidence calculation if enhanced calculator not available"""
        if market_type == "over_1.5":
            if probability >= 0.90: return 82
            elif probability >= 0.80: return 75
            elif probability >= 0.65: return 68
            elif probability >= 0.50: return 60
            else: return 50
        elif market_type == "over_2.5":
            if probability >= 0.80: return 78
            elif probability >= 0.70: return 72
            elif probability >= 0.55: return 65
            elif probability >= 0.40: return 58
            else: return 48
        else:  # over_3.5
            if probability >= 0.70: return 75
            elif probability >= 0.60: return 68
            elif probability >= 0.45: return 60
            elif probability >= 0.30: return 52
            else: return 42

    def _calculate_winner_confidence(self, home_prob: float, draw_prob: float, away_prob: float, home_data: dict, away_data: dict) -> float:
        """Calculate winner confidence - uses enhanced calculator when available"""
        # If we have the enhanced confidence calculator, use it properly
        if self.confidence_calculator:
            # Create a mock inputs dict for the confidence calculator
            mock_inputs = {
                'home_injuries': 'None',  # These would be set by the engine
                'away_injuries': 'None',
                'home_rest': 7,
                'away_rest': 7
            }
            
            probabilities = {
                'home_win': home_prob,
                'draw': draw_prob, 
                'away_win': away_prob
            }
            
            outcome_confidences, _ = self.confidence_calculator.calculate_outcome_specific_confidence(
                probabilities, home_data, away_data, mock_inputs
            )
            
            # Return the highest confidence among the outcomes
            return max(outcome_confidences.values())
        
        # Fallback: simple probability-based confidence
        max_prob = max(home_prob, draw_prob, away_prob)
        if max_prob > 0.60:
            return 75
        elif max_prob > 0.45:
            return 65
        elif max_prob > 0.35:
            return 55
        else:
            return 45

    def _calculate_btts_confidence(self, home_data: dict, away_data: dict, home_goal_exp: float, away_goal_exp: float) -> float:
        """
        Confidence for BTTS - LEGACY METHOD (used if enhanced calculator not available)
        """
        prob_home = 1.0 - poisson.cdf(0, home_goal_exp)
        prob_away = 1.0 - poisson.cdf(0, away_goal_exp)
        poisson_btts = prob_home * prob_away
        dist = abs(poisson_btts - 0.5)
        base = 45.0 + dist * 90.0
        hist = (home_data.get("btts_pct", 50) + away_data.get("btts_pct", 50)) / 2.0
        base += (abs(hist - 50.0) / 50.0) * 10.0
        return float(np.clip(base, 30.0, 95.0))

    # -------------------------
    # Utility & scoring helpers
    # -------------------------
    @staticmethod
    def _normalize_triple(a: float, b: float, c: float) -> Tuple[float, float, float]:
        """Normalize three positive numbers so they sum to 1."""
        vals = np.array([float(a), float(b), float(c)], dtype=float)
        vals = np.clip(vals, 0.0, None)
        s = vals.sum()
        if s <= 0:
            return 1 / 3, 1 / 3, 1 / 3
        return float(vals[0] / s), float(vals[1] / s), float(vals[2] / s)
