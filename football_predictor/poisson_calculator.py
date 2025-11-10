import numpy as np
from scipy.stats import poisson

class PoissonCalculator:
    def __init__(self):
        self.max_goals = 8
        
    def calculate_poisson_probabilities(self, home_goal_exp, away_goal_exp):
        """Calculate probabilities using proper goal expectancy"""
        # Initialize probability arrays
        home_probs = [poisson.pmf(i, home_goal_exp) for i in range(self.max_goals)]
        away_probs = [poisson.pmf(i, away_goal_exp) for i in range(self.max_goals)]
        
        # Calculate outcome probabilities
        home_win = 0
        draw = 0
        away_win = 0
        
        for i in range(self.max_goals):
            for j in range(self.max_goals):
                prob = home_probs[i] * away_probs[j]
                if i > j:
                    home_win += prob
                elif i == j:
                    draw += prob
                else:
                    away_win += prob
        
        # Normalize to account for truncated distribution
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total
        
        # Calculate over/under probabilities using combined goal expectancy
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
        
    def predict_scorelines(self, home_goal_exp, away_goal_exp, top_n=3):
        """Predict most likely scorelines"""
        scorelines = []
        
        for i in range(5):  # Home goals
            for j in range(5):  # Away goals
                prob = (poisson.pmf(i, home_goal_exp) * 
                       poisson.pmf(j, away_goal_exp))
                scorelines.append((f"{i}-{j}", prob))
                
        # Sort by probability and return top N
        scorelines.sort(key=lambda x: x[1], reverse=True)
        return [scoreline[0] for scoreline in scorelines[:top_n]]
