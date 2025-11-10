# football_predictor/team_quality.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TeamQuality:
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def get_team_quality(self, team_name: str, current_ppg: float = None) -> str:
        """Hybrid structural + dynamic team quality classification"""
        base_team = self._get_team_base_name(team_name)
        
        try:
            quality_data = self.data_loader.get_team_quality_data(base_team)
            
            # Use provided PPG or default based on structural tier
            if current_ppg is None:
                current_ppg = self._get_default_ppg(quality_data['structural_tier'])
            
            # Hybrid scoring
            structural_score = self._calculate_structural_score(quality_data, current_ppg)
            
            # Classification
            return self._classify_quality(structural_score)
            
        except Exception as e:
            logger.error(f"Error calculating quality for {team_name}: {e}")
            return "average"
    
    def _get_team_base_name(self, team_name: str) -> str:
        """Extract base team name without Home/Away suffix"""
        if " Home" in team_name:
            return team_name.replace(" Home", "")
        elif " Away" in team_name:
            return team_name.replace(" Away", "")
        return team_name
    
    def _get_default_ppg(self, structural_tier: str) -> float:
        """Get default PPG based on structural tier"""
        return {
            "elite": 2.0, 
            "strong": 1.7, 
            "average": 1.3, 
            "weak": 0.8
        }[structural_tier]
    
    def _calculate_structural_score(self, quality_data: Dict[str, Any], current_ppg: float) -> float:
        """Calculate hybrid structural score"""
        return (
            (quality_data['elo'] / 2000) * 0.4 +
            (quality_data['squad_value'] / 1000000000) * 0.4 +
            (current_ppg / 2.5) * 0.2
        )
    
    def _classify_quality(self, structural_score: float) -> str:
        """Classify team into quality tier"""
        if structural_score >= 0.85:
            return "elite"
        elif structural_score >= 0.70:
            return "strong"
        elif structural_score >= 0.55:
            return "average"
        else:
            return "weak"
    
    def get_quality_scaling_factor(self, quality: str) -> float:
        """Get injury scaling factor based on team quality"""
        from .config import QUALITY_SCALING
        return QUALITY_SCALING.get(quality, 1.0)
