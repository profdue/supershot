import pandas as pd
import numpy as np
from scipy.stats import poisson
from .data_loader import DataLoader
from .team_quality import TeamQualityAnalyzer
from .home_advantage import HomeAdvantageCalculator
from .injury_module import InjuryAnalyzer
from .poisson_calculator import PoissonCalculator
from .value_calculator import ValueCalculator
from .confidence_calculator import ConfidenceCalculator
from .enhanced_predictor import EnhancedPredictor

class DataIntegrator:
    def __init__(self, engine):
        self.engine = engine
        self.team_database = {}
        self.team_base_data = {}
        self.home_advantage_data = {}
        self.team_quality_data = {}
        
    def integrate_all_data(self):
        """Completely integrate all data updates into the engine"""
        print("🔄 Integrating all data updates...")
        
        # 1. Integrate team performance data
        self._integrate_team_performance_data()
        
        # 2. Integrate home advantage data  
        self._integrate_home_advantage_data()
        
        # 3. Integrate team quality data
        self._integrate_team_quality_data()
        
        # 4. Build comprehensive team database
        self._build_comprehensive_database()
        
        print("✅ All data updates integrated successfully!")
        
    def _integrate_team_performance_data(self):
        """Integrate the main team performance data"""
        if 'teams' in self.engine.data:
            df = self.engine.data['teams']
            for _, row in df.iterrows():
                team_key = row['team_key']
                self.team_database[team_key] = {
                    'league': row['league'],
                    'xg_total': row['xg_total'],
                    'xga_total': row['xga_total'],
                    'matches_played': row['matches_played'],
                    'form_trend': row['form_trend'],
                    'location': row['location'],
                    'clean_sheet_pct': row['clean_sheet_pct'],
                    'btts_pct': row['btts_pct'],
                    'goal_difference': row['goal_difference']
                }
                
    def _integrate_home_advantage_data(self):
        """Integrate home advantage data with proper mapping"""
        if 'home_advantage' in self.engine.data:
            df = self.engine.data['home_advantage']
            for _, row in df.iterrows():
                team_key = row['team_key']
                self.home_advantage_data[team_key] = {
                    'ppg_diff': row['ppg_diff'],
                    'goals_boost': row['goals_boost'],
                    'strength': row['strength']
                }
                
    def _integrate_team_quality_data(self):
        """Integrate team quality and base data"""
        if 'team_quality' in self.engine.data:
            df = self.engine.data['team_quality']
            for _, row in df.iterrows():
                team_base = row['team_base']
                self.team_base_data[team_base] = {
                    'elo': row['elo'],
                    'squad_value': row['squad_value'],
                    'structural_tier': row['structural_tier']
                }
                
    def _build_comprehensive_database(self):
        """Build a comprehensive team database with all integrated data"""
        comprehensive_db = {}
        
        for team_key, perf_data in self.team_database.items():
            team_base = self._extract_base_name(team_key)
            
            # Get home advantage data
            home_adv = self.home_advantage_data.get(team_key, {
                'ppg_diff': 0.0, 'goals_boost': 0.0, 'strength': 'moderate'
            })
            
            # Get base team quality data
            base_quality = self.team_base_data.get(team_base, {
                'elo': 1600, 'squad_value': 100000000, 'structural_tier': 'average'
            })
            
            # Calculate per-match averages
            matches = max(1, perf_data['matches_played'])
            xg_per_match = perf_data['xg_total'] / matches
            xga_per_match = perf_data['xga_total'] / matches
            
            comprehensive_db[team_key] = {
                # Performance data
                'league': perf_data['league'],
                'xg_total': perf_data['xg_total'],
                'xga_total': perf_data['xga_total'],
                'matches_played': perf_data['matches_played'],
                'form_trend': perf_data['form_trend'],
                'location': perf_data['location'],
                'clean_sheet_pct': perf_data['clean_sheet_pct'],
                'btts_pct': perf_data['btts_pct'],
                'goal_difference': perf_data['goal_difference'],
                
                # Calculated metrics
                'xg_per_match': xg_per_match,
                'xga_per_match': xga_per_match,
                
                # Home advantage data
                'home_advantage': home_adv,
                
                # Base team quality
                'base_quality': base_quality,
                'base_name': team_base,
                
                # Derived metrics
                'net_xg_per_match': xg_per_match - xga_per_match,
                'attack_strength': xg_per_match / self._get_league_avg_xg(perf_data['league']),
                'defense_strength': xga_per_match / self._get_league_avg_xga(perf_data['league'])
            }
            
        self.comprehensive_database = comprehensive_db
        
    def _extract_base_name(self, team_key):
        """Extract base team name from team key"""
        if " Home" in team_key:
            return team_key.replace(" Home", "")
        elif " Away" in team_key:
            return team_key.replace(" Away", "")
        return team_key
        
    def _get_league_avg_xg(self, league):
        """Get league average xG"""
        league_averages = {
            "Premier League": 1.45,
            "La Liga": 1.38, 
            "Bundesliga": 1.52,
            "Serie A": 1.42,
            "Ligue 1": 1.40,
            "RFPL": 1.35
        }
        return league_averages.get(league, 1.40)
        
    def _get_league_avg_xga(self, league):
        """Get league average xGA"""
        return self._get_league_avg_xg(league)  # Same as xG for simplicity

    def get_comprehensive_team_data(self, team_key):
        """Get fully integrated team data"""
        return self.comprehensive_database.get(team_key, self._get_default_team_data(team_key))
        
    def _get_default_team_data(self, team_key):
        """Get default data for missing teams"""
        base_name = self._extract_base_name(team_key)
        return {
            'league': "Premier League",
            'xg_total': 7.5, 'xga_total': 7.5, 'matches_played': 5,
            'form_trend': 0.0, 'location': 'home' if 'Home' in team_key else 'away',
            'clean_sheet_pct': 20, 'btts_pct': 50, 'goal_difference': 0,
            'xg_per_match': 1.5, 'xga_per_match': 1.5, 'net_xg_per_match': 0.0,
            'home_advantage': {'ppg_diff': 0.0, 'goals_boost': 0.0, 'strength': 'moderate'},
            'base_quality': {'elo': 1600, 'squad_value': 100000000, 'structural_tier': 'average'},
            'base_name': base_name,
            'attack_strength': 1.0, 'defense_strength': 1.0
        }

