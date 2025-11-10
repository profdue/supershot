import pandas as pd
from .config import HOME_ADVANTAGE_BASE

class HomeAdvantageCalculator:
    def __init__(self, home_advantage_df):
        self.home_advantage_df = home_advantage_df
        
    def get_home_advantage(self, team_key):
        """Get home advantage metrics for a specific team"""
        team_data = self.home_advantage_df[
            self.home_advantage_df['team_key'] == team_key
        ]
        
        if team_data.empty:
            print(f"⚠️ No home advantage data found for {team_key}")
            return {
                'ppg_diff': 0.0,
                'goals_boost': HOME_ADVANTAGE_BASE,
                'strength': 'moderate'
            }
            
        return {
            'ppg_diff': team_data['ppg_diff'].iloc[0],
            'goals_boost': team_data['goals_boost'].iloc[0],
            'strength': team_data['strength'].iloc[0]
        }
        
    def calculate_home_boost(self, home_team_key, away_team_key):
        """Calculate net home advantage considering both teams"""
        home_adv = self.get_home_advantage(home_team_key)
        away_adv = self.get_home_advantage(away_team_key.replace('Away', 'Home'))
        
        # Base home advantage minus away team's ability to negate it
        net_boost = home_adv['goals_boost'] - (away_adv['goals_boost'] * 0.3)
        
        return max(net_boost, 0.05)  # Minimum boost of 0.05
        
    def get_strength_level(self, team_key):
        """Get home advantage strength level"""
        adv = self.get_home_advantage(team_key)
        return adv['strength']
