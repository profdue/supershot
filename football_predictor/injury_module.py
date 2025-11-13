class InjuryAnalyzer:
    def __init__(self):
        # MORE CONSERVATIVE injury impacts (7-20% vs 10-28%)
        self.injury_weights = {
            "None": {
                "attack_mult": 1.00, "defense_mult": 1.00,
                "description": "Full squad available", "impact_level": "None"
            },
            "Minor": {
                "attack_mult": 0.97, "defense_mult": 0.96,  # 3-4% impact
                "description": "1-2 rotational players missing", "impact_level": "Low"
            },
            "Moderate": {
                "attack_mult": 0.93, "defense_mult": 0.90,  # 7-10% impact  
                "description": "1-2 key starters missing", "impact_level": "Medium"
            },
            "Significant": {
                "attack_mult": 0.88, "defense_mult": 0.85,  # 12-15% impact
                "description": "3-4 key starters missing", "impact_level": "High"
            },
            "Crisis": {
                "attack_mult": 0.80, "defense_mult": 0.78,  # 20-22% impact
                "description": "5+ key starters missing", "impact_level": "Severe"
            }
        }

        self.fatigue_multipliers = {
            2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96,
            7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
            12: 1.03, 13: 1.03, 14: 1.03
        }

    def apply_injury_impact(self, xg_for, xg_against, injury_level, rest_days, form_trend):
        injury_data = self.injury_weights.get(injury_level, self.injury_weights['None'])
        attack_mult = injury_data["attack_mult"]
        defense_mult = injury_data["defense_mult"]
        fatigue_mult = self.fatigue_multipliers.get(rest_days, 1.0)
        form_mult = 1 + (form_trend * 0.15)  # Reduced form impact

        # Attack: conservative reduction
        xg_modified = xg_for * attack_mult * fatigue_mult * form_mult
        
        # Defense: conservative weakening  
        xga_modified = xg_against * (2 - defense_mult) * fatigue_mult * form_mult

        return max(0.3, xg_modified), max(0.3, xga_modified)

    def get_injury_description(self, injury_level):
        return self.injury_weights.get(injury_level, self.injury_weights['None'])['description']

    def get_impact_level(self, injury_level):
        return self.injury_weights.get(injury_level, self.injury_weights['None'])['impact_level']

    def calculate_injury_differential(self, team1_injury, team2_injury):
        team1_data = self.injury_weights.get(team1_injury, self.injury_weights['None'])
        team2_data = self.injury_weights.get(team2_injury, self.injury_weights['None'])
        attack_diff = team1_data['attack_mult'] - team2_data['attack_mult']
        defense_diff = team1_data['defense_mult'] - team2_data['defense_mult']
        return (0.4 * attack_diff + 0.6 * defense_diff)

    def get_injury_impact_summary(self, injury_level):
        data = self.injury_weights.get(injury_level, self.injury_weights['None'])
        attack_impact = (1 - data['attack_mult']) * 100
        defense_impact = (1 - data['defense_mult']) * 100
        return {
            'attack_reduction': attack_impact,
            'defense_reduction': defense_impact,
            'description': data['description'],
            'impact_level': data['impact_level']
        }
