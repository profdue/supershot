class InjuryAnalyzer:
    def __init__(self):
        # ENHANCED Injury impact weights - defense injuries hit harder to increase goals
        self.injury_weights = {
            "None": {
                "attack_mult": 1.00, 
                "defense_mult": 1.00, 
                "description": "Full squad available",
                "key_players_missing": 0,
                "player_type": "None",
                "impact_level": "None"
            },
            "Minor": {
                "attack_mult": 0.95, 
                "defense_mult": 0.94,  # Defense hit slightly harder
                "description": "1-2 rotational/fringe players missing",
                "key_players_missing": 0,
                "player_type": "Rotational",
                "impact_level": "Low"
            },
            "Moderate": {
                "attack_mult": 0.90,  # Reduced from 0.88
                "defense_mult": 0.85,  # Defense hit harder (was 0.90)
                "description": "1-2 key starters missing", 
                "key_players_missing": 1,
                "player_type": "Key Starters",
                "impact_level": "Medium"
            },
            "Significant": {
                "attack_mult": 0.82,  # Reduced from 0.78
                "defense_mult": 0.72,  # Defense hit much harder (was 0.82)
                "description": "3-4 key starters missing",
                "key_players_missing": 3, 
                "player_type": "Key Starters",
                "impact_level": "High"
            },
            "Crisis": {
                "attack_mult": 0.70,  # Reduced from 0.65
                "defense_mult": 0.58,  # Defense crushed (was 0.72)
                "description": "5+ key starters missing",
                "key_players_missing": 5,
                "player_type": "Key Starters",
                "impact_level": "Severe"
            }
        }
        
        # Fatigue multipliers
        self.fatigue_multipliers = {
            2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96, 
            7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
            12: 1.03, 13: 1.03, 14: 1.03
        }
        
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
