import math
from typing import Tuple, Dict, Any
import numpy as np
from scipy.stats import poisson

class WeightConfig:
    def __init__(self):
        self.base_weights = {
            'performance': 0.55,  # Poisson/xG based
            'quality': 0.45       # Elo based
        }
        self.league_weights = {
            "Premier League": {'performance': 0.60, 'quality': 0.40},
            "Serie A": {'performance': 0.52, 'quality': 0.48},
            "La Liga": {'performance': 0.56, 'quality': 0.44},
            "Bundesliga": {'performance': 0.62, 'quality': 0.38},
            "Ligue 1": {'performance': 0.54, 'quality': 0.46},
            "RFPL": {'performance': 0.50, 'quality': 0.50}
        }
    
    def get_weights(self, league, home_matches, away_matches, home_injuries, away_injuries):
        """Get dynamic weights based on context"""
        # Start with league-specific or base weights
        weights = self.league_weights.get(league, self.base_weights.copy())
        
        # Small sample protection
        min_matches = min(home_matches, away_matches)
        if min_matches < 6:
            weights = self._adjust_for_sample_size(weights, min_matches)
            
        # Injury disparity adjustment
        if self._has_significant_injury_gap(home_injuries, away_injuries):
            weights = self._adjust_for_injuries(weights)
            
        return self._normalize_weights(weights)
    
    def _adjust_for_sample_size(self, weights, min_matches):
        """More weight to quality when sample is small"""
        adjustment = (6 - min_matches) * 0.05  # 5% per missing match
        return {
            'performance': max(0.40, weights['performance'] - adjustment),
            'quality': min(0.60, weights['quality'] + adjustment)
        }
    
    def _has_significant_injury_gap(self, home_injuries, away_injuries):
        """Check if injury difference is significant (2+ levels)"""
        injury_levels = {"None": 0, "Minor": 1, "Moderate": 2, "Significant": 3, "Crisis": 4}
        gap = abs(injury_levels[home_injuries] - injury_levels[away_injuries])
        return gap >= 2
    
    def _adjust_for_injuries(self, weights):
        """Adjust weights when injury gap is significant"""
        return {
            'performance': weights['performance'] - 0.05,
            'quality': weights['quality'] + 0.05
        }
    
    def _normalize_weights(self, weights):
        """Ensure weights sum to 1.0"""
        total = weights['performance'] + weights['quality']
        return {
            'performance': weights['performance'] / total,
            'quality': weights['quality'] / total
        }

