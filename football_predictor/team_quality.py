import pandas as pd

class TeamQualityAnalyzer:
    def __init__(self, team_quality_df):
        self.team_quality_df = team_quality_df
        
    def get_team_quality(self, team_name):
        """Get quality metrics for a specific team with robust lookup"""
        # Extract base name if needed
        base_name = self._extract_base_name(team_name)
        
        # Case-insensitive lookup
        team_data = self.team_quality_df[
            self.team_quality_df['team_base'].str.lower() == base_name.lower()
        ]
        
        if team_data.empty:
            print(f"⚠️ No quality data found for {base_name} (searched for: {team_name})")
            # Return sensible defaults instead of None to prevent crashes
            return {
                'elo': 1600,
                'squad_value': 100000000,
                'structural_tier': 'average',
                'base_name': base_name
            }
            
        return {
            'elo': team_data['elo'].iloc[0],
            'squad_value': team_data['squad_value'].iloc[0],
            'structural_tier': team_data['structural_tier'].iloc[0],
            'base_name': base_name
        }
    
    def _extract_base_name(self, team_name):
        """Extract base team name from any format"""
        if " Home" in team_name:
            return team_name.replace(" Home", "")
        elif " Away" in team_name:
            return team_name.replace(" Away", "")
        return team_name
        
    def calculate_quality_difference(self, team1, team2):
        """Calculate quality difference between two teams"""
        qual1 = self.get_team_quality(team1)
        qual2 = self.get_team_quality(team2)
        
        # Elo difference (normalized)
        elo_diff = (qual1['elo'] - qual2['elo']) / 100
        
        # Squad value difference (log scale)
        val_diff = (
            (qual1['squad_value'] - qual2['squad_value']) / 
            max(qual1['squad_value'], qual2['squad_value'], 1)  # Avoid division by zero
        )
        
        # Combined quality difference
        quality_diff = (elo_diff * 0.7) + (val_diff * 0.3)
        
        return quality_diff
        
    def get_structural_tier(self, team_name):
        """Get structural tier for a team"""
        qual = self.get_team_quality(team_name)
        return qual['structural_tier']
