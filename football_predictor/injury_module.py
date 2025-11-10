from .config import INJURY_WEIGHTS, FATIGUE_MULTIPLIERS

class InjuryAnalyzer:
    def __init__(self):
        self.injury_weights = INJURY_WEIGHTS
        self.fatigue_multipliers = FATIGUE_MULTIPLIERS
        
    def apply_injury_impact(self, xg_for, xg_against, injury_level, rest_days, form_trend):
        """ENHANCED: Apply modifiers with improved injury impact"""
        injury_data = self.injury_weights[injury_level]
        
        # Apply injury impacts
        attack_mult = injury_data["attack_mult"]
        defense_mult = injury_data["defense_mult"]
        
        # Apply fatigue impact
        fatigue_mult = self.fatigue_multipliers.get(rest_days, 1.0)
        
        # Apply form trend
        form_mult = 1 + (form_trend * 0.2)
        
        # Apply all modifiers
        xg_modified = xg_for * attack_mult * fatigue_mult * form_mult
        xga_modified = xg_against * defense_mult * fatigue_mult * form_mult
        
        return max(0.1, xg_modified), max(0.1, xga_modified)
        
    def get_injury_description(self, injury_level):
        """Get description for injury level"""
        if injury_level in self.injury_weights:
            return self.injury_weights[injury_level]['description']
        return "Unknown injury level"
        
    def calculate_injury_differential(self, team1_injury, team2_injury):
        """Calculate net injury impact between two teams"""
        if team1_injury not in self.injury_weights:
            team1_injury = "None"
        if team2_injury not in self.injury_weights:
            team2_injury = "None"
            
        attack_diff = (
            self.injury_weights[team1_injury]['attack_mult'] - 
            self.injury_weights[team2_injury]['attack_mult']
        )
        defense_diff = (
            self.injury_weights[team1_injury]['defense_mult'] - 
            self.injury_weights[team2_injury]['defense_mult']
        )
        
        return (attack_diff + defense_diff) / 2
        
    def get_impact_level(self, injury_level):
        """Get impact level for injury"""
        if injury_level in self.injury_weights:
            return self.injury_weights[injury_level]['impact_level']
        return "None"
