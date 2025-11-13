import pandas as pd

class HomeAdvantageCalculator:
    def __init__(self, home_advantage_df):
        self.home_advantage_df = home_advantage_df
        
    def get_home_advantage(self, team_key):
        """Get home advantage metrics for a specific team - FIXED FOR YOUR DATA"""
        print(f"🔍 HOME ADV LOOKUP - Looking for: {team_key}")
        
        # Extract base name from team_key (e.g., "Arsenal Home" → "Arsenal")
        base_name = team_key.replace(" Home", "").replace(" Away", "")
        print(f"🔍 HOME ADV LOOKUP - Base name: {base_name}")
        
        # Check what columns we actually have
        print(f"🔍 HOME ADV COLUMNS: {list(self.home_advantage_df.columns)}")
        
        # Look up by base_name since your data uses team_base
        team_data = self.home_advantage_df[
            self.home_advantage_df['team_base'] == base_name
        ]
        
        if team_data.empty:
            print(f"⚠️ No home advantage data found for {base_name}")
            return {
                'ppg_diff': 0.0,
                'goals_boost': 0.3 * 0.33,  # Default moderate boost
                'strength': 'moderate'
            }
        
        # ✅ USE YOUR ACTUAL COLUMN NAMES
        home_ppg = team_data['home_ppg'].iloc[0]
        away_ppg = team_data['away_ppg'].iloc[0]
        performance_diff = home_ppg - away_ppg  # Calculate the difference
        strength = team_data['advantage_strength'].iloc[0]
        goals_boost = performance_diff * 0.33  # Convert PPG difference to goals
        
        print(f"✅ HOME ADV FOUND - {base_name}: {home_ppg:.2f} home, {away_ppg:.2f} away, diff: {performance_diff:.2f}")
        
        return {
            'ppg_diff': performance_diff,
            'goals_boost': goals_boost,
            'strength': strength
        }
        
    def calculate_home_boost(self, home_team_key, away_team_key):
        """Calculate net home advantage considering both teams"""
        home_adv = self.get_home_advantage(home_team_key)
        
        # For away team, get their home data to see how strong they are at home
        away_base = away_team_key.replace(' Away', '')
        away_home_key = f"{away_base} Home"
        away_adv = self.get_home_advantage(away_home_key)
        
        # Base home advantage minus away team's ability to negate it
        net_boost = home_adv['goals_boost'] - (away_adv['goals_boost'] * 0.3)
        
        return max(net_boost, 0.05)  # Minimum boost of 0.05
        
    def get_strength_level(self, team_key):
        """Get home advantage strength level"""
        adv = self.get_home_advantage(team_key)
        return adv['strength']
    
    def get_team_home_performance(self, team_key):
        """Get team's home performance metrics"""
        base_name = team_key.replace(" Home", "").replace(" Away", "")
        
        team_data = self.home_advantage_df[
            self.home_advantage_df['team_base'] == base_name
        ]
        
        if team_data.empty:
            return {
                'home_ppg': 1.8,  # Default average
                'away_ppg': 1.2,  # Default average  
                'performance_difference': 0.6,
                'advantage_strength': 'moderate'
            }
        
        home_ppg = team_data['home_ppg'].iloc[0]
        away_ppg = team_data['away_ppg'].iloc[0]
        performance_diff = home_ppg - away_ppg
        
        return {
            'home_ppg': home_ppg,
            'away_ppg': away_ppg,
            'performance_difference': performance_diff,
            'advantage_strength': team_data['advantage_strength'].iloc[0]
        }