class EnhancedPredictor:
    def __init__(self, data_integrator):
        self.data_integrator = data_integrator
        self.weight_config = WeightConfig()

    def _get_correct_team_data(self, team_key: str, is_home: bool) -> dict:
        base_name = self.data_integrator._extract_base_name(team_key)
        correct_key = f"{base_name} Home" if is_home else f"{base_name} Away"
        data = self.data_integrator.get_comprehensive_team_data(correct_key)
        
        if data is None or data.get('xg_total', 0) == 0:
            fallback_key = f"{base_name} Home"
            data = self.data_integrator.get_comprehensive_team_data(fallback_key)
        return data

    def predict_winner_enhanced(self, home_team: str, away_team: str, home_xg: float, 
                              away_xg: float, home_xga: float, away_xga: float,
                              home_injuries: str = "None", away_injuries: str = "None") -> Dict[str, Any]:
        
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", "Premier League")

        # Get dynamic weights based on context
        weights = self.weight_config.get_weights(
            league,
            home_data['matches_played'],
            away_data['matches_played'], 
            home_injuries,
            away_injuries
        )

        # PURE xG-based goal counting (NO DOUBLE HOME ADVANTAGE)
        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        # Apply injury adjustments
        inj_adj = self._calculate_injury_adjustment(home_injuries, away_injuries)
        home_goal_exp *= inj_adj["home_attack"]
        away_goal_exp *= inj_adj["away_attack"]

        # Apply professional reality checks
        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)
        home_goal_exp, away_goal_exp = self._apply_professional_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)

        # Poisson probabilities
        poisson_home_win, poisson_draw, poisson_away_win = self._calculate_poisson_match_probs(home_goal_exp, away_goal_exp)

        # ELO probabilities  
        elo_home_win, elo_draw, elo_away_win = self._calculate_elo_probabilities(home_data, away_data)

        # Apply dynamic weights
        home_prob = weights['performance'] * poisson_home_win + weights['quality'] * elo_home_win
        draw_prob = weights['performance'] * poisson_draw + weights['quality'] * elo_draw
        away_prob = weights['performance'] * poisson_away_win + weights['quality'] * elo_away_win

        # Normalize
        home_prob, draw_prob, away_prob = self._normalize_triple(home_prob, draw_prob, away_prob)

        return {
            "home_win": round(home_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_prob, 4),
            "expected_goals": {"home": round(home_goal_exp, 3), "away": round(away_goal_exp, 3)},
            "key_factors": {
                "performance_weight": round(weights['performance'], 3),
                "quality_weight": round(weights['quality'], 3),
                "elo_diff": home_data["base_quality"]["elo"] - away_data["base_quality"]["elo"],
                "injury_home": home_injuries,
                "injury_away": away_injuries,
                "league": league,
                "sample_size_note": f"min_matches: {min(home_data['matches_played'], away_data['matches_played'])}"
            },
        }

    def predict_over_under_enhanced(self, home_team: str, away_team: str, home_xg: float, 
                                  away_xg: float, home_xga: float, away_xga: float) -> Dict[str, Any]:
        
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league = home_data.get("league", "Premier League")

        # Pure xG-based goals (NO DOUBLE HOME ADVANTAGE)
        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        home_goal_exp, away_goal_exp = self._apply_league_damping(home_goal_exp, away_goal_exp, league)
        home_goal_exp, away_goal_exp = self._apply_professional_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)
        
        total_lambda = home_goal_exp + away_goal_exp

        # ONLY THESE THREE MARKETS: Over 1.5, Over 2.5, Under 2.5
        over_15 = 1.0 - poisson.cdf(1, total_lambda)
        over_25 = 1.0 - poisson.cdf(2, total_lambda)
        under_25 = poisson.cdf(2, total_lambda)  # P(X ≤ 2)

        # Defense consistency adjustment
        defense_consistency = (home_data.get("clean_sheet_pct", 0) + away_data.get("clean_sheet_pct", 0)) / 200.0
        consistency_factor = 1.0 + (0.5 - defense_consistency) * 0.25  # Reduced impact
        
        over_25 = float(np.clip(over_25 * consistency_factor, 0.05, 0.95))
        over_15 = float(np.clip(over_15 * consistency_factor, 0.10, 0.99))
        under_25 = 1.0 - over_25  # Ensure consistency

        return {
            "over_1.5": round(over_15, 4),
            "over_2.5": round(over_25, 4),
            "under_2.5": round(under_25, 4),
            "expected_total_goals": round(total_lambda, 3),
            "key_factors": {
                "total_lambda": round(total_lambda, 3), 
                "defense_consistency": round(defense_consistency, 3)
            },
        }

    def predict_btts_enhanced(self, home_team: str, away_team: str, home_xg: float, 
                             away_xg: float, home_xga: float, away_xga: float) -> Dict[str, Any]:
        
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)

        home_goal_exp, away_goal_exp = self._calculate_pure_xg_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )

        home_goal_exp, away_goal_exp = self._apply_professional_reality_check(home_goal_exp, away_goal_exp, home_data, away_data)

        prob_home_scores = 1.0 - poisson.cdf(0, home_goal_exp)
        prob_away_scores = 1.0 - poisson.cdf(0, away_goal_exp)
        poisson_btts = prob_home_scores * prob_away_scores

        historical_home = home_data.get("btts_pct", 50) / 100.0
        historical_away = away_data.get("btts_pct", 50) / 100.0
        historical_avg = (historical_home + historical_away) / 2.0

        blend_weight_hist = 0.5  # More balanced blend
        btts_prob = blend_weight_hist * historical_avg + (1 - blend_weight_hist) * poisson_btts
        btts_prob = float(np.clip(btts_prob, 0.10, 0.90))

        return {
            "btts_yes": round(btts_prob, 4),
            "btts_no": round(1.0 - btts_prob, 4),
            "key_factors": {
                "historical_btts": round(historical_avg, 3), 
                "poisson_btts": round(poisson_btts, 3)
            },
        }

    def _calculate_pure_xg_goal_expectancy(self, home_team: str, away_team: str, 
                                         home_xg: float, away_xg: float, 
                                         home_xga: float, away_xga: float) -> Tuple[float, float]:
        
        home_data = self._get_correct_team_data(home_team, is_home=True)
        away_data = self._get_correct_team_data(away_team, is_home=False)
        league_avg = max(0.1, self.data_integrator._get_league_avg_xg(home_data.get("league", "Premier League")))

        # Pure xG calculation - NO MANUAL HOME BOOST (it's already in the data)
        home_goal_exp = home_xg * (away_xga / league_avg)
        away_goal_exp = away_xg * (home_xga / league_avg)

        # Ensure realistic minimums
        home_goal_exp = max(0.15, home_goal_exp)
        away_goal_exp = max(0.15, away_goal_exp)

        return home_goal_exp, away_goal_exp

    def _apply_professional_reality_check(self, home_goal_exp: float, away_goal_exp: float, 
                                        home_data: dict, away_data: dict) -> Tuple[float, float]:
        
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        total_goals = home_goal_exp + away_goal_exp
        
        # Premier League reality: matches rarely exceed 3.8 expected goals
        if total_goals > 3.8:
            damping = 3.8 / total_goals
            home_goal_exp *= damping
            away_goal_exp *= damping
        
        # Individual team limits
        if home_tier == 'elite' and home_goal_exp > 2.4:
            home_goal_exp = min(home_goal_exp, 2.4)
        elif home_goal_exp > 2.0:
            home_goal_exp = min(home_goal_exp, 2.0)
        
        if away_tier == 'elite' and away_goal_exp > 2.0:
            away_goal_exp = min(away_goal_exp, 2.0)
        elif away_goal_exp > 1.6:
            away_goal_exp = min(away_goal_exp, 1.6)
        
        return home_goal_exp, away_goal_exp

    def _calculate_elo_probabilities(self, home_data: dict, away_data: dict) -> Tuple[float, float, float]:
        home_elo = home_data["base_quality"].get("elo", 1600)
        away_elo = away_data["base_quality"].get("elo", 1600)

        HOME_ADV_ELO = 70  # Reduced from 80
        elo_diff = (home_elo - away_elo) + HOME_ADV_ELO

        home_win_raw = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))

        # Enhanced draw probability
        closeness = max(0.0, 1.0 - abs(elo_diff) / 800.0)  # More draws for closer teams
        base_draw = 0.26  # Increased base draw probability
        draw_prob = base_draw * (0.7 + 0.3 * closeness)

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
        league_base = {
            "Premier League": 0.92,
            "La Liga": 0.90,
            "Bundesliga": 0.95,
            "Serie A": 0.88,
            "Ligue 1": 0.90,
            "RFPL": 0.85,
        }
        base = league_base.get(league, 0.90)
        total = home_goal_exp + away_goal_exp

        if total <= 3.0:  # More aggressive damping
            return home_goal_exp, away_goal_exp

        excess = total - 3.0
        damping = base - 0.04 * min(excess, 3.0)  # Stronger damping
        damping = float(np.clip(damping, 0.70, 1.0))

        return home_goal_exp * damping, away_goal_exp * damping

    def _calculate_poisson_match_probs(self, home_lambda: float, away_lambda: float) -> Tuple[float, float, float]:
        max_goals = 8
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

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

        home_tail = 1.0 - sum(home_pmf)
        away_tail = 1.0 - sum(away_pmf)
        tail_mass = home_tail * away_tail
        away_win += tail_mass * 0.5
        home_win += tail_mass * 0.5

        return self._normalize_triple(home_win, draw, away_win)

    def _calculate_injury_adjustment(self, home_injuries: str, away_injuries: str) -> Dict[str, float]:
        # CONSERVATIVE injury impacts (6-12% vs 10-28%)
        injury_weights = {
            "None": {"attack_mult": 1.00, "defense_mult": 1.00},
            "Minor": {"attack_mult": 0.97, "defense_mult": 0.96},
            "Moderate": {"attack_mult": 0.94, "defense_mult": 0.92},  # 6-8% impact
            "Significant": {"attack_mult": 0.90, "defense_mult": 0.88},  # 10-12% impact
            "Crisis": {"attack_mult": 0.85, "defense_mult": 0.82},  # 15-18% impact
        }
        home_adj = injury_weights.get(home_injuries, injury_weights["None"])
        away_adj = injury_weights.get(away_injuries, injury_weights["None"])
        return {
            "home_attack": float(home_adj["attack_mult"]),
            "home_defense": float(home_adj["defense_mult"]),
            "away_attack": float(away_adj["attack_mult"]),
            "away_defense": float(away_adj["defense_mult"]),
        }

    @staticmethod
    def _normalize_triple(a: float, b: float, c: float) -> Tuple[float, float, float]:
        vals = np.array([float(a), float(b), float(c)], dtype=float)
        vals = np.clip(vals, 0.0, None)
        s = vals.sum()
        if s <= 0:
            return 1 / 3, 1 / 3, 1 / 3
        return float(vals[0] / s), float(vals[1] / s), float(vals[2] / s)
