"""
Advanced configuration for professional football prediction engine
"""

# ENHANCED Injury impact weights - defense injuries hit harder to increase goals
INJURY_WEIGHTS = {
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
FATIGUE_MULTIPLIERS = {
    2: 0.85, 3: 0.88, 4: 0.91, 5: 0.94, 6: 0.96, 
    7: 0.98, 8: 1.00, 9: 1.01, 10: 1.02, 11: 1.03,
    12: 1.03, 13: 1.03, 14: 1.03
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

# Form trend thresholds
FORM_TREND_THRESHOLDS = {
    "positive": 0.05,
    "negative": -0.05,
    "neutral_min": -0.05,
    "neutral_max": 0.05
}

# Home advantage parameters
HOME_ADVANTAGE_BASE = 0.3  # Base goals boost for home teams

# Prediction thresholds
PREDICTION_THRESHOLDS = {
    "high_confidence": 0.65,
    "medium_confidence": 0.55,
    "close_match": 0.45
}

# League strength modifiers
LEAGUE_STRENGTH = {
    "Premier League": 1.05,
    "La Liga": 1.00,
    "Bundesliga": 0.98,
    "Serie A": 0.96,
    "Ligue 1": 0.94,
    "RFPL": 0.85
}

# Value betting thresholds
VALUE_THRESHOLDS = {
    "excellent": {"ev": 0.08, "value_ratio": 1.12},
    "good": {"ev": 0.04, "value_ratio": 1.06},
    "fair": {"ev": 0.01, "value_ratio": 1.02},
    "poor": {"ev": 0.00, "value_ratio": 1.00}
}

# Confidence weights
CONFIDENCE_WEIGHTS = {
    'data_quality': 0.18,
    'predictability': 0.18, 
    'injury_stability': 0.22,
    'rest_balance': 0.12,
    'home_advantage_consistency': 0.30
}

# Squad value tiers (in euros) - ADDED THIS
SQUAD_VALUE_TIERS = {
    "elite": 500000000,      # 500M+
    "strong": 200000000,     # 200-500M
    "average": 80000000,     # 80-200M
    "weak": 0                # <80M
}
