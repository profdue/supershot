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
        self.team_database = {}
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
        self.poisson_calculator = PoissonCalculator()
        self.value_calculator = ValueCalculator()
        self.confidence_calculator = ConfidenceCalculator(self.injury_analyzer, self.home_advantage)
        
        # Build team database from loaded data
        self._build_team_database()
        
        print("✅ Prediction engine initialized successfully!")
        
    def _build_team_database(self):
        """Build team database from loaded CSV data"""
        for _, row in self.data['teams'].iterrows():
            self.team_database[row['team_key']] = {
                'league': row['league'],
                'last_5_xg_total': row['last_5_xg_total'],
                'last_5_xga_total': row['last_5_xga_total'],
                'form_trend': row['form_trend'],
                'location': row['location']
            }
    
    # PUBLIC METHODS FOR THE APP TO USE
    def get_team_data(self, team_key):
        """Get team data with fallback defaults"""
        default_data = {
            "league": "Unknown", 
            "last_5_xg_total": 7.50,
            "last_5_xga_total": 7.50,
            "form_trend": 0.00
        }
        
        team_data = self.team_database.get(team_key, default_data).copy()
        
        # Calculate per-match averages
        team_data['last_5_xg_per_match'] = team_data['last_5_xg_total'] / 5
        team_data['last_5_xga_per_match'] = team_data['last_5_xga_total'] / 5
        
        return team_data
        
    def get_teams_by_league(self, league, team_type="all"):
        """Get teams in a specific league, filtered by type (home/away/all)"""
        teams = []
        for team_name, data in self.team_database.items():
            if data["league"] == league:
                if team_type == "all":
                    teams.append(team_name)
                elif team_type == "home" and "Home" in team_name:
                    teams.append(team_name)
                elif team_type == "away" and "Away" in team_name:
                    teams.append(team_name)
        return sorted(teams)
        
    def get_team_base_name(self, team_name):
        """Extract base team name without Home/Away suffix"""
        if " Home" in team_name:
            return team_name.replace(" Home", "")
        elif " Away" in team_name:
            return team_name.replace(" Away", "")
        return team_name
        
    def get_team_home_advantage(self, team_name):
        """Get team-specific home advantage data"""
        return self.home_advantage.get_home_advantage(team_name)
        
    def validate_team_selection(self, home_team, away_team):
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

    # YOUR ADVANCED PREDICTION LOGIC
    def calculate_goal_expectancy(self, home_xg, home_xga, away_xg, away_xga, home_team, away_team, league):
        """ENHANCED: Calculate proper goal expectancy with FIXED normalization"""
        league_avg = {
            "Premier League": {"xg": 1.45, "xga": 1.45},
            "La Liga": {"xg": 1.38, "xga": 1.38},
            "Bundesliga": {"xg": 1.52, "xga": 1.52},
            "Serie A": {"xg": 1.42, "xga": 1.42},
            "Ligue 1": {"xg": 1.40, "xga": 1.40},
            "RFPL": {"xg": 1.35, "xga": 1.35}
        }.get(league, {"xg": 1.4, "xga": 1.4})
        
        # Get team-specific home advantage
        home_advantage_data = self.home_advantage.get_home_advantage(home_team)
        away_advantage_data = self.home_advantage.get_home_advantage(away_team)
        
        home_boost = home_advantage_data["goals_boost"]
        away_penalty = -away_advantage_data["goals_boost"] * 0.5  # Away teams get partial penalty
        
        # FIXED: Less aggressive normalization (0.8 power instead of 0.5)
        home_goal_exp = home_xg * (away_xga / league_avg["xga"]) ** 0.8
        
        # Away goal expectancy: away attack vs home defense, normalized by league average  
        away_goal_exp = away_xg * (home_xga / league_avg["xga"]) ** 0.8
        
        # Apply team-specific home advantage
        home_goal_exp += home_boost
        away_goal_exp += away_penalty
        
        return max(0.1, home_goal_exp), max(0.1, away_goal_exp)

    def calculate_minimal_advantage(self, home_xg, home_xga, away_xg, away_xga):
        """MINIMAL advantage adjustment to prevent over-correction"""
        # Very small adjustment factor
        alpha = 0.02  # Reduced from 0.12 (6x smaller)
        
        home_advantage = (home_xg - away_xg + away_xga - home_xga) * 0.1
        
        home_xg_adj = home_xg * (1 + home_advantage * alpha)
        away_xg_adj = away_xg * (1 - home_advantage * alpha)
        
        # Leave defenses mostly unchanged
        home_xga_adj = home_xga
        away_xga_adj = away_xga
        
        return home_xg_adj, home_xga_adj, away_xg_adj, away_xga_adj

    def generate_insights(self, inputs, probabilities, home_xg, away_xg, home_xga, away_xga):
        """ENHANCED: Generate insights with home advantage and injury context"""
        insights = []
        
        # Get base team names for display
        home_base = self.get_team_base_name(inputs['home_team'])
        away_base = self.get_team_base_name(inputs['away_team'])
        
        # Get home advantage data
        home_adv_data = self.home_advantage.get_home_advantage(inputs['home_team'])
        away_adv_data = self.home_advantage.get_home_advantage(inputs['away_team'])
        
        # Home advantage insights
        home_adv_strength = home_adv_data['strength']
        away_adv_strength = away_adv_data['strength']
        
        if home_adv_strength == "strong":
            insights.append(f"🏠 **STRONG HOME ADVANTAGE**: {home_base} performs much better at home (+{home_adv_data['ppg_diff']:.2f} PPG)")
        elif home_adv_strength == "weak":
            insights.append(f"🏠 **WEAK HOME FORM**: {home_base} struggles at home ({home_adv_data['ppg_diff']:+.2f} PPG difference)")
        else:
            insights.append(f"🏠 **MODERATE HOME ADVANTAGE**: {home_base} has standard home performance (+{home_adv_data['ppg_diff']:.2f} PPG)")
        
        if away_adv_strength == "strong":
            insights.append(f"✈️ **POOR AWAY FORM**: {away_base} struggles away from home ({away_adv_data['ppg_diff']:+.2f} PPG difference)")
        elif away_adv_strength == "weak":
            insights.append(f"✈️ **STRONG AWAY FORM**: {away_base} travels well ({away_adv_data['ppg_diff']:+.2f} PPG difference)")
        
        # ENHANCED: Injury insights with impact levels
        home_injury_data = self.injury_analyzer.injury_weights[inputs['home_injuries']]
        away_injury_data = self.injury_analyzer.injury_weights[inputs['away_injuries']]
        
        if inputs['home_injuries'] != "None":
            attack_reduction = (1-home_injury_data['attack_mult'])*100
            defense_reduction = (1-home_injury_data['defense_mult'])*100
            insights.append(f"🩹 **INJURY IMPACT**: {home_base} - {home_injury_data['description']} (Attack: -{attack_reduction:.0f}%, Defense: -{defense_reduction:.0f}%)")
        
        if inputs['away_injuries'] != "None":
            attack_reduction = (1-away_injury_data['attack_mult'])*100
            defense_reduction = (1-away_injury_data['defense_mult'])*100
            insights.append(f"🩹 **INJURY IMPACT**: {away_base} - {away_injury_data['description']} (Attack: -{attack_reduction:.0f}%, Defense: -{defense_reduction:.0f}%)")
        
        # Rest insights
        rest_diff = inputs['home_rest'] - inputs['away_rest']
        if abs(rest_diff) >= 3:
            if rest_diff > 0:
                insights.append(f"⚖️ **REST ADVANTAGE**: {home_base} has {rest_diff} more rest days")
            else:
                insights.append(f"⚖️ **REST ADVANTAGE**: {away_base} has {-rest_diff} more rest days")
        
        # Team strength insights
        if home_xg > away_xg + 0.3:
            insights.append(f"📈 **ATTACKING EDGE**: {home_base} has significantly stronger attack ({home_xg:.2f} vs {away_xg:.2f} xG)")
        elif away_xg > home_xg + 0.3:
            insights.append(f"📈 **ATTACKING EDGE**: {away_base} has significantly stronger attack ({away_xg:.2f} vs {home_xg:.2f} xG)")
        
        if home_xga < away_xga - 0.3:
            insights.append(f"🛡️ **DEFENSIVE EDGE**: {home_base} has much better defense ({home_xga:.2f} vs {away_xga:.2f} xGA)")
        elif away_xga < home_xga - 0.3:
            insights.append(f"🛡️ **DEFENSIVE EDGE**: {away_base} has much better defense ({away_xga:.2f} vs {home_xga:.2f} xGA)")
        
        # Match type analysis
        total_goals = probabilities['expected_home_goals'] + probabilities['expected_away_goals']
        if total_goals > 3.2:
            insights.append(f"⚽ **HIGH-SCORING EXPECTED**: {total_goals:.2f} total xG suggests goals")
        elif total_goals < 1.8:
            insights.append(f"🔒 **LOW-SCORING EXPECTED**: {total_goals:.2f} total xG suggests defensive battle")
        
        # Value insights
        value_bets = self.value_calculator.calculate_value_bets(probabilities, {
            'home': inputs['home_odds'], 'draw': inputs['draw_odds'], 
            'away': inputs['away_odds'], 'over_2.5': inputs['over_odds']
        })
        
        excellent_bets = [k for k, v in value_bets.items() if v['rating'] == 'excellent']
        good_bets = [k for k, v in value_bets.items() if v['rating'] == 'good']
        
        if excellent_bets:
            bet_names = [{'home': f"{home_base} Win", 'draw': "Draw", 'away': f"{away_base} Win", 'over_2.5': "Over 2.5 Goals"}[bet] for bet in excellent_bets]
            insights.append(f"💰 **EXCELLENT VALUE**: {', '.join(bet_names)} show strong positive EV")
        elif good_bets:
            bet_names = [{'home': f"{home_base} Win", 'draw': "Draw", 'away': f"{away_base} Win", 'over_2.5': "Over 2.5 Goals"}[bet] for bet in good_bets]
            insights.append(f"💰 **GOOD VALUE**: {', '.join(bet_names)} show positive EV")
        
        return insights

    def predict_match(self, inputs):
        """ENHANCED MAIN PREDICTION FUNCTION with all improvements"""
        # Validate team selection
        validation_errors = self.validate_team_selection(inputs['home_team'], inputs['away_team'])
        if validation_errors:
            return None, validation_errors, []
        
        # Get league for normalization
        league = self.get_team_data(inputs['home_team'])["league"]
        
        # Calculate per-match averages from user inputs
        home_xg_per_match = inputs['home_xg_total'] / 5
        home_xga_per_match = inputs['home_xga_total'] / 5
        away_xg_per_match = inputs['away_xg_total'] / 5
        away_xga_per_match = inputs['away_xga_total'] / 5
        
        # Apply modifiers
        home_xg_adj, home_xga_adj = self.injury_analyzer.apply_injury_impact(
            home_xg_per_match, home_xga_per_match,
            inputs['home_injuries'], inputs['home_rest'],
            self.get_team_data(inputs['home_team'])['form_trend']
        )
        
        away_xg_adj, away_xga_adj = self.injury_analyzer.apply_injury_impact(
            away_xg_per_match, away_xga_per_match,
            inputs['away_injuries'], inputs['away_rest'],
            self.get_team_data(inputs['away_team'])['form_trend']
        )
        
        # Apply MINIMAL advantage adjustment
        home_xg_ba, home_xga_ba, away_xg_ba, away_xga_ba = self.calculate_minimal_advantage(
            home_xg_adj, home_xga_adj, away_xg_adj, away_xga_adj
        )
        
        # ENHANCED: Calculate proper goal expectancy with FIXED normalization
        home_goal_exp, away_goal_exp = self.calculate_goal_expectancy(
            home_xg_ba, home_xga_ba, away_xg_ba, away_xga_ba, 
            inputs['home_team'], inputs['away_team'], league
        )
        
        # Calculate probabilities using proper goal expectancy
        probabilities = self.poisson_calculator.calculate_poisson_probabilities(home_goal_exp, away_goal_exp)
        
        # Calculate confidence
        confidence, confidence_factors = self.confidence_calculator.calculate_confidence(
            home_xg_per_match, away_xg_per_match,
            home_xga_per_match, away_xga_per_match, inputs
        )
        
        # Calculate context reliability
        rest_diff = abs(inputs['home_rest'] - inputs['away_rest'])
        reliability_score, reliability_level, reliability_advice = self.confidence_calculator.get_context_reliability(
            inputs['home_injuries'], inputs['away_injuries'], rest_diff, confidence
        )
        
        # Calculate value bets
        odds = {
            'home': inputs['home_odds'],
            'draw': inputs['draw_odds'],
            'away': inputs['away_odds'],
            'over_2.5': inputs['over_odds']
        }
        value_bets = self.value_calculator.calculate_value_bets(probabilities, odds)
        
        # Generate insights
        insights = self.generate_insights(inputs, probabilities, home_xg_per_match, away_xg_per_match, home_xga_per_match, away_xga_per_match)
        
        # Store calculation details for transparency
        home_adv_data = self.home_advantage.get_home_advantage(inputs['home_team'])
        away_adv_data = self.home_advantage.get_home_advantage(inputs['away_team'])
        home_injury_data = self.injury_analyzer.injury_weights[inputs['home_injuries']]
        away_injury_data = self.injury_analyzer.injury_weights[inputs['away_injuries']]
        
        calculation_details = {
            'home_xg_raw': home_xg_per_match,
            'home_xg_modified': home_xg_ba,
            'away_xg_raw': away_xg_per_match, 
            'away_xg_modified': away_xg_ba,
            'home_xga_raw': home_xga_per_match,
            'home_xga_modified': home_xga_ba,
            'away_xga_raw': away_xga_per_match,
            'away_xga_modified': away_xga_ba,
            'home_goal_expectancy': home_goal_exp,
            'away_goal_expectancy': away_goal_exp,
            'total_goals_lambda': home_goal_exp + away_goal_exp,
            'home_advantage_boost': home_adv_data['goals_boost'],
            'away_advantage_penalty': -away_adv_data['goals_boost'] * 0.5,
            'home_advantage_strength': home_adv_data['strength'],
            'away_advantage_strength': away_adv_data['strength'],
            'home_injury_impact': f"{((1-home_injury_data['attack_mult'])*100):.1f}% attack, {((1-home_injury_data['defense_mult'])*100):.1f}% defense",
            'away_injury_impact': f"{((1-away_injury_data['attack_mult'])*100):.1f}% attack, {((1-away_injury_data['defense_mult'])*100):.1f}% defense"
        }
        
        result = {
            'probabilities': probabilities,
            'expected_goals': {'home': probabilities['expected_home_goals'], 'away': probabilities['expected_away_goals']},
            'value_bets': value_bets,
            'confidence': confidence,
            'confidence_factors': confidence_factors,
            'reliability_score': reliability_score,
            'reliability_level': reliability_level,
            'reliability_advice': reliability_advice,
            'insights': insights,
            'per_match_stats': {
                'home_xg': home_xg_per_match,
                'home_xga': home_xga_per_match,
                'away_xg': away_xg_per_match,
                'away_xga': away_xga_per_match
            },
            'calculation_details': calculation_details
        }
        
        return result, [], []
        
    def get_available_leagues(self):
        """Get list of available leagues from the database"""
        leagues = set()
        for team_data in self.team_database.values():
            leagues.add(team_data["league"])
        return sorted(list(leagues))
