# football_predictor/config.py
"""
Central configuration for constants and thresholds
"""

# Injury multipliers (moderated for 2025/26)
INJURY_WEIGHTS = {
    "None": {
        "attack_mult": 1.00, 
        "defense_mult": 1.00, 
        "description": "Full squad available",
        "impact_level": "None"
    },
    "Minor": {
        "attack_mult": 0.96, 
        "defense_mult": 0.97,
        "description": "1-2 rotational/fringe players missing",
        "impact_level": "Low"
    },
    "Moderate": {
        "attack_mult": 0.90,
        "defense_mult": 0.92,
        "description": "1-2 key starters missing", 
        "impact_level": "Medium"
    },
    "Significant": {
        "attack_mult": 0.82,
        "defense_mult": 0.85,
        "description": "3-4 key starters missing",
        "impact_level": "High"
    },
    "Crisis": {
        "attack_mult": 0.85,
        "defense_mult": 0.75,
        "description": "5+ key starters missing",
        "impact_level": "Severe"
    }
}

# League averages for normalization
LEAGUE_AVERAGES = {
    "Premier League": {"xg": 1.45, "xga": 1.45},
    "La Liga": {"xg": 1.38, "xga": 1.38},
    "Bundesliga": {"xg": 1.52, "xga": 1.52},
    "Serie A": {"xg": 1.42, "xga": 1.42},
    "Ligue 1": {"xg": 1.40, "xga": 1.40},
    "RFPL": {"xg": 1.35, "xga": 1.35}
}

# Fatigue multipliers
FATIGUE_MULTIPLIERS = {
    2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96, 
    7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
    12: 1.03, 13: 1.03, 14: 1.03
}

# Team quality scaling factors
QUALITY_SCALING = {
    "elite": 1.08,    # Elite teams lose only 92% of injury impact
    "strong": 1.04,   # Strong teams lose 96% of injury impact  
    "average": 1.00,  # Average teams feel full impact
    "weak": 0.96      # Weak teams feel 104% of injury impact
}

# Home advantage opponent scaling
OPPONENT_QUALITY_FACTOR = {
    "elite": 0.6,    # 40% reduction vs elite teams
    "strong": 0.8,   # 20% reduction vs strong teams
    "average": 1.0,  # Full advantage vs average
    "weak": 1.1      # 10% boost vs weak teams
}
