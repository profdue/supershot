import pandas as pd
from .config import SQUAD_VALUE_TIERS

class TeamQualityAnalyzer:
    def __init__(self, team_quality_df):
        self.team_quality_df = team_quality_df
        
    def get_team_quality(self, team_name):
        """Get quality metrics for a specific team"""
        team_data = self.team_quality_df[
            self.team_quality_df['team_base'] == team_name
        ]
        
        if team_data.empty:
            print(f"⚠️ No quality data found for {team_name}")
            return None
            
        return {
            'elo': team_data['elo'].iloc[0],
            'squad_value': team_data['squad_value'].iloc[0],
            'structural_tier': team_data['structural_tier'].iloc[0]
        }
        
    def calculate_quality_difference(self, team1, team2):
        """Calculate quality difference between two teams"""
        qual1 = self.get_team_quality(team1)
        qual2 = self.get_team_quality(team2)
        
        if not qual1 or not qual2:
            return 0
            
        # Elo difference (normalized)
        elo_diff = (qual1['elo'] - qual2['elo']) / 100
        
        # Squad value difference (log scale)
        val_diff = (
            (qual1['squad_value'] - qual2['squad_value']) / 
            max(qual1['squad_value'], qual2['squad_value'])
        )
        
        # Combined quality difference
        quality_diff = (elo_diff * 0.7) + (val_diff * 0.3)
        
        return quality_diff
        
    def get_structural_tier(self, team_name):
        """Get structural tier for a team"""
        qual = self.get_team_quality(team_name)
        return qual['structural_tier'] if qual else 'average'
