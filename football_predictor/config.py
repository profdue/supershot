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
        "description": "Key starter + 1-2 rotational players missing",
        "impact_level": "Medium"
    },
    "Major": {
        "attack_mult": 0.82, 
        "defense_mult": 0.85,
        "description": "Multiple key starters missing in same area",
        "impact_level": "High"
    },
    "Crisis": {
        "attack_mult": 0.72, 
        "defense_mult": 0.76,
        "description": "Critical injury situation affecting entire unit",
        "impact_level": "Very High"
    }
}

# Squad value tiers (in euros)
SQUAD_VALUE_TIERS = {
    "elite": 500000000,      # 500M+
    "strong": 200000000,     # 200-500M
    "average": 80000000,     # 80-200M
    "weak": 0                # <80M
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
