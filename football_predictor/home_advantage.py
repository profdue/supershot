import pandas as pd

class HomeAdvantageCalculator:
    def __init__(self, home_advantage_df):
        self.home_advantage_df = home_advantage_df
        
    def get_home_advantage(self, team_key):
        """Get home advantage metrics for a specific team - FIXED FOR YOUR DATA STRUCTURE"""
        team_data = self.home_advantage_df[
            self.home_advantage_df['team_key'] == team_key
        ]
        
        if team_data.empty:
            print(f"⚠️ No home advantage data found for {team_key}")
            return {
                'ppg_diff': 0.0,
                'goals_boost': 0.3 * 0.33,  # Default moderate boost
                'strength': 'moderate'
            }
        
        # ✅ FIXED: Use YOUR column names and calculate goals_boost
        performance_diff = team_data['performance_difference'].iloc[0]
        strength = team_data['advantage_strength'].iloc[0]
        goals_boost = performance_diff * 0.33  # Convert PPG difference to goals
        
        return {
            'ppg_diff': performance_diff,  # Map to expected name
            'goals_boost': goals_boost,    # Calculate from performance_diff
            'strength': strength           # Map to expected name
        }
        
    def calculate_home_boost(self, home_team_key, away_team_key):
        """Calculate net home advantage considering both teams"""
        home_adv = self.get_home_advantage(home_team_key)
        
        # For away team, get their home data to see how strong they are at home
        away_base = away_team_key.replace(' Away', '')
        away_home_key = f"{away_base} Home"
        away_adv = self.get_home_advantage(away_home_key)
        
        # Base home advantage minus away team's ability to negate it
        # Strong home teams are less affected by away disadvantage
        net_boost = home_adv['goals_boost'] - (away_adv['goals_boost'] * 0.3)
        
        return max(net_boost, 0.05)  # Minimum boost of 0.05
        
    def get_strength_level(self, team_key):
        """Get home advantage strength level"""
        adv = self.get_home_advantage(team_key)
        return adv['strength']
    
    def get_team_home_performance(self, team_key):
        """Get team's home performance metrics - ADDED FOR COMPLETENESS"""
        team_data = self.home_advantage_df[
            self.home_advantage_df['team_key'] == team_key
        ]
        
        if team_data.empty:
            return {
                'home_ppg': 1.8,  # Default average
                'away_ppg': 1.2,  # Default average  
                'performance_difference': 0.6,
                'advantage_strength': 'moderate'
            }
        
        return {
            'home_ppg': team_data['home_ppg'].iloc[0],
            'away_ppg': team_data['away_ppg'].iloc[0],
            'performance_difference': team_data['performance_difference'].iloc[0],
            'advantage_strength': team_data['advantage_strength'].iloc[0]
        }
