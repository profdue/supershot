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
        
        # 🚨 CRITICAL: Store current probabilities for confidence calculation
        home_data['current_probability'] = probabilities['home_win']
        away_data['current_probability'] = probabilities['away_win']
        
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
        
        outcome_confidences = {
            'home_win': home_win_confidence,
            'draw': draw_confidence,
            'away_win': away_win_confidence
        }
        
        # 🚨 CRITICAL SANITY CHECK: Predicted winner should have highest confidence
        max_prob = max(probabilities['home_win'], probabilities['away_win'], probabilities['draw'])
        predicted_outcome = [k for k, v in probabilities.items() if v == max_prob][0]
        
        # If predicted winner doesn't have highest confidence, fix it
        predicted_confidence = outcome_confidences[predicted_outcome]
        max_confidence = max(outcome_confidences.values())
        
        if predicted_confidence < max_confidence:
            print(f"🚨 CONFIDENCE SANITY FIX: Boosting {predicted_outcome} confidence from {predicted_confidence} to {max_confidence + 2}")
            outcome_confidences[predicted_outcome] = max_confidence + 2
        
        return outcome_confidences, factors

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
        """🚨 COMPLETELY REVISED: Confidence must align with probability logic"""
        
        # 🚨 CRITICAL: Confidence should correlate with probability strength
        # Higher probability = Higher confidence (with reality checks)
        
        if win_probability >= 0.70:
            base_confidence = 78 + (win_probability - 0.70) * 40  # 78-82%
        elif win_probability >= 0.60:
            base_confidence = 72 + (win_probability - 0.60) * 60  # 72-78%
        elif win_probability >= 0.50:
            base_confidence = 65 + (win_probability - 0.50) * 70  # 65-72%
        elif win_probability >= 0.40:
            base_confidence = 58 + (win_probability - 0.40) * 70  # 58-65%
        elif win_probability >= 0.30:
            base_confidence = 50 + (win_probability - 0.30) * 80  # 50-58%
        elif win_probability >= 0.20:
            base_confidence = 42 + (win_probability - 0.20) * 80  # 42-50%
        else:
            base_confidence = 35 + win_probability * 350  # 35-42%
        
        # 🚨 REALITY CHECK: Predicted winner should have HIGHEST confidence
        # Get all probabilities to determine if this is the predicted winner
        all_probs = {
            'home': team_data.get('current_probability', 0) if side == 'home' else opponent_data.get('current_probability', 0),
            'away': opponent_data.get('current_probability', 0) if side == 'home' else team_data.get('current_probability', 0),
            'draw': 1 - (team_data.get('current_probability', 0) + opponent_data.get('current_probability', 0))
        }
        
        predicted_winner = max(all_probs, key=all_probs.get)
        is_predicted_winner = (
            (side == 'home' and predicted_winner == 'home') or
            (side == 'away' and predicted_winner == 'away')
        )
        
        # 🚨 BOOST confidence for predicted winner
        if is_predicted_winner and win_probability > 0.35:
            base_confidence += 8  # Significant boost for predicted winner
            print(f"🔍 PREDICTED WINNER BOOST: {side} gets +8% confidence boost")
        
        # 🚨 SANITY: Elite teams shouldn't have low confidence when favored
        team_tier = team_data['base_quality']['structural_tier']
        opponent_tier = opponent_data['base_quality']['structural_tier']
        
        if team_tier == 'elite' and opponent_tier != 'elite' and win_probability > 0.45 and base_confidence < 60:
            base_confidence = max(base_confidence, 65)  # Minimum confidence for elite favorites
            print(f"🔍 ELITE TEAM CONFIDENCE BOOST: {side} minimum confidence set to 65%")
        
        # Apply context (but less influence)
        final_confidence = 0.8 * base_confidence + 0.2 * context_confidence
        
        return min(85, max(35, final_confidence))

    def _calculate_draw_confidence(self, draw_probability, context_confidence, home_data, away_data):
        """🚨 FIXED: Draw confidence should be conservative and probability-based"""
        
        # Draws are inherently less predictable
        if draw_probability >= 0.35:
            base_confidence = 55 + (draw_probability - 0.35) * 28  # 55-59%
        elif draw_probability >= 0.25:
            base_confidence = 48 + (draw_probability - 0.25) * 70  # 48-55%
        elif draw_probability >= 0.15:
            base_confidence = 40 + (draw_probability - 0.15) * 80  # 40-48%
        else:
            base_confidence = 30 + draw_probability * 67  # 30-40%
        
        # 🚨 Draw confidence should generally be LOWER than win confidences
        base_confidence *= 0.9  # Additional 10% reduction for draw uncertainty
        
        # Close matches (similar ELO) increase draw confidence
        elo_diff = abs(home_data['base_quality']['elo'] - away_data['base_quality']['elo'])
        if elo_diff < 100:
            base_confidence += 5
        elif elo_diff > 250:
            base_confidence -= 8
        
        final_confidence = 0.85 * base_confidence + 0.15 * context_confidence
        
        return min(70, max(25, final_confidence))

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

    # 🚨 NEW METHOD: Calculate goal market confidence
    def calculate_goal_market_confidence(self, total_goals, probability, market_type="over_2.5"):
        """Calculate confidence for goal markets based on probability strength"""
        
        # Base confidence from probability strength
        if market_type == "over_1.5":
            if probability >= 0.90:
                confidence = 82
            elif probability >= 0.80:
                confidence = 75
            elif probability >= 0.65:
                confidence = 68
            elif probability >= 0.50:
                confidence = 60
            else:
                confidence = 50
                
        elif market_type == "over_2.5":
            if probability >= 0.80:
                confidence = 78
            elif probability >= 0.70:
                confidence = 72
            elif probability >= 0.55:
                confidence = 65
            elif probability >= 0.40:
                confidence = 58
            else:
                confidence = 48
                
        else:  # over_3.5
            if probability >= 0.70:
                confidence = 75
            elif probability >= 0.60:
                confidence = 68
            elif probability >= 0.45:
                confidence = 60
            elif probability >= 0.30:
                confidence = 52
            else:
                confidence = 42
        
        # Adjust based on total goals expectation
        if total_goals > 4.0 and probability > 0.6:
            confidence += 3  # Higher confidence for extreme totals
        elif total_goals < 2.0 and probability < 0.4:
            confidence += 2  # Higher confidence for low totals
        
        return min(85, max(35, confidence))

    # 🚨 NEW METHOD: Calculate BTTS confidence with proper logic
    def calculate_btts_confidence(self, btts_probability, home_data, away_data, home_goal_exp, away_goal_exp):
        """🚨 COMPLETELY FIXED: BTTS confidence based on probability strength"""
        
        # 🚨 CRITICAL: Confidence should vary based on how far from 50%
        distance_from_50 = abs(btts_probability - 0.5)
        
        if distance_from_50 > 0.25:  # Very clear signal (25%+ from 50%)
            base_confidence = 70 + (distance_from_50 - 0.25) * 100  # 70-75%
        elif distance_from_50 > 0.15:  # Clear signal (15-25% from 50%)
            base_confidence = 60 + (distance_from_50 - 0.15) * 100  # 60-70%
        elif distance_from_50 > 0.08:  # Moderate signal (8-15% from 50%)
            base_confidence = 50 + (distance_from_50 - 0.08) * 142  # 50-60%
        elif distance_from_50 > 0.03:  # Weak signal (3-8% from 50%)
            base_confidence = 40 + (distance_from_50 - 0.03) * 200  # 40-50%
        else:  # Very close to 50% (0-3% from 50%)
            base_confidence = 35 + distance_from_50 * 166  # 35-40%
        
        # Historical consistency adjustment
        hist_home = home_data.get("btts_pct", 50) / 100.0
        hist_away = away_data.get("btts_pct", 50) / 100.0
        hist_avg = (hist_home + hist_away) / 2.0
        
        # Reduce confidence if historical data is inconsistent with prediction
        if abs(hist_avg - btts_probability) > 0.2:
            base_confidence *= 0.9
        
        # Ensure BTTS Yes and No have different confidences when probabilities differ
        if abs(btts_probability - 0.5) > 0.01:  # If probabilities are meaningfully different
            # The more likely outcome should have slightly higher confidence
            if btts_probability > 0.5:
                base_confidence += 1
            else:
                base_confidence -= 1
        
        return min(80, max(35, base_confidence))

    # For backward compatibility
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        """Legacy method - calculates overall match confidence"""
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        return context_confidence, factors
