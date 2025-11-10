import pandas as pd
import numpy as np
from .data_loader import DataLoader
from .team_quality import TeamQualityAnalyzer
from .home_advantage import HomeAdvantageCalculator
from .injury_module import InjuryAnalyzer
from .config import FORM_TREND_THRESHOLDS, LEAGUE_STRENGTH

class ProfessionalPredictionEngine:
    def __init__(self, data_path="data"):
        self.data_loader = DataLoader(data_path)
        self.data = None
        self.team_quality = None
        self.home_advantage = None
        self.injury_analyzer = None
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize all components of the prediction engine"""
        print("🚀 Initializing Professional Prediction Engine...")
        
        # Load all data
        self.data = self.data_loader.load_all_data()
        
        if not self.data or any(v is None for v in self.data.values()):
            raise Exception("Failed to load required data files")
            
        # Initialize analyzers
        self.team_quality = TeamQualityAnalyzer(self.data['team_quality'])
        self.home_advantage = HomeAdvantageCalculator(self.data['home_advantage'])
        self.injury_analyzer = InjuryAnalyzer()
        
        print("✅ Prediction engine initialized successfully!")
        
    def get_team_performance_data(self, team_key):
        """Get performance data for a specific team"""
        team_data = self.data['teams'][
            self.data['teams']['team_key'] == team_key
        ]
        
        if team_data.empty:
            print(f"❌ No performance data found for {team_key}")
            return None
            
        return {
            'last_5_xg_total': team_data['last_5_xg_total'].iloc[0],
            'last_5_xga_total': team_data['last_5_xga_total'].iloc[0],
            'form_trend': team_data['form_trend'].iloc[0],
            'location': team_data['location'].iloc[0],
            'league': team_data['league'].iloc[0]
        }
        
    def calculate_form_impact(self, form_trend):
        """Calculate form impact multiplier"""
        if form_trend > FORM_TREND_THRESHOLDS["positive"]:
            return 1.05  # Positive form boost
        elif form_trend < FORM_TREND_THRESHOLDS["negative"]:
            return 0.95  # Negative form penalty
        else:
            return 1.00  # Neutral form
            
    def calculate_league_strength(self, league):
        """Apply league strength modifier"""
        return LEAGUE_STRENGTH.get(league, 1.0)
        
    def predict_match(self, home_team, away_team, home_injury="None", away_injury="None"):
        """Main prediction function"""
        print(f"🎯 Predicting: {home_team} vs {away_team}")
        
        # Get performance data
        home_data = self.get_team_performance_data(f"{home_team} Home")
        away_data = self.get_team_performance_data(f"{away_team} Away")
        
        if not home_data or not away_data:
            return {"error": "Could not load team data"}
            
        # Apply injury impacts
        home_xg_for, home_xg_against = self.injury_analyzer.apply_injury_impact(
            home_data['last_5_xg_total'], home_data['last_5_xga_total'], home_injury
        )
        away_xg_for, away_xg_against = self.injury_analyzer.apply_injury_impact(
            away_data['last_5_xg_total'], away_data['last_5_xga_total'], away_injury
        )
        
        # Calculate form impacts
        home_form_mult = self.calculate_form_impact(home_data['form_trend'])
        away_form_mult = self.calculate_form_impact(away_data['form_trend'])
        
        # Calculate quality difference
        quality_diff = self.team_quality.calculate_quality_difference(home_team, away_team)
        
        # Calculate home advantage
        home_boost = self.home_advantage.calculate_home_boost(
            f"{home_team} Home", f"{away_team} Away"
        )
        
        # Apply league strength
        home_league_mult = self.calculate_league_strength(home_data['league'])
        away_league_mult = self.calculate_league_strength(away_data['league'])
        
        # Calculate expected goals
        home_expected_goals = (
            (home_xg_for / 5) * home_form_mult * 
            (1 + quality_diff * 0.1) * home_league_mult + home_boost
        )
        away_expected_goals = (
            (away_xg_for / 5) * away_form_mult * 
            (1 - quality_diff * 0.1) * away_league_mult
        )
        
        # Adjust for defensive strength
        home_defense = (home_xg_against / 5) * home_league_mult
        away_defense = (away_xg_against / 5) * away_league_mult
        
        home_expected_goals -= away_defense * 0.2
        away_expected_goals -= home_defense * 0.2
        
        # Ensure minimum values
        home_expected_goals = max(home_expected_goals, 0.1)
        away_expected_goals = max(away_expected_goals, 0.1)
        
        # Calculate win probabilities using Poisson distribution
        home_win_prob, draw_prob, away_win_prob = self._calculate_poisson_probabilities(
            home_expected_goals, away_expected_goals
        )
        
        # Generate scoreline predictions
        likely_scorelines = self._predict_scorelines(
            home_expected_goals, away_expected_goals
        )
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_expected_goals': round(home_expected_goals, 2),
            'away_expected_goals': round(away_expected_goals, 2),
            'home_win_probability': round(home_win_prob, 3),
            'draw_probability': round(draw_prob, 3),
            'away_win_probability': round(away_win_prob, 3),
            'home_injury_impact': home_injury,
            'away_injury_impact': away_injury,
            'likely_scorelines': likely_scorelines,
            'home_advantage_boost': round(home_boost, 3),
            'quality_difference': round(quality_diff, 3)
        }
        
    def _calculate_poisson_probabilities(self, home_exp, away_exp):
        """Calculate match probabilities using Poisson distribution"""
        home_win = 0
        draw = 0
        away_win = 0
        
        for i in range(8):  # Home goals
            for j in range(8):  # Away goals
                prob = (np.exp(-home_exp) * home_exp**i / np.math.factorial(i)) * \
                       (np.exp(-away_exp) * away_exp**j / np.math.factorial(j))
                
                if i > j:
                    home_win += prob
                elif i == j:
                    draw += prob
                else:
                    away_win += prob
                    
        # Normalize probabilities
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total
            
        return home_win, draw, away_win
        
    def _predict_scorelines(self, home_exp, away_exp):
        """Predict most likely scorelines"""
        scorelines = []
        
        for i in range(5):  # Home goals
            for j in range(5):  # Away goals
                prob = (np.exp(-home_exp) * home_exp**i / np.math.factorial(i)) * \
                       (np.exp(-away_exp) * away_exp**j / np.math.factorial(j))
                scorelines.append((f"{i}-{j}", prob))
                
        # Sort by probability and return top 3
        scorelines.sort(key=lambda x: x[1], reverse=True)
        return [scoreline[0] for scoreline in scorelines[:3]]
        
    def get_available_teams(self):
        """Get list of available teams for selection"""
        teams_df = self.data['team_quality']
        return sorted(teams_df['team_base'].unique().tolist())
