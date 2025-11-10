# football_predictor/data_loader.py
import pandas as pd
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._teams_df = None
        self._quality_df = None
        self._home_advantage_df = None
        self._leagues_df = None
        
    def load_teams(self) -> pd.DataFrame:
        """Load main teams database"""
        if self._teams_df is None:
            try:
                self._teams_df = pd.read_csv(os.path.join(self.data_dir, "teams.csv"))
                logger.info(f"Loaded {len(self._teams_df)} teams from database")
            except FileNotFoundError:
                logger.error("teams.csv not found - using empty dataframe")
                self._teams_df = pd.DataFrame()
        return self._teams_df
    
    def load_team_quality(self) -> pd.DataFrame:
        """Load team quality database"""
        if self._quality_df is None:
            try:
                self._quality_df = pd.read_csv(os.path.join(self.data_dir, "team_quality.csv"))
                logger.info(f"Loaded quality data for {len(self._quality_df)} teams")
            except FileNotFoundError:
                logger.error("team_quality.csv not found - using empty dataframe")
                self._quality_df = pd.DataFrame()
        return self._quality_df
    
    def load_home_advantage(self) -> pd.DataFrame:
        """Load home advantage data"""
        if self._home_advantage_df is None:
            try:
                self._home_advantage_df = pd.read_csv(os.path.join(self.data_dir, "home_advantage.csv"))
                logger.info(f"Loaded home advantage data for {len(self._home_advantage_df)} teams")
            except FileNotFoundError:
                logger.error("home_advantage.csv not found - using empty dataframe")
                self._home_advantage_df = pd.DataFrame()
        return self._home_advantage_df
    
    def get_team_data(self, team_name: str) -> Dict[str, Any]:
        """Get data for a specific team"""
        teams_df = self.load_teams()
        
        if teams_df.empty:
            return self._get_default_team_data()
        
        team_data = teams_df[teams_df['team_key'] == team_name]
        
        if team_data.empty:
            logger.warning(f"Team '{team_name}' not found in database")
            return self._get_default_team_data()
        
        data = team_data.iloc[0].to_dict()
        
        # Calculate per-match averages
        data['last_5_xg_per_match'] = data['last_5_xg_total'] / 5
        data['last_5_xga_per_match'] = data['last_5_xga_total'] / 5
        
        return data
    
    def get_team_quality_data(self, team_base_name: str) -> Dict[str, Any]:
        """Get quality data for a team"""
        quality_df = self.load_team_quality()
        
        if quality_df.empty:
            return self._get_default_quality_data()
        
        team_data = quality_df[quality_df['team_base'] == team_base_name]
        
        if team_data.empty:
            logger.warning(f"No quality data for '{team_base_name}'")
            return self._get_default_quality_data()
        
        return team_data.iloc[0].to_dict()
    
    def get_home_advantage_data(self, team_name: str) -> Dict[str, Any]:
        """Get home advantage data for a team"""
        advantage_df = self.load_home_advantage()
        
        if advantage_df.empty:
            return self._get_default_home_advantage_data()
        
        team_data = advantage_df[advantage_df['team_key'] == team_name]
        
        if team_data.empty:
            logger.warning(f"No home advantage data for '{team_name}'")
            return self._get_default_home_advantage_data()
        
        return team_data.iloc[0].to_dict()
    
    def _get_default_team_data(self) -> Dict[str, Any]:
        return {
            'league': 'Unknown', 
            'last_5_xg_total': 7.50,
            'last_5_xga_total': 7.50,
            'form_trend': 0.00,
            'last_5_xg_per_match': 1.50,
            'last_5_xga_per_match': 1.50
        }
    
    def _get_default_quality_data(self) -> Dict[str, Any]:
        return {
            'elo': 1600,
            'squad_value': 200000000,
            'structural_tier': 'average'
        }
    
    def _get_default_home_advantage_data(self) -> Dict[str, Any]:
        return {
            'ppg_diff': 0.30,
            'goals_boost': 0.30 * 0.33,
            'strength': 'moderate'
        }
    
    def get_available_leagues(self) -> list:
        """Get list of available leagues"""
        teams_df = self.load_teams()
        if teams_df.empty:
            return []
        return sorted(teams_df['league'].unique().tolist())
    
    def get_teams_by_league(self, league: str, team_type: str = "all") -> list:
        """Get teams in a specific league"""
        teams_df = self.load_teams()
        if teams_df.empty:
            return []
        
        league_teams = teams_df[teams_df['league'] == league]
        
        if team_type == "all":
            return sorted(league_teams['team_key'].tolist())
        elif team_type == "home":
            home_teams = league_teams[league_teams['team_key'].str.contains(" Home")]
            return sorted(home_teams['team_key'].tolist())
        elif team_type == "away":
            away_teams = league_teams[league_teams['team_key'].str.contains(" Away")]
            return sorted(away_teams['team_key'].tolist())
        
        return []