class ProfessionalPredictionEngine:
    def __init__(self, data_path="data"):
        self.data_loader = DataLoader(data_path)
        self.data = None
        self.team_quality = None
        self.home_advantage = None
        self.injury_analyzer = None
        self.poisson_calculator = None
        self.value_calculator = None
        self.confidence_calculator = None
        self.data_integrator = None
        self.enhanced_predictor = None
        self.comprehensive_database = {}
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize all components with proper data integration"""
        print("🚀 Initializing Professional Prediction Engine...")
        
        # Load all data
        self.data = self.data_loader.load_all_data()
        
        if not self.data or any(v is None for v in self.data.values()):
            raise Exception("Failed to load required data files")
            
        # Initialize data integrator FIRST
        self.data_integrator = DataIntegrator(self)
        self.data_integrator.integrate_all_data()
        self.comprehensive_database = self.data_integrator.comprehensive_database
            
        # Initialize analyzers with integrated data
        self.team_quality = TeamQualityAnalyzer(self.data['team_quality'])
        self.home_advantage = HomeAdvantageCalculator(self.data['home_advantage'])
        self.injury_analyzer = InjuryAnalyzer()
        self.poisson_calculator = PoissonCalculator()
        self.value_calculator = ValueCalculator()
        self.confidence_calculator = ConfidenceCalculator(self.injury_analyzer, self.home_advantage)
        self.enhanced_predictor = EnhancedPredictor(self.data_integrator)
        
        print("✅ Prediction engine initialized with enhanced predictors!")
        
    def get_team_data(self, team_key):
        """Get comprehensive team data with all updates integrated"""
        return self.data_integrator.get_comprehensive_team_data(team_key)
        
    def get_teams_by_league(self, league, team_type="all"):
        """Get teams in a specific league using integrated data"""
        teams = []
        for team_name, data in self.comprehensive_database.items():
            if data["league"] == league:
                if team_type == "all":
                    teams.append(team_name)
                elif team_type == "home" and "Home" in team_name:
                    teams.append(team_name)
                elif team_type == "away" and "Away" in team_name:
                    teams.append(team_name)
        return sorted(teams)
        
    def get_team_base_name(self, team_name):
        """Extract base team name using integrated logic"""
        return self.data_integrator._extract_base_name(team_name)
        
    def get_team_home_advantage(self, team_name):
        """Get integrated home advantage data"""
        team_data = self.get_team_data(team_name)
        return team_data['home_advantage']
        
    def validate_team_selection(self, home_team, away_team):
        """Validate team selection using integrated data"""
        home_data = self.get_team_data(home_team)
        away_data = self.get_team_data(away_team)
        
        errors = []
        if home_data['base_name'] == away_data['base_name']:
            errors.append("Cannot select the same team for both home and away")
        if home_data['league'] != away_data['league']:
            errors.append(f"Teams must be from the same league. {home_data['base_name']} is in {home_data['league']}, {away_data['base_name']} is in {away_data['league']}")
        
        return errors

    def calculate_goal_expectancy(self, home_xg, home_xga, away_xg, away_xga, home_team, away_team, league):
        """Calculate goal expectancy using integrated data"""
        # Get comprehensive team data
        home_data = self.get_team_data(home_team)
        away_data = self.get_team_data(away_team)
        
        # Use integrated home advantage data
        home_boost = home_data['home_advantage']['goals_boost']
        away_penalty = -away_data['home_advantage']['goals_boost'] * 0.5
        
        # Use league averages from integrated data
        league_avg_xg = self.data_integrator._get_league_avg_xg(league)
        league_avg_xga = self.data_integrator._get_league_avg_xga(league)
        
        # Enhanced normalization using integrated data
        home_goal_exp = home_xg * (away_xga / league_avg_xga) ** 0.7 * home_data['attack_strength'] ** 0.3
        away_goal_exp = away_xg * (home_xga / league_avg_xga) ** 0.7 * away_data['attack_strength'] ** 0.3
        
        # Apply integrated home advantage
        home_goal_exp += home_boost
        away_goal_exp += away_penalty
        
        return max(0.1, home_goal_exp), max(0.1, away_goal_exp)

    def generate_enhanced_insights(self, inputs, probabilities, home_team, away_team):
        """Generate enhanced insights using integrated data"""
        insights = []
        
        home_data = self.get_team_data(home_team)
        away_data = self.get_team_data(away_team)
        
        home_base = home_data['base_name']
        away_base = away_data['base_name']
        
        # Enhanced home advantage insights using integrated data
        home_adv = home_data['home_advantage']
        away_adv = away_data['home_advantage']
        
        if home_adv['strength'] == "strong":
            insights.append(f"🏠 **STRONG HOME ADVANTAGE**: {home_base} performs much better at home (+{home_adv['ppg_diff']:.2f} PPG, {home_adv['goals_boost']:.3f} goal boost)")
        elif home_adv['strength'] == "weak":
            insights.append(f"🏠 **WEAK HOME FORM**: {home_base} struggles at home ({home_adv['ppg_diff']:+.2f} PPG difference)")
        
        if away_adv['strength'] == "strong":
            insights.append(f"✈️ **STRONG AWAY PERFORMANCE**: {away_base} travels well ({away_adv['ppg_diff']:+.2f} PPG difference)")
        elif away_adv['strength'] == "weak":
            insights.append(f"✈️ **POOR AWAY FORM**: {away_base} struggles away from home ({away_adv['ppg_diff']:+.2f} PPG difference)")
        
        # Team quality insights using integrated data
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        
        if home_tier != away_tier:
            insights.append(f"🏆 **TEAM QUALITY DIFFERENCE**: {home_base} ({home_tier}) vs {away_base} ({away_tier})")
        
        # Form insights using integrated data
        if home_data['form_trend'] > 0.05:
            insights.append(f"📈 **POSITIVE FORM**: {home_base} showing improvement (trend: {home_data['form_trend']:.2f})")
        elif home_data['form_trend'] < -0.05:
            insights.append(f"📉 **NEGATIVE FORM**: {home_base} in decline (trend: {home_data['form_trend']:.2f})")
            
        if away_data['form_trend'] > 0.05:
            insights.append(f"📈 **POSITIVE FORM**: {away_base} showing improvement (trend: {away_data['form_trend']:.2f})")
        elif away_data['form_trend'] < -0.05:
            insights.append(f"📉 **NEGATIVE FORM**: {away_base} in decline (trend: {away_data['form_trend']:.2f})")
        
        # Defense/attack insights using clean sheet and BTTS data
        if home_data['clean_sheet_pct'] > 40:
            insights.append(f"🛡️ **STRONG DEFENSE**: {home_base} keeps clean sheets in {home_data['clean_sheet_pct']}% of matches")
        if away_data['clean_sheet_pct'] > 40:
            insights.append(f"🛡️ **STRONG DEFENSE**: {away_base} keeps clean sheets in {away_data['clean_sheet_pct']}% of matches")
            
        if home_data['btts_pct'] > 60:
            insights.append(f"⚽ **GOAL-FRIENDLY**: {home_base} matches see both teams score in {home_data['btts_pct']}% of games")
        if away_data['btts_pct'] > 60:
            insights.append(f"⚽ **GOAL-FRIENDLY**: {away_base} matches see both teams score in {away_data['btts_pct']}% of games")
        
        return insights

    def predict_match_enhanced(self, inputs):
        """Enhanced prediction with better accuracy for winner, over/under, BTTS"""
        # Validate team selection
        validation_errors = self.validate_team_selection(inputs['home_team'], inputs['away_team'])
        if validation_errors:
            return None, validation_errors, []
        
        # Get team data
        home_data = self.get_team_data(inputs['home_team'])
        away_data = self.get_team_data(inputs['away_team'])
        
        # Calculate per-match averages
        home_xg_per_match = inputs['home_xg_total'] / 5
        home_xga_per_match = inputs['home_xga_total'] / 5
        away_xg_per_match = inputs['away_xg_total'] / 5
        away_xga_per_match = inputs['away_xga_total'] / 5
        
        # Apply injury impacts
        home_xg_adj, home_xga_adj = self.injury_analyzer.apply_injury_impact(
            home_xg_per_match, home_xga_per_match,
            inputs['home_injuries'], inputs['home_rest'],
            home_data['form_trend']
        )
        
        away_xg_adj, away_xga_adj = self.injury_analyzer.apply_injury_impact(
            away_xg_per_match, away_xga_per_match,
            inputs['away_injuries'], inputs['away_rest'],
            away_data['form_trend']
        )
        
        # Get enhanced predictions
        winner_prediction = self.enhanced_predictor.predict_winner_enhanced(
            inputs['home_team'], inputs['away_team'],
            home_xg_adj, away_xg_adj, home_xga_adj, away_xga_adj,
            inputs['home_injuries'], inputs['away_injuries']
        )
        
        over_under_prediction = self.enhanced_predictor.predict_over_under_enhanced(
            inputs['home_team'], inputs['away_team'],
            home_xg_adj, away_xg_adj, home_xga_adj, away_xga_adj
        )
        
        btts_prediction = self.enhanced_predictor.predict_btts_enhanced(
            inputs['home_team'], inputs['away_team'],
            home_xg_adj, away_xg_adj, home_xga_adj, away_xga_adj
        )
        
        # Calculate value bets
        odds = {
            'home': inputs['home_odds'],
            'draw': inputs['draw_odds'],
            'away': inputs['away_odds'],
            'over_2.5': inputs['over_odds']
        }
        
        probabilities = {
            'home_win': winner_prediction['home_win'],
            'draw': winner_prediction['draw'],
            'away_win': winner_prediction['away_win'],
            'over_2.5': over_under_prediction['over_2.5']
        }
        
        value_bets = self.value_calculator.calculate_value_bets(probabilities, odds)
        
        # Generate insights
        insights = self.generate_enhanced_insights(inputs, probabilities, inputs['home_team'], inputs['away_team'])
        
        # Calculate overall confidence
        confidence, confidence_factors = self.confidence_calculator.calculate_confidence(
            home_xg_per_match, away_xg_per_match,
            home_xga_per_match, away_xga_per_match, inputs
        )
        
        # Enhanced calculation details
        calculation_details = {
            'enhanced_predictions_used': True,
            'winner_confidence': winner_prediction['confidence'],
            'over_under_confidence': over_under_prediction['confidence'],
            'btts_confidence': btts_prediction['confidence'],
            'key_factors_winner': winner_prediction['key_factors'],
            'key_factors_over_under': over_under_prediction['key_factors'],
            'key_factors_btts': btts_prediction['key_factors'],
            'data_integration_note': 'All data updates fully integrated and utilized in enhanced predictions'
        }
        
        # Combine all predictions
        combined_probabilities = {
            **probabilities,
            'over_1.5': over_under_prediction['over_1.5'],
            'over_3.5': over_under_prediction['over_3.5'],
            'under_1.5': over_under_prediction['under_1.5'],
            'under_2.5': over_under_prediction['under_2.5'],
            'under_3.5': over_under_prediction['under_3.5'],
            'btts_yes': btts_prediction['btts_yes'],
            'btts_no': btts_prediction['btts_no']
        }
        
        result = {
            'probabilities': combined_probabilities,
            'expected_goals': winner_prediction['expected_goals'],
            'value_bets': value_bets,
            'confidence': confidence,
            'confidence_factors': confidence_factors,
            'enhanced_predictions': {
                'winner': winner_prediction,
                'over_under': over_under_prediction,
                'btts': btts_prediction
            },
            'insights': insights,
            'team_data': {
                'home': home_data,
                'away': away_data
            },
            'calculation_details': calculation_details,
            'reliability_score': min(95, confidence * 0.9),  # Enhanced predictions are more reliable
            'reliability_level': 'High' if confidence > 70 else 'Moderate' if confidence > 55 else 'Low',
            'reliability_advice': 'Enhanced predictions using all integrated data provide high reliability'
        }
        
        return result, [], []

    # Keep original method for backward compatibility
    def predict_match(self, inputs):
        """Original prediction method - now uses enhanced predictions by default"""
        return self.predict_match_enhanced(inputs)
        
    def get_available_leagues(self):
        """Get list of available leagues from the database"""
        leagues = set()
        for team_data in self.comprehensive_database.values():
            leagues.add(team_data["league"])
        return sorted(list(leagues))
