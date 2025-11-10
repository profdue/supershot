class InjuryAnalyzer:
    def __init__(self):
        # REALISTIC Injury impact weights based on practical football estimates
        # 5-15% impact for significant injuries, not 30-50%
        self.injury_weights = {
            "None": {
                "attack_mult": 1.00,
                "defense_mult": 1.00,
                "description": "Full squad available",
                "key_players_missing": 0,
                "player_type": "None",
                "impact_level": "None",
                "practical_impact": "No impact"
            },
            "Minor": {
                "attack_mult": 0.95,  # 5% reduction (not 10%)
                "defense_mult": 0.94,  # 6% reduction (not 12%)
                "description": "1-2 rotational/fringe players missing",
                "key_players_missing": 0,
                "player_type": "Rotational",
                "impact_level": "Low",
                "practical_impact": "2-3% performance drop"
            },
            "Moderate": {
                "attack_mult": 0.90,  # 10% reduction (not 20%)
                "defense_mult": 0.87,  # 13% reduction (not 26%)
                "description": "1-2 key starters missing",
                "key_players_missing": 1,
                "player_type": "Key Starters",
                "impact_level": "Medium",
                "practical_impact": "8-10% performance drop"
            },
            "Significant": {
                "attack_mult": 0.85,  # 15% reduction (not 30%)
                "defense_mult": 0.82,  # 18% reduction (not 36%)
                "description": "3-4 key starters missing",
                "key_players_missing": 3,
                "player_type": "Key Starters",
                "impact_level": "High",
                "practical_impact": "13-15% performance drop"
            },
            "Crisis": {
                "attack_mult": 0.75,  # 25% reduction (not 42%)
                "defense_mult": 0.72,  # 28% reduction (not 50%)
                "description": "5+ key starters missing",
                "key_players_missing": 5,
                "player_type": "Key Starters",
                "impact_level": "Severe",
                "practical_impact": "23-25% performance drop"
            }
        }

        # Fatigue multipliers per rest days
        self.fatigue_multipliers = {
            2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96,
            7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
            12: 1.03, 13: 1.03, 14: 1.03
        }

    def apply_injury_impact(self, xg_for, xg_against, injury_level, rest_days, form_trend):
        """
        Apply REALISTIC injury impacts based on practical football estimates
        ✅ 5-15% impact range for significant injuries (not 30-50%)
        ✅ Defense properly weakens (increases xGA)
        ✅ No over-correction or mathematical distortion
        """
        injury_data = self.injury_weights.get(injury_level, self.injury_weights['None'])

        attack_mult = injury_data["attack_mult"]
        defense_mult = injury_data["defense_mult"]

        # Fatigue multiplier
        fatigue_mult = self.fatigue_multipliers.get(rest_days, 1.0)

        # Form multiplier
        form_mult = 1 + (form_trend * 0.2)

        # Attack: realistic reduction in scoring
        xg_modified = xg_for * attack_mult * fatigue_mult * form_mult
        
        # Defense: realistic weakening = MORE goals conceded
        # Use simple multiplication (not division) to avoid over-correction
        xga_modified = xg_against * (2 - defense_mult) * fatigue_mult * form_mult

        # Ensure reasonable minimums
        return max(0.3, xg_modified), max(0.3, xga_modified)

    def get_injury_description(self, injury_level):
        """Return human-readable description of injury level."""
        return self.injury_weights.get(injury_level, self.injury_weights['None'])['description']

    def get_impact_level(self, injury_level):
        """Return impact level (None, Low, Medium, High, Severe)."""
        return self.injury_weights.get(injury_level, self.injury_weights['None'])['impact_level']

    def calculate_injury_differential(self, team1_injury, team2_injury):
        """
        Calculate net injury impact between two teams.
        Returns a float: average difference of attack and defense multipliers.
        """
        team1_data = self.injury_weights.get(team1_injury, self.injury_weights['None'])
        team2_data = self.injury_weights.get(team2_injury, self.injury_weights['None'])

        attack_diff = team1_data['attack_mult'] - team2_data['attack_mult']
        defense_diff = team1_data['defense_mult'] - team2_data['defense_mult']

        # Weighted average (defense slightly more important)
        return (0.4 * attack_diff + 0.6 * defense_diff)

    def get_injury_impact_summary(self, injury_level):
        """Return summary of injury impact for display"""
        data = self.injury_weights.get(injury_level, self.injury_weights['None'])
        attack_impact = (1 - data['attack_mult']) * 100
        defense_impact = (1 - data['defense_mult']) * 100
        return {
            'attack_reduction': attack_impact,
            'defense_reduction': defense_impact,
            'description': data['description'],
            'impact_level': data['impact_level'],
            'practical_impact': data['practical_impact']
        }
