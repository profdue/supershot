# football_predictor/engine.py
import logging
import numpy as np
from scipy.stats import poisson
from typing import Dict, Any, Tuple, List

from .data_loader import DataLoader
from .team_quality import TeamQuality
from .injury_module import InjuryModule
from .home_advantage import HomeAdvantage
from .config import LEAGUE_AVERAGES, FATIGUE_MULTIPLIERS

logger = logging.getLogger(__name__)

class ProfessionalPredictionEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_loader = DataLoader(data_dir)
        self.team_quality = TeamQuality(self.data_loader)
        self.injury_module = InjuryModule(self.team_quality)
        self.home_advantage = HomeAdvantage(self.data_loader, self.team_quality)
        
        logger.info("Professional Prediction Engine initialized")
    
    def get_team_base_name(self, team_name: str) -> str:
        """Extract base team name without Home/Away suffix"""
        if " Home" in team_name:
            return team_name.replace(" Home", "")
        elif " Away" in team_name:
            return team_name.replace(" Away", "")
        return team_name
    
    def get_team_data(self, team_name: str) -> Dict[str, Any]:
        """Get team data from database"""
        return self.data_loader.get_team_data(team_name)
    
    def get_available_leagues(self) -> List[str]:
        """Get list of available leagues"""
        return self.data_loader.get_available_leagues()
    
    def get_teams_by_league(self, league: str, team_type: str = "all") -> List[str]:
        """Get teams in a specific league"""
        return self.data_loader.get_teams_by_league(league, team_type)
    
    def validate_team_selection(self, home_team: str, away_team: str) -> List[str]:
        """Validate that teams are from the same base team and league"""
        home_base = self.get_team_base_name(home_team)
        away_base = self.get_team_base_name(away_team)
        home_league = self.get_team_data(home_team)["league"]
        away_league = self.get_team_data(away_team)["league"]
        
        errors = []
        if home_base == away_base:
            errors.append("Cannot select the same team for both home and away")
        if home_league != away_league:
            errors.append(f"Teams must be from the same league. {home_base} is in {home_league}, {away_base} is in {away_league}")
        
        return errors
    
    def apply_fatigue_modifiers(self, base_value: float, rest_days: int, form_trend: float) -> float:
        """Apply fatigue and form modifiers"""
        fatigue_mult = FATIGUE_MULTIPLIERS.get(rest_days, 1.0)
        form_mult = 1 + (form_trend * 0.2)
        return base_value * fatigue_mult * form_mult
    
    def calculate_goal_expectancy(self, home_xg: float, home_xga: float, 
                                away_xg: float, away_xga: float, 
                                home_team: str, away_team: str, 
                                league: str) -> Tuple[float, float]:
        """Calculate proper goal expectancy with opponent-quality aware home advantage"""
        league_avg = LEAGUE_AVERAGES.get(league, {"xg": 1.4, "xga": 1.4})
        
        # Get quality-adjusted home advantage
        home_boost, away_penalty = self.home_advantage.get_home_advantage_boost(home_team, away_team)
        
        # Normalization
        home_goal_exp = home_xg * (away_xga / league_avg["xga"]) ** 0.8
        away_goal_exp = away_xg * (home_xga / league_avg["xga"]) ** 0.8
        
        # Apply quality-adjusted advantages
        home_goal_exp += home_boost
        away_goal_exp += away_penalty
        
        return max(0.1, home_goal_exp), max(0.1, away_goal_exp)
    
    def calculate_poisson_probabilities(self, home_goal_exp: float, away_goal_exp: float) -> Dict[str, float]:
        """Calculate probabilities using Poisson distribution"""
        max_goals = 8
        
        home_probs = [poisson.pmf(i, home_goal_exp) for i in range(max_goals)]
        away_probs = [poisson.pmf(i, away_goal_exp) for i in range(max_goals)]
        
        home_win = 0
        draw = 0
        away_win = 0
        
        for i in range(max_goals):
            for j in range(max_goals):
                prob = home_probs[i] * away_probs[j]
                if i > j:
                    home_win += prob
                elif i == j:
                    draw += prob
                else:
                    away_win += prob
        
        # Normalize
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total
        
        # Over/under probabilities
        total_goals_lambda = home_goal_exp + away_goal_exp
        over_25 = 1 - sum(poisson.pmf(i, total_goals_lambda) for i in range(3))
        
        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'over_2.5': over_25,
            'under_2.5': 1 - over_25,
            'expected_home_goals': home_goal_exp,
            'expected_away_goals': away_goal_exp,
            'total_goals_lambda': total_goals_lambda
        }
    
    def predict_match(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Main prediction function with all enhancements"""
        # Validate team selection
        validation_errors = self.validate_team_selection(inputs['home_team'], inputs['away_team'])
        if validation_errors:
            return {'error': validation_errors}
        
        # Get league for normalization
        league = self.get_team_data(inputs['home_team'])["league"]
        
        try:
            # Calculate per-match averages
            home_xg_per_match = inputs['home_xg_total'] / 5
            home_xga_per_match = inputs['home_xga_total'] / 5
            away_xg_per_match = inputs['away_xg_total'] / 5
            away_xga_per_match = inputs['away_xga_total'] / 5
            
            # Apply injury modifiers with team quality scaling
            home_xg_adj, home_xga_adj = self.injury_module.apply_injury_modifiers(
                home_xg_per_match, home_xga_per_match,
                inputs['home_injuries'], inputs['home_team']
            )
            
            away_xg_adj, away_xga_adj = self.injury_module.apply_injury_modifiers(
                away_xg_per_match, away_xga_per_match,
                inputs['away_injuries'], inputs['away_team']
            )
            
            # Apply fatigue and form modifiers
            home_data = self.get_team_data(inputs['home_team'])
            away_data = self.get_team_data(inputs['away_team'])
            
            home_xg_final = self.apply_fatigue_modifiers(
                home_xg_adj, inputs['home_rest'], home_data['form_trend']
            )
            home_xga_final = self.apply_fatigue_modifiers(
                home_xga_adj, inputs['home_rest'], home_data['form_trend']
            )
            away_xg_final = self.apply_fatigue_modifiers(
                away_xg_adj, inputs['away_rest'], away_data['form_trend']
            )
            away_xga_final = self.apply_fatigue_modifiers(
                away_xga_adj, inputs['away_rest'], away_data['form_trend']
            )
            
            # Calculate goal expectancy
            home_goal_exp, away_goal_exp = self.calculate_goal_expectancy(
                home_xg_final, home_xga_final, away_xg_final, away_xga_final,
                inputs['home_team'], inputs['away_team'], league
            )
            
            # Calculate probabilities
            probabilities = self.calculate_poisson_probabilities(home_goal_exp, away_goal_exp)
            
            # Calculate value bets
            value_bets = self.calculate_value_bets(probabilities, {
                'home': inputs['home_odds'],
                'draw': inputs['draw_odds'], 
                'away': inputs['away_odds'],
                'over_2.5': inputs['over_odds']
            })
            
            # Generate insights
            insights = self.generate_insights(inputs, probabilities, 
                                            home_xg_per_match, away_xg_per_match,
                                            home_xga_per_match, away_xga_per_match)
            
            return {
                'probabilities': probabilities,
                'expected_goals': {'home': home_goal_exp, 'away': away_goal_exp},
                'value_bets': value_bets,
                'insights': insights,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'error': [f"Prediction failed: {str(e)}"]}
    
    def calculate_value_bets(self, probabilities: Dict[str, float], odds: Dict[str, float]) -> Dict[str, Any]:
        """Calculate value bets for all markets"""
        value_bets = {}
        
        for market, prob in [('home', probabilities['home_win']),
                           ('draw', probabilities['draw']),
                           ('away', probabilities['away_win']),
                           ('over_2.5', probabilities['over_2.5'])]:
            
            if odds[market] <= 1.0:
                value_bets[market] = {'rating': 'invalid', 'ev': -1}
                continue
            
            ev = (prob * (odds[market] - 1)) - (1 - prob)
            value_ratio = prob * odds[market]
            
            kelly_fraction = (prob * odds[market] - 1) / (odds[market] - 1) if prob * odds[market] > 1 else 0
            
            if ev > 0.08 and value_ratio > 1.12:
                rating = "excellent"
            elif ev > 0.04 and value_ratio > 1.06:
                rating = "good"
            elif ev > 0.01 and value_ratio > 1.02:
                rating = "fair"
            else:
                rating = "poor"
            
            value_bets[market] = {
                'ev': ev,
                'kelly_fraction': max(0, kelly_fraction),
                'value_ratio': value_ratio,
                'rating': rating,
                'implied_prob': 1 / odds[market],
                'model_prob': prob
            }
        
        return value_bets
    
    def generate_insights(self, inputs: Dict[str, Any], probabilities: Dict[str, float],
                         home_xg: float, away_xg: float, home_xga: float, away_xga: float) -> List[str]:
        """Generate match insights"""
        insights = []
        
        home_base = self.get_team_base_name(inputs['home_team'])
        away_base = self.get_team_base_name(inputs['away_team'])
        
        # Team quality insights
        home_quality = self.team_quality.get_team_quality(inputs['home_team'])
        away_quality = self.team_quality.get_team_quality(inputs['away_team'])
        
        quality_display = {
            "elite": "🏆 ELITE", "strong": "💪 STRONG", 
            "average": "⚖️ AVERAGE", "weak": "⚠️ WEAK"
        }
        insights.append(f"{quality_display[home_quality]} **{home_base}** vs {quality_display[away_quality]} **{away_base}**")
        
        # Add more insights as needed...
        
        return insights
