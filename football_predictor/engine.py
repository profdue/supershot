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

# Import EnhancedPredictor with error handling
try:
    from .enhanced_predictor import EnhancedPredictor
    ENHANCED_PREDICTOR_AVAILABLE = True
except ImportError:
    ENHANCED_PREDICTOR_AVAILABLE = False
    print("⚠️ EnhancedPredictor not available, using basic prediction methods")

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
                
                performance_diff = row['performance_difference']
                strength = row['advantage_strength']
                goals_boost = performance_diff * 0.33
                
                self.home_advantage_data[team_key] = {
                    'ppg_diff': performance_diff,
                    'goals_boost': goals_boost,
                    'strength': strength
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
                'ppg_diff': 0.0, 
                'goals_boost': 0.0, 
                'strength': 'moderate'
            })
            
            # Get base team quality data
            base_quality = self.team_base_data.get(team_base, {
                'elo': 1600, 
                'squad_value': 100000000, 
                'structural_tier': 'average'
            })
            
            # Calculate per-match averages from stored data
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
        return self._get_league_avg_xg(league)

    def get_comprehensive_team_data(self, team_key):
        """Get fully integrated team data"""
        return self.comprehensive_database.get(team_key, self._get_default_team_data(team_key))
        
    def _get_default_team_data(self, team_key):
        """Get default data for missing teams"""
        base_name = self._extract_base_name(team_key)
        return {
            'league': "Premier League",
            'xg_total': 7.5, 
            'xga_total': 7.5, 
            'matches_played': 5,
            'form_trend': 0.0, 
            'location': 'home' if 'Home' in team_key else 'away',
            'clean_sheet_pct': 20, 
            'btts_pct': 50, 
            'goal_difference': 0,
            'xg_per_match': 1.5, 
            'xga_per_match': 1.5, 
            'net_xg_per_match': 0.0,
            'home_advantage': {
                'ppg_diff': 0.0, 
                'goals_boost': 0.0, 
                'strength': 'moderate'
            },
            'base_quality': {
                'elo': 1600, 
                'squad_value': 100000000, 
                'structural_tier': 'average'
            },
            'base_name': base_name,
            'attack_strength': 1.0, 
            'defense_strength': 1.0
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
        
        # Initialize enhanced predictor if available
        if ENHANCED_PREDICTOR_AVAILABLE:
            self.enhanced_predictor = EnhancedPredictor(self.data_integrator)
            print("✅ Prediction engine initialized with enhanced predictors!")
        else:
            self.enhanced_predictor = None
            print("✅ Prediction engine initialized (basic mode)")
        
    # PUBLIC PROPERTIES FOR THE APP TO USE
    @property
    def injury_weights(self):
        """Expose injury weights to the app"""
        return self.injury_analyzer.injury_weights
        
    @property
    def fatigue_multipliers(self):
        """Expose fatigue multipliers to the app"""
        return self.injury_analyzer.fatigue_multipliers
        
    @property
    def league_averages(self):
        """Expose league averages to the app"""
        return {
            "Premier League": {"xg": 1.45, "xga": 1.45},
            "La Liga": {"xg": 1.38, "xga": 1.38},
            "Bundesliga": {"xg": 1.52, "xga": 1.52},
            "Serie A": {"xg": 1.42, "xga": 1.42},
            "Ligue 1": {"xg": 1.40, "xga": 1.40},
            "RFPL": {"xg": 1.35, "xga": 1.35}
        }
        
    @property
    def value_thresholds(self):
        """Expose value thresholds to the app"""
        return self.value_calculator.value_thresholds
        
    @property
    def confidence_weights(self):
        """Expose confidence weights to the app"""
        return self.confidence_calculator.confidence_weights
        
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

    def _get_correct_team_data(self, team_key, is_home):
        """Get correct home/away team data based on context"""
        base_name = self.get_team_base_name(team_key)
        
        if is_home:
            correct_key = f"{base_name} Home"
        else:
            correct_key = f"{base_name} Away"
        
        data = self.get_team_data(correct_key)
        
        # Fallback if specific home/away data not found
        if data is None or data.get('xg_total', 0) == 0:
            fallback_key = f"{base_name} Home"
            data = self.get_team_data(fallback_key)
            
        return data

    def _get_team_xg_data(self, team_key, is_home):
        """Get xG data for a team - now using integrated data only"""
        team_data = self._get_correct_team_data(team_key, is_home)
        
        # Use the integrated data directly
        xg_per_match = team_data['xg_per_match']
        xga_per_match = team_data['xga_per_match']
        
        # Convert to totals for 5 matches (for compatibility)
        xg_total = xg_per_match * 5
        xga_total = xga_per_match * 5
        
        return xg_total, xga_total

    def calculate_goal_expectancy(self, home_team, away_team, home_injuries, away_injuries, home_rest, away_rest):
        """Calculate goal expectancy using ONLY integrated data"""
        # Get comprehensive team data
        home_data = self.get_team_data(home_team)
        away_data = self.get_team_data(away_team)
        
        # Use integrated xG data directly
        home_xg_per_match = home_data['xg_per_match']
        home_xga_per_match = home_data['xga_per_match']
        away_xg_per_match = away_data['xg_per_match']
        away_xga_per_match = away_data['xga_per_match']
        
        # Apply injury impacts
        home_xg_adj, home_xga_adj = self.injury_analyzer.apply_injury_impact(
            home_xg_per_match, home_xga_per_match,
            home_injuries, home_rest,
            home_data['form_trend']
        )
        
        away_xg_adj, away_xga_adj = self.injury_analyzer.apply_injury_impact(
            away_xg_per_match, away_xga_per_match,
            away_injuries, away_rest,
            away_data['form_trend']
        )
        
        # Use integrated home advantage data
        home_boost = home_data['home_advantage']['goals_boost']
        away_penalty = -away_data['home_advantage']['goals_boost'] * 0.5
        
        # Use league averages from integrated data
        league = home_data['league']
        league_avg_xg = self.data_integrator._get_league_avg_xg(league)
        league_avg_xga = self.data_integrator._get_league_avg_xga(league)
        
        # Enhanced normalization using integrated data
        home_goal_exp = home_xg_adj * (away_xga_adj / league_avg_xga) ** 0.7 * home_data['attack_strength'] ** 0.3
        away_goal_exp = away_xg_adj * (home_xga_adj / league_avg_xga) ** 0.7 * away_data['attack_strength'] ** 0.3
        
        # Apply integrated home advantage
        home_goal_exp += home_boost
        away_goal_exp += away_penalty
        
        return max(0.1, home_goal_exp), max(0.1, away_goal_exp)

    def _apply_prediction_sanity_checks(self, result, home_data, away_data):
        """Apply sanity checks to prevent unrealistic predictions"""
        home_elo = home_data['base_quality']['elo']
        away_elo = away_data['base_quality']['elo']
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        
        home_win_prob = result['probabilities']['home_win']
        away_win_prob = result['probabilities']['away_win']
        
        # Elite teams should rarely be underdogs against non-elite teams
        if (home_tier == 'elite' and away_tier != 'elite' and away_win_prob > home_win_prob) or \
           (away_tier == 'elite' and home_tier != 'elite' and home_win_prob > away_win_prob):
            if home_tier == 'elite':
                home_win_prob = max(home_win_prob, 0.45)
                away_win_prob = min(away_win_prob, 0.40)
            else:
                away_win_prob = max(away_win_prob, 0.45)
                home_win_prob = min(home_win_prob, 0.40)
            
            # Re-normalize with draw probability
            draw_prob = result['probabilities']['draw']
            total = home_win_prob + draw_prob + away_win_prob
            result['probabilities']['home_win'] = home_win_prob / total
            result['probabilities']['away_win'] = away_win_prob / total
            result['probabilities']['draw'] = draw_prob / total
        
        # Sanity check: Weak teams shouldn't be heavy favorites over strong teams
        if (home_tier == 'weak' and away_tier == 'strong' and home_win_prob > 0.6) or \
           (away_tier == 'weak' and home_tier == 'strong' and away_win_prob > 0.6):
            elo_diff = home_elo - away_elo
            elo_correction = 1 / (1 + 10 ** (-elo_diff / 400))
            
            if home_tier == 'weak':
                home_win_prob = min(home_win_prob, elo_correction * 0.8)
                away_win_prob = max(away_win_prob, (1 - elo_correction) * 0.8)
            else:
                away_win_prob = min(away_win_prob, (1 - elo_correction) * 0.8)
                home_win_prob = max(home_win_prob, elo_correction * 0.8)
            
            # Re-normalize
            total = home_win_prob + result['probabilities']['draw'] + away_win_prob
            result['probabilities']['home_win'] = home_win_prob / total
            result['probabilities']['away_win'] = away_win_prob / total
            result['probabilities']['draw'] = result['probabilities']['draw'] / total
        
        # Sanity check: Total goals shouldn't be unrealistically high
        total_goals = result['expected_goals']['home'] + result['expected_goals']['away']
        if total_goals > 5.0:
            damping = 4.5 / total_goals
            result['expected_goals']['home'] *= damping
            result['expected_goals']['away'] *= damping
        
        # Sanity check: Very weak teams shouldn't have high goal expectancy
        if home_tier == 'weak' and result['expected_goals']['home'] > 2.0:
            result['expected_goals']['home'] = min(result['expected_goals']['home'], 1.5)
        
        if away_tier == 'weak' and result['expected_goals']['away'] > 2.0:
            result['expected_goals']['away'] = min(result['expected_goals']['away'], 1.5)
        
        return result

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
        """Enhanced prediction using ONLY integrated data - no manual xG inputs"""
        # Validate team selection
        validation_errors = self.validate_team_selection(inputs['home_team'], inputs['away_team'])
        if validation_errors:
            return None, validation_errors, []
        
        # Get team data
        home_data = self._get_correct_team_data(inputs['home_team'], is_home=True)
        away_data = self._get_correct_team_data(inputs['away_team'], is_home=False)
        
        # Calculate goal expectancy using integrated data only
        home_goal_exp, away_goal_exp = self.calculate_goal_expectancy(
            inputs['home_team'], inputs['away_team'],
            inputs['home_injuries'], inputs['away_injuries'],
            inputs['home_rest'], inputs['away_rest']
        )
        
        # Use enhanced predictor if available, otherwise fall back to basic
        if self.enhanced_predictor:
            winner_prediction = self.enhanced_predictor.predict_winner_enhanced(
                inputs['home_team'], inputs['away_team'],
                home_goal_exp, away_goal_exp, home_goal_exp, away_goal_exp,
                inputs['home_injuries'], inputs['away_injuries']
            )
            
            over_under_prediction = self.enhanced_predictor.predict_over_under_enhanced(
                inputs['home_team'], inputs['away_team'],
                home_goal_exp, away_goal_exp, home_goal_exp, away_goal_exp
            )
            
            btts_prediction = self.enhanced_predictor.predict_btts_enhanced(
                inputs['home_team'], inputs['away_team'],
                home_goal_exp, away_goal_exp, home_goal_exp, away_goal_exp
            )
        else:
            # Fall back to basic predictions
            basic_probs = self.poisson_calculator.calculate_poisson_probabilities(home_goal_exp, away_goal_exp)
            
            winner_prediction = {
                'home_win': basic_probs['home_win'],
                'draw': basic_probs['draw'],
                'away_win': basic_probs['away_win'],
                'confidence': 60,
                'expected_goals': {'home': home_goal_exp, 'away': away_goal_exp},
                'key_factors': {'basic_mode': True}
            }
            
            total_goals = home_goal_exp + away_goal_exp
            over_under_prediction = {
                'over_1.5': 1 - poisson.cdf(1.5, total_goals),
                'over_2.5': 1 - poisson.cdf(2.5, total_goals),
                'over_3.5': 1 - poisson.cdf(3.5, total_goals),
                'under_1.5': poisson.cdf(1.5, total_goals),
                'under_2.5': poisson.cdf(2.5, total_goals),
                'under_3.5': poisson.cdf(3.5, total_goals),
                'confidence': 55,
                'key_factors': {'basic_mode': True}
            }
            
            btts_prob = (1 - poisson.cdf(0, home_goal_exp)) * (1 - poisson.cdf(0, away_goal_exp))
            btts_prediction = {
                'btts_yes': btts_prob,
                'btts_no': 1 - btts_prob,
                'confidence': 50,
                'key_factors': {'basic_mode': True}
            }
        
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
        
        # Use outcome-specific confidence calculation
        outcome_confidences, confidence_factors = self.confidence_calculator.calculate_outcome_specific_confidence(
            probabilities, home_data, away_data, inputs
        )
        
        # Enhanced calculation details
        calculation_details = {
            'enhanced_predictions_used': self.enhanced_predictor is not None,
            'winner_confidence': winner_prediction['confidence'],
            'over_under_confidence': over_under_prediction['confidence'],
            'btts_confidence': btts_prediction['confidence'],
            'key_factors_winner': winner_prediction['key_factors'],
            'key_factors_over_under': over_under_prediction['key_factors'],
            'key_factors_btts': btts_prediction['key_factors'],
            'data_integration_note': 'All data updates fully integrated and utilized in enhanced predictions',
            'outcome_specific_confidences': outcome_confidences,
            'team_data_context': f"Home: {home_data.get('location', 'unknown')}, Away: {away_data.get('location', 'unknown')}"
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
            'confidence': outcome_confidences,
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
            # Calculate overall reliability based on average confidence
            'reliability_score': min(95, np.mean(list(outcome_confidences.values())) * 0.9),
            'reliability_level': 'High' if np.mean(list(outcome_confidences.values())) > 70 else 'Moderate' if np.mean(list(outcome_confidences.values())) > 55 else 'Low',
            'reliability_advice': 'Enhanced predictions using all integrated data provide high reliability'
        }
        
        # Apply sanity checks as final defense
        result = self._apply_prediction_sanity_checks(result, home_data, away_data)
        
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
