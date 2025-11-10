class InjuryAnalyzer:
    def __init__(self):
        # ENHANCED Injury impact weights - defense injuries hit harder
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
                "defense_mult": 0.94,
                "description": "1-2 rotational/fringe players missing",
                "key_players_missing": 0,
                "player_type": "Rotational",
                "impact_level": "Low"
            },
            "Moderate": {
                "attack_mult": 0.90,
                "defense_mult": 0.85,
                "description": "1-2 key starters missing",
                "key_players_missing": 1,
                "player_type": "Key Starters",
                "impact_level": "Medium"
            },
            "Significant": {
                "attack_mult": 0.82,
                "defense_mult": 0.72,
                "description": "3-4 key starters missing",
                "key_players_missing": 3,
                "player_type": "Key Starters",
                "impact_level": "High"
            },
            "Crisis": {
                "attack_mult": 0.70,
                "defense_mult": 0.58,
                "description": "5+ key starters missing",
                "key_players_missing": 5,
                "player_type": "Key Starters",
                "impact_level": "Severe"
            }
        }

        # Fatigue multipliers per rest days (interpolated if needed)
        self.fatigue_multipliers = {
            2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96,
            7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
            12: 1.03, 13: 1.03, 14: 1.03
        }

    def apply_injury_impact(self, xg_for, xg_against, injury_level, rest_days, form_trend):
        """Apply injury, fatigue, and form modifiers to xG for and against."""
        # Validate injury level
        injury_data = self.injury_weights.get(injury_level, self.injury_weights['None'])

        attack_mult = injury_data["attack_mult"]
        defense_mult = injury_data["defense_mult"]

        # Fatigue multiplier with fallback to 1.0 if outside defined range
        fatigue_mult = self.fatigue_multipliers.get(rest_days, 1.0)

        # Form multiplier: expects form_trend roughly in [-1,0,1]
        form_mult = 1 + (form_trend * 0.2)

        # Apply all modifiers
        xg_modified = xg_for * attack_mult * fatigue_mult * form_mult
        xga_modified = xg_against * defense_mult * fatigue_mult * form_mult

        # Ensure minimum xG
        return max(0.1, xg_modified), max(0.1, xga_modified)

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

