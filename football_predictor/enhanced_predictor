import numpy as np
from scipy.stats import poisson

class EnhancedPredictor:
    def __init__(self, data_integrator):
        self.data_integrator = data_integrator
        
    def predict_winner_enhanced(self, home_team, away_team, home_xg, away_xg, home_xga, away_xga, home_injuries, away_injuries):
        """Enhanced winner prediction using ELO blending and quality factors"""
        home_data = self.data_integrator.get_comprehensive_team_data(home_team)
        away_data = self.data_integrator.get_comprehensive_team_data(away_team)
        
        # Base goal expectancy
        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )
        
        # ELO-based probabilities (your Bayesian blending recommendation)
        elo_home_win, elo_draw, elo_away_win = self._calculate_elo_probabilities(home_data, away_data)
        
        # Poisson-based probabilities
        poisson_home_win, poisson_draw, poisson_away_win = self._calculate_enhanced_poisson_probabilities(
            home_goal_exp, away_goal_exp
        )
        
        # Bayesian blending: 60% Poisson, 40% ELO (adjustable weights)
        home_win_prob = 0.6 * poisson_home_win + 0.4 * elo_home_win
        draw_prob = 0.6 * poisson_draw + 0.4 * elo_draw
        away_win_prob = 0.6 * poisson_away_win + 0.4 * elo_away_win
        
        # Apply injury impacts
        injury_adjustment = self._calculate_injury_adjustment(home_injuries, away_injuries)
        home_win_prob *= injury_adjustment['home_attack']
        away_win_prob *= injury_adjustment['away_attack']
        
        # Normalize
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # Apply league damping factor (your recommendation)
        home_goal_exp, away_goal_exp = self._apply_league_damping(
            home_goal_exp, away_goal_exp, home_data['league']
        )
        
        confidence = self._calculate_winner_confidence(
            home_win_prob, draw_prob, away_win_prob, home_data, away_data
        )
        
        return {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
            'confidence': confidence,
            'expected_goals': {'home': home_goal_exp, 'away': away_goal_exp},
            'key_factors': {
                'poisson_weight': 0.6,
                'elo_weight': 0.4,
                'home_elo_advantage': home_data['base_quality']['elo'] - away_data['base_quality']['elo']
            }
        }
    
    def _calculate_elo_probabilities(self, home_data, away_data):
        """Calculate ELO-based probabilities"""
        home_elo = home_data['base_quality']['elo']
        away_elo = away_data['base_quality']['elo']
        
        # ELO difference with home advantage (typically +100 ELO for home)
        elo_diff = home_elo - away_elo + 100
        
        # Convert ELO difference to probabilities
        home_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        away_win_prob = 1 / (1 + 10 ** ((elo_diff) / 400))
        
        # Draw probability (simplified - can be more sophisticated)
        draw_prob = 1 - home_win_prob - away_win_prob
        if draw_prob < 0.1:
            draw_prob = 0.1
            # Re-normalize
            total = home_win_prob + away_win_prob + draw_prob
            home_win_prob /= total
            away_win_prob /= total
            draw_prob /= total
        
        return home_win_prob, draw_prob, away_win_prob
    
    def _calculate_enhanced_goal_expectancy(self, home_team, away_team, home_xg, away_xg, home_xga, away_xga):
        """Enhanced goal expectancy with quality adjustments"""
        home_data = self.data_integrator.get_comprehensive_team_data(home_team)
        away_data = self.data_integrator.get_comprehensive_team_data(away_team)
        
        league_avg_xg = self.data_integrator._get_league_avg_xg(home_data['league'])
        
        # Quality-adjusted goal expectancy
        home_goal_exp = home_xg * (away_xga / league_avg_xg) * home_data['attack_strength']
        away_goal_exp = away_xg * (home_xga / league_avg_xg) * away_data['attack_strength']
        
        # Apply home advantage from integrated data
        home_advantage = home_data['home_advantage']['goals_boost']
        home_goal_exp += home_advantage
        
        return max(0.1, home_goal_exp), max(0.1, away_goal_exp)
    
    def _apply_league_damping(self, home_goal_exp, away_goal_exp, league):
        """Apply league-specific damping to prevent unrealistic totals"""
        league_damping = {
            "Premier League": 0.85,
            "La Liga": 0.82,
            "Bundesliga": 0.90,  # Higher scoring league
            "Serie A": 0.80,
            "Ligue 1": 0.83,
            "RFPL": 0.78
        }
        
        damping = league_damping.get(league, 0.85)
        
        # Only apply damping if total goals > 4.0
        total_goals = home_goal_exp + away_goal_exp
        if total_goals > 4.0:
            home_goal_exp *= damping
            away_goal_exp *= damping
        
        return home_goal_exp, away_goal_exp
    
    def _calculate_enhanced_poisson_probabilities(self, home_lambda, away_lambda):
        """Calculate Poisson probabilities with goal limits"""
        home_win = 0
        draw = 0
        away_win = 0
        
        # Reasonable goal limits (your variance recommendation)
        for i in range(0, 7):  # home goals
            for j in range(0, 7):  # away goals
                prob = poisson.pmf(i, home_lambda) * poisson.pmf(j, away_lambda)
                if i > j:
                    home_win += prob
                elif i == j:
                    draw += prob
                else:
                    away_win += prob
        
        return home_win, draw, away_win
    
    def _calculate_injury_adjustment(self, home_injuries, away_injuries):
        """Calculate injury impacts"""
        injury_weights = {
            "None": {"attack_mult": 1.00, "defense_mult": 1.00},
            "Minor": {"attack_mult": 0.95, "defense_mult": 0.94},
            "Moderate": {"attack_mult": 0.90, "defense_mult": 0.85},
            "Significant": {"attack_mult": 0.82, "defense_mult": 0.72},
            "Crisis": {"attack_mult": 0.70, "defense_mult": 0.58}
        }
        
        home_adj = injury_weights.get(home_injuries, injury_weights["None"])
        away_adj = injury_weights.get(away_injuries, injury_weights["None"])
        
        return {
            'home_attack': home_adj['attack_mult'],
            'home_defense': home_adj['defense_mult'],
            'away_attack': away_adj['attack_mult'],
            'away_defense': away_adj['defense_mult']
        }
    
    def _calculate_winner_confidence(self, home_win, draw, away_win, home_data, away_data):
        """Enhanced confidence calculation"""
        max_prob = max(home_win, draw, away_win)
        
        # Base confidence from probability spread
        if max_prob > 0.6:
            base_confidence = 80 + (max_prob - 0.6) * 100
        elif max_prob > 0.45:
            base_confidence = 60 + (max_prob - 0.45) * 133
        else:
            base_confidence = 40 + max_prob * 44
        
        # Adjust for team quality consistency
        elo_diff = abs(home_data['base_quality']['elo'] - away_data['base_quality']['elo'])
        if elo_diff > 300:
            base_confidence += 10  # High confidence in clear favorites
        elif elo_diff < 100:
            base_confidence -= 5   # Lower confidence in close matches
        
        return min(95, base_confidence)

    # Add the other enhanced prediction methods (over/under, BTTS) with similar improvements
    def predict_over_under_enhanced(self, home_team, away_team, home_xg, away_xg, home_xga, away_xga):
        """Enhanced over/under prediction"""
        home_data = self.data_integrator.get_comprehensive_team_data(home_team)
        away_data = self.data_integrator.get_comprehensive_team_data(away_team)
        
        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )
        
        # Apply league damping
        home_goal_exp, away_goal_exp = self._apply_league_damping(
            home_goal_exp, away_goal_exp, home_data['league']
        )
        
        total_goals_lambda = home_goal_exp + away_goal_exp
        
        # Calculate probabilities with variance adjustment
        over_25_prob = 1 - poisson.cdf(2.5, total_goals_lambda)
        over_15_prob = 1 - poisson.cdf(1.5, total_goals_lambda)
        over_35_prob = 1 - poisson.cdf(3.5, total_goals_lambda)
        
        # Adjust based on defensive consistency
        defense_consistency = (home_data['clean_sheet_pct'] + away_data['clean_sheet_pct']) / 200
        consistency_adjustment = 1.0 + (0.5 - defense_consistency) * 0.4
        
        over_25_prob *= consistency_adjustment
        over_25_prob = max(0.05, min(0.95, over_25_prob))
        
        confidence = self._calculate_over_under_confidence(total_goals_lambda, home_data, away_data)
        
        return {
            'over_1.5': over_15_prob,
            'over_2.5': over_25_prob,
            'over_3.5': over_35_prob,
            'under_1.5': 1 - over_15_prob,
            'under_2.5': 1 - over_25_prob,
            'under_3.5': 1 - over_35_prob,
            'expected_total_goals': total_goals_lambda,
            'confidence': confidence,
            'key_factors': {
                'total_goals_lambda': total_goals_lambda,
                'defense_consistency': defense_consistency
            }
        }
    
    def predict_btts_enhanced(self, home_team, away_team, home_xg, away_xg, home_xga, away_xga):
        """Enhanced BTTS prediction"""
        home_data = self.data_integrator.get_comprehensive_team_data(home_team)
        away_data = self.data_integrator.get_comprehensive_team_data(away_team)
        
        home_goal_exp, away_goal_exp = self._calculate_enhanced_goal_expectancy(
            home_team, away_team, home_xg, away_xg, home_xga, away_xga
        )
        
        # Historical BTTS percentages
        home_btts_historical = home_data['btts_pct'] / 100
        away_btts_historical = away_data['btts_pct'] / 100
        
        # Poisson probability both teams score
        prob_home_scores = 1 - poisson.cdf(0, home_goal_exp)
        prob_away_scores = 1 - poisson.cdf(0, away_goal_exp)
        poisson_btts = prob_home_scores * prob_away_scores
        
        # Blend historical and Poisson (60% historical, 40% current form)
        btts_prob = 0.6 * ((home_btts_historical + away_btts_historical) / 2) + 0.4 * poisson_btts
        
        # Ensure reasonable bounds
        btts_prob = max(0.1, min(0.9, btts_prob))
        
        confidence = self._calculate_btts_confidence(home_data, away_data, home_goal_exp, away_goal_exp)
        
        return {
            'btts_yes': btts_prob,
            'btts_no': 1 - btts_prob,
            'confidence': confidence,
            'key_factors': {
                'historical_btts': (home_btts_historical + away_btts_historical) / 2,
                'poisson_btts': poisson_btts,
                'blend_weight': 0.6
            }
        }
    
    def _calculate_over_under_confidence(self, total_goals, home_data, away_data):
        """Confidence for over/under predictions"""
        distance_from_threshold = abs(total_goals - 2.5)
        
        if distance_from_threshold > 1.0:
            confidence = 80
        elif distance_from_threshold > 0.5:
            confidence = 70
        elif distance_from_threshold > 0.25:
            confidence = 60
        else:
            confidence = 50
        
        return min(95, confidence)
    
    def _calculate_btts_confidence(self, home_data, away_data, home_goal_exp, away_goal_exp):
        """Confidence for BTTS predictions"""
        # Based on how far from 50/50 and historical consistency
        prob_both_score = (1 - poisson.cdf(0, home_goal_exp)) * (1 - poisson.cdf(0, away_goal_exp))
        distance_from_50 = abs(prob_both_score - 0.5)
        
        base_confidence = 50 + distance_from_50 * 100
        
        return min(95, base_confidence)
