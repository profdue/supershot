# football_predictor/home_advantage.py
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class HomeAdvantage:
    def __init__(self, data_loader, team_quality_module):
        self.data_loader = data_loader
        self.team_quality = team_quality_module
    
    def get_home_advantage_boost(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """Get quality-adjusted home advantage boosts"""
        home_adv_data = self.data_loader.get_home_advantage_data(home_team)
        away_adv_data = self.data_loader.get_home_advantage_data(away_team)
        
        # Get team qualities
        home_quality = self.team_quality.get_team_quality(home_team)
        away_quality = self.team_quality.get_team_quality(away_team)
        
        # Home advantage scaling based on opponent quality
        from .config import OPPONENT_QUALITY_FACTOR
        base_home_boost = home_adv_data['goals_boost']
        opponent_factor = OPPONENT_QUALITY_FACTOR.get(away_quality, 1.0)
        adjusted_home_boost = base_home_boost * opponent_factor
        
        # Away penalty also scales with home team quality
        base_away_penalty = -away_adv_data['goals_boost'] * 0.5
        
        home_quality_factor = {
            "elite": 1.2,    # Stronger penalty when elite team is home
            "strong": 1.1,
            "average": 1.0,
            "weak": 0.8
        }.get(home_quality, 1.0)
        
        adjusted_away_penalty = base_away_penalty * home_quality_factor
        
        logger.debug(f"Home advantage: {home_team} (+{adjusted_home_boost:.3f}), "
                    f"{away_team} ({adjusted_away_penalty:+.3f})")
        
        return adjusted_home_boost, adjusted_away_penalty
    
    def get_home_advantage_strength(self, team_name: str) -> str:
        """Get home advantage strength description"""
        adv_data = self.data_loader.get_home_advantage_data(team_name)
        return adv_data.get('strength', 'moderate')
