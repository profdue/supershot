import numpy as np

class ConfidenceCalculator:
    def __init__(self, injury_analyzer, home_advantage):
        self.injury_analyzer = injury_analyzer
        self.home_advantage = home_advantage
        
        # Confidence weights (these can be tuned)
        self.confidence_weights = {
            'data_quality': 0.18,
            'predictability': 0.18, 
            'injury_stability': 0.22,
            'rest_balance': 0.12,
            'home_advantage_consistency': 0.30
        }

    def calculate_outcome_specific_confidence(self, probabilities, home_data, away_data, inputs):
        """Calculate dynamic, outcome-specific confidence scores"""
        
        # Base context confidence (match-level factors)
        context_confidence, factors = self._calculate_context_confidence(
            home_data, away_data, inputs
        )
        
        # Outcome-specific adjustments
        home_win_confidence = self._calculate_win_confidence(
            probabilities['home_win'], context_confidence, home_data, away_data, 'home'
        )
        
        away_win_confidence = self._calculate_win_confidence(
            probabilities['away_win'], context_confidence, home_data, away_data, 'away'
        )
        
        draw_confidence = self._calculate_draw_confidence(
            probabilities['draw'], context_confidence, home_data, away_data
        )
        
        return {
            'home_win': home_win_confidence,
            'draw': draw_confidence,
            'away_win': away_win_confidence
        }, factors

    def _calculate_context_confidence(self, home_data, away_data, inputs):
        """Calculate overall match context confidence"""
        factors = {}
        
        # 1. Data Quality Factor
        home_matches = max(1, home_data['matches_played'])
        away_matches = max(1, away_data['matches_played'])
        data_quality = min(home_matches / 5, away_matches / 5, 1.0)
        factors['data_quality'] = data_quality
        
        # 2. Predictability Factor (team consistency)
        home_consistency = self._calculate_team_consistency(home_data)
        away_consistency = self._calculate_team_consistency(away_data)
        predictability = (home_consistency + away_consistency) / 2
        factors['predictability'] = predictability
        
        # 3. Injury Stability Factor
        injury_stability = self._calculate_injury_stability(inputs['home_injuries'], inputs['away_injuries'])
        factors['injury_stability'] = injury_stability
        
        # 4. Rest Balance Factor
        rest_balance = self._calculate_rest_balance(inputs['home_rest'], inputs['away_rest'])
        factors['rest_balance'] = rest_balance
        
        # 5. Home Advantage Consistency Factor
        home_adv_consistency = self._calculate_home_advantage_consistency(home_data)
        factors['home_advantage_consistency'] = home_adv_consistency
        
        # Weighted context confidence
        context_confidence = (
            factors['data_quality'] * self.confidence_weights['data_quality'] +
            factors['predictability'] * self.confidence_weights['predictability'] +
            factors['injury_stability'] * self.confidence_weights['injury_stability'] +
            factors['rest_balance'] * self.confidence_weights['rest_balance'] +
            factors['home_advantage_consistency'] * self.confidence_weights['home_advantage_consistency']
        ) * 100  # Convert to percentage
        
        return min(95, max(40, context_confidence)), factors

    def _calculate_win_confidence(self, win_probability, context_confidence, team_data, opponent_data, side):
        """Calculate confidence for a win outcome"""
        
        # Base confidence from probability strength
        if win_probability > 0.70:
            prob_confidence = 80 + (win_probability - 0.70) * 50  # 80-95%
        elif win_probability > 0.50:
            prob_confidence = 65 + (win_probability - 0.50) * 75  # 65-80%
        elif win_probability > 0.30:
            prob_confidence = 50 + (win_probability - 0.30) * 75  # 50-65%
        elif win_probability > 0.15:
            prob_confidence = 40 + (win_probability - 0.15) * 67  # 40-50%
        else:
            prob_confidence = 30 + win_probability * 67  # 30-40%
        
        # Team quality adjustment
        elo_diff = team_data['base_quality']['elo'] - opponent_data['base_quality']['elo']
        if side == 'home':
            elo_diff += 100  # Home advantage in ELO terms
        
        if abs(elo_diff) > 300:
            # High confidence in clear favorites/underdogs
            if (elo_diff > 0 and win_probability > 0.5) or (elo_diff < 0 and win_probability < 0.3):
                prob_confidence += 8
            else:
                prob_confidence -= 5
        elif abs(elo_diff) < 100:
            # Lower confidence in close matches
            prob_confidence -= 3
        
        # Form trend adjustment
        form_trend = team_data['form_trend']
        if form_trend > 0.05 and win_probability > 0.4:
            prob_confidence += 4
        elif form_trend < -0.05 and win_probability > 0.4:
            prob_confidence -= 4
        
        # Blend with context confidence (70% probability-based, 30% context)
        final_confidence = 0.7 * prob_confidence + 0.3 * context_confidence
        
        return min(95, max(25, final_confidence))

    def _calculate_draw_confidence(self, draw_probability, context_confidence, home_data, away_data):
        """Calculate confidence for draw outcome"""
        
        # Draw confidence is highest when probabilities are balanced
        balance_confidence = 1.0 - abs((home_data['base_quality']['elo'] - away_data['base_quality']['elo']) / 1000)
        balance_confidence = max(0.3, min(0.8, balance_confidence))
        
        # Probability-based confidence for draws
        if draw_probability > 0.35:
            prob_confidence = 60 + (draw_probability - 0.35) * 50  # 60-80%
        elif draw_probability > 0.25:
            prob_confidence = 50 + (draw_probability - 0.25) * 50  # 50-60%
        elif draw_probability > 0.15:
            prob_confidence = 40 + (draw_probability - 0.15) * 50  # 40-50%
        else:
            prob_confidence = 30 + draw_probability * 67  # 30-40%
        
        # Draws are more likely when teams are closely matched
        elo_diff = abs(home_data['base_quality']['elo'] - away_data['base_quality']['elo'])
        if elo_diff < 150:
            prob_confidence += 5
        elif elo_diff > 300:
            prob_confidence -= 8
        
        # Blend with context confidence
        final_confidence = 0.6 * prob_confidence + 0.4 * context_confidence
        
        return min(90, max(25, final_confidence))

    def _calculate_team_consistency(self, team_data):
        """Calculate team performance consistency"""
        # Use clean sheet % and BTTS % as consistency indicators
        clean_sheet_consistency = team_data['clean_sheet_pct'] / 100
        btts_consistency = 1.0 - abs(team_data['btts_pct'] - 50) / 50  # Closer to 50% = more predictable
        
        return (clean_sheet_consistency + btts_consistency) / 2

    def _calculate_injury_stability(self, home_injuries, away_injuries):
        """Calculate injury impact on confidence"""
        injury_impact = {
            "None": 1.0,
            "Minor": 0.9,
            "Moderate": 0.75,
            "Significant": 0.6,
            "Crisis": 0.4
        }
        
        home_stability = injury_impact.get(home_injuries, 0.8)
        away_stability = injury_impact.get(away_injuries, 0.8)
        
        return (home_stability + away_stability) / 2

    def _calculate_rest_balance(self, home_rest, away_rest):
        """Calculate rest balance impact"""
        rest_diff = abs(home_rest - away_rest)
        if rest_diff <= 2:
            return 1.0  # Balanced rest
        elif rest_diff <= 4:
            return 0.8  # Moderate imbalance
        else:
            return 0.6  # Significant imbalance

    def _calculate_home_advantage_consistency(self, home_data):
        """Calculate home advantage consistency"""
        home_adv = home_data['home_advantage']
        if home_adv['strength'] == 'strong':
            return 0.95
        elif home_adv['strength'] == 'moderate':
            return 0.85
        else:  # weak
            return 0.7

    # For backward compatibility
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        """Legacy method - calculates overall match confidence"""
        # This might be what's causing the static confidence issue
        # If your engine is calling this, it needs to be updated
        
        # For now, return a reasonable default
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        return context_confidence, factors
