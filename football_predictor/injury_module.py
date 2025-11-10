from .config import INJURY_WEIGHTS

class InjuryAnalyzer:
    def __init__(self):
        self.injury_weights = INJURY_WEIGHTS
        
    def apply_injury_impact(self, xg_for, xg_against, injury_level):
        """Apply injury impact to expected goals"""
        if injury_level not in self.injury_weights:
            print(f"⚠️ Unknown injury level: {injury_level}, using 'None'")
            injury_level = "None"
            
        weights = self.injury_weights[injury_level]
        
        adjusted_xg_for = xg_for * weights['attack_mult']
        adjusted_xg_against = xg_against * weights['defense_mult']
        
        return adjusted_xg_for, adjusted_xg_against
        
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
