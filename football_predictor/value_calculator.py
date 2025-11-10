from .config import VALUE_THRESHOLDS

class ValueCalculator:
    def __init__(self):
        self.value_thresholds = VALUE_THRESHOLDS
        
    def calculate_true_value(self, probability, odds):
        """Proper value calculation"""
        if odds <= 1.0:
            return {'ev': -1, 'kelly_fraction': 0, 'value_ratio': 0, 'rating': 'invalid', 'implied_prob': 0, 'model_prob': probability}
        
        # Proper Expected Value calculation
        ev = (probability * (odds - 1)) - (1 - probability)
        
        # Kelly Criterion
        kelly_fraction = (probability * odds - 1) / (odds - 1) if probability * odds > 1 else 0
        
        value_ratio = probability * odds
        
        # Realistic value rating
        if ev > self.value_thresholds["excellent"]["ev"] and value_ratio > self.value_thresholds["excellent"]["value_ratio"]:
            rating = "excellent"
        elif ev > self.value_thresholds["good"]["ev"] and value_ratio > self.value_thresholds["good"]["value_ratio"]:
            rating = "good"
        elif ev > self.value_thresholds["fair"]["ev"] and value_ratio > self.value_thresholds["fair"]["value_ratio"]:
            rating = "fair"
        else:
            rating = "poor"
        
        return {
            'ev': ev,
            'kelly_fraction': max(0, kelly_fraction),
            'value_ratio': value_ratio,
            'rating': rating,
            'implied_prob': 1 / odds,
            'model_prob': probability
        }

    def calculate_value_bets(self, probabilities, odds):
        """Calculate value bets for all markets"""
        value_bets = {}
        
        value_bets['home'] = self.calculate_true_value(probabilities['home_win'], odds['home'])
        value_bets['draw'] = self.calculate_true_value(probabilities['draw'], odds['draw'])
        value_bets['away'] = self.calculate_true_value(probabilities['away_win'], odds['away'])
        value_bets['over_2.5'] = self.calculate_true_value(probabilities['over_2.5'], odds['over_2.5'])
        
        return value_bets
