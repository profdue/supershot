# football_predictor/injury_module.py
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class InjuryModule:
    def __init__(self, team_quality_module):
        self.team_quality = team_quality_module
    
    def apply_injury_modifiers(self, base_xg: float, base_xga: float, 
                             injury_level: str, team_name: str) -> Tuple[float, float]:
        """Apply injury modifiers with team quality scaling"""
        from .config import INJURY_WEIGHTS
        
        if injury_level not in INJURY_WEIGHTS:
            logger.warning(f"Unknown injury level: {injury_level}")
            return base_xg, base_xga
        
        injury_data = INJURY_WEIGHTS[injury_level]
        team_quality = self.team_quality.get_team_quality(team_name)
        
        # Base injury impacts
        attack_mult = injury_data["attack_mult"]
        defense_mult = injury_data["defense_mult"]
        
        # Apply team quality scaling
        quality_scaling = self.team_quality.get_quality_scaling_factor(team_quality)
        attack_mult = 1 - ((1 - attack_mult) / quality_scaling)
        defense_mult = 1 - ((1 - defense_mult) / quality_scaling)
        
        xg_modified = base_xg * attack_mult
        xga_modified = base_xga * defense_mult
        
        logger.debug(f"Injury modifiers for {team_name}: {injury_level} -> "
                    f"attack: {attack_mult:.3f}, defense: {defense_mult:.3f}, "
                    f"quality: {team_quality}")
        
        return max(0.1, xg_modified), max(0.1, xga_modified)
    
    def get_injury_description(self, injury_level: str) -> str:
        """Get description for injury level"""
        from .config import INJURY_WEIGHTS
        return INJURY_WEIGHTS.get(injury_level, {}).get("description", "Unknown")
    
    def get_injury_impact(self, injury_level: str) -> Tuple[float, float]:
        """Get base injury impact without quality scaling"""
        from .config import INJURY_WEIGHTS
        injury_data = INJURY_WEIGHTS.get(injury_level, INJURY_WEIGHTS["None"])
        return injury_data["attack_mult"], injury_data["defense_mult"]
