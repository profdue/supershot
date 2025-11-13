import json
import datetime
import pandas as pd

class WeightLogger:
    def __init__(self):
        self.predictions_log = []
    
    def log_prediction(self, match_data, weights_used, probabilities, actual_result=None):
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'match': f"{match_data['home']} vs {match_data['away']}",
            'league': match_data['league'],
            'weights_used': weights_used,
            'probabilities': probabilities,
            'actual_result': actual_result,
            'sample_sizes': {
                'home_matches': match_data['home_matches'],
                'away_matches': match_data['away_matches']
            },
            'injuries': {
                'home': match_data['home_injuries'],
                'away': match_data['away_injuries']
            },
            'context_factors': {
                'performance_weight': weights_used['performance'],
                'quality_weight': weights_used['quality'],
                'min_matches': min(match_data['home_matches'], match_data['away_matches']),
                'injury_gap': self._calculate_injury_gap(match_data['home_injuries'], match_data['away_injuries'])
            }
        }
        self.predictions_log.append(log_entry)
        
    def _calculate_injury_gap(self, home_injuries, away_injuries):
        injury_levels = {"None": 0, "Minor": 1, "Moderate": 2, "Significant": 3, "Crisis": 4}
        return abs(injury_levels[home_injuries] - injury_levels[away_injuries])
        
    def export_for_analysis(self):
        with open('weight_performance_log.json', 'w') as f:
            json.dump(self.predictions_log, f, indent=2)
            
    def load_historical_data(self, filepath):
        """Load historical data for backtesting"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
            
    def analyze_weight_performance(self):
        """Basic analysis of weight performance"""
        if not self.predictions_log:
            return "No prediction data available"
            
        df = pd.DataFrame(self.predictions_log)
        
        # Group by weight combinations and calculate accuracy
        weight_groups = df.groupby([
            df['weights_used'].apply(lambda x: f"{x['performance']:.2f}/{x['quality']:.2f}")
        ])
        
        results = {}
        for weight_combo, group in weight_groups:
            if group['actual_result'].notna().any():
                accuracy = self._calculate_accuracy(group)
                results[weight_combo] = {
                    'count': len(group),
                    'accuracy': accuracy,
                    'avg_performance_weight': group['context_factors'].apply(lambda x: x['performance_weight']).mean()
                }
                
        return results
    
    def _calculate_accuracy(self, group):
        """Calculate prediction accuracy for a group"""
        correct_predictions = 0
        total_predictions = 0
        
        for _, row in group.iterrows():
            if pd.notna(row['actual_result']):
                predicted_winner = max(row['probabilities'], key=row['probabilities'].get)
                if predicted_winner == row['actual_result']:
                    correct_predictions += 1
                total_predictions += 1
                
        return correct_predictions / total_predictions if total_predictions > 0 else 0
