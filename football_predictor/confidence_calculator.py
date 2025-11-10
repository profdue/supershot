import numpy as np

class ConfidenceCalculator:
    def __init__(self, injury_analyzer, home_advantage_calculator):
        self.injury_analyzer = injury_analyzer
        self.home_advantage_calculator = home_advantage_calculator
        self.confidence_weights = {
            'data_quality': 0.18,
            'predictability': 0.18, 
            'injury_stability': 0.22,
            'rest_balance': 0.12,
            'home_advantage_consistency': 0.30
        }
        
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        """ENHANCED: Calculate confidence with injury and home advantage factors"""
        factors = {}
        
        # Data quality factor
        data_quality = min(1.0, (home_xg + away_xg + home_xga + away_xga) / 5.4)
        factors['data_quality'] = data_quality
        
        # Predictability factor
        predictability = 1 - (abs(home_xg - away_xg) / max(home_xg, away_xg, 0.1))
        factors['predictability'] = predictability
        
        # ENHANCED: Injury impact factor with player type consideration
        home_injury_data = self.injury_analyzer.injury_weights[inputs['home_injuries']]
        away_injury_data = self.injury_analyzer.injury_weights[inputs['away_injuries']]
        
        # More severe penalty for key starter injuries
        home_injury_severity = (1 - home_injury_data["attack_mult"]) * (1.2 if home_injury_data["player_type"] == "Key Starters" else 0.8)
        away_injury_severity = (1 - away_injury_data["attack_mult"]) * (1.2 if away_injury_data["player_type"] == "Key Starters" else 0.8)
        
        injury_factor = 1 - (home_injury_severity + away_injury_severity) / 2
        factors['injury_stability'] = injury_factor
        
        # Rest balance factor
        rest_diff = abs(inputs['home_rest'] - inputs['away_rest'])
        rest_factor = 1 - (rest_diff * 0.03)
        factors['rest_balance'] = rest_factor
        
        # Home advantage consistency factor (ENHANCED)
        home_adv_data = self.home_advantage_calculator.get_home_advantage(inputs['home_team'])
        away_adv_data = self.home_advantage_calculator.get_home_advantage(inputs['away_team'])
        
        # Extreme home advantages are less predictable
        home_adv_consistency = 1 - (abs(home_adv_data['ppg_diff']) * 0.08)
        away_adv_consistency = 1 - (abs(away_adv_data['ppg_diff']) * 0.08)
        factors['home_advantage_consistency'] = (home_adv_consistency + away_adv_consistency) / 2
        
        # Calculate weighted confidence using logistic scaling
        weighted_sum = sum(factors[factor] * self.confidence_weights[factor] for factor in factors)
        confidence_score = 1 / (1 + np.exp(-10 * (weighted_sum - 0.5)))
        
        base_confidence = 55
        adjustment = confidence_score * 30
        
        confidence = base_confidence + adjustment
        return min(85, max(45, confidence)), factors
        
    def get_context_reliability(self, home_injury, away_injury, rest_diff, confidence):
        """Calculate context reliability for predictions"""
        reliability_score = 100
        
        # Injury reliability penalty
        if home_injury in ["Significant", "Crisis"] and away_injury in ["Significant", "Crisis"]:
            reliability_score -= 25
        elif home_injury in ["Moderate", "Significant", "Crisis"] or away_injury in ["Moderate", "Significant", "Crisis"]:
            reliability_score -= 15
        elif home_injury == "Minor" or away_injury == "Minor":
            reliability_score -= 5
            
        # Rest disparity penalty  
        if rest_diff >= 5:
            reliability_score -= 15
        elif rest_diff >= 3:
            reliability_score -= 8
            
        # Confidence-based adjustment
        if confidence < 70:
            reliability_score -= 10
        elif confidence > 85:
            reliability_score += 5
            
        reliability_score = max(50, min(95, reliability_score))
        
        # Categorize reliability
        if reliability_score >= 80:
            return reliability_score, "🟢 HIGH RELIABILITY", "Trust model predictions - optimal conditions"
        elif reliability_score >= 65:
            return reliability_score, "🟡 MODERATE RELIABILITY", "Use normal discretion - some context factors present"
        else:
            return reliability_score, "🔴 LOW RELIABILITY", "Exercise caution - significant context factors may distort predictions"
