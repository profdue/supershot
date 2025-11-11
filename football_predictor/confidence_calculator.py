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
        
        # 🚨 CRITICAL FIX: Use the actual probabilities from the enhanced predictor
        # Not the raw inputs that might be causing issues
        
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
        
        # 🚨 CRITICAL FIX: Proper probability-based confidence scaling
        if win_probability > 0.70:
            prob_confidence = 80 + (win_probability - 0.70) * 30  # 80-89% (reduced range)
        elif win_probability > 0.55:
            prob_confidence = 65 + (win_probability - 0.55) * 40  # 65-75%
        elif win_probability > 0.40:
            prob_confidence = 55 + (win_probability - 0.40) * 33  # 55-65%
        elif win_probability > 0.25:
            prob_confidence = 45 + (win_probability - 0.25) * 40  # 45-55%
        else:
            prob_confidence = 35 + win_probability * 40  # 35-45%
        
        # 🚨 FIX: More aggressive confidence reduction for unrealistic predictions
        team_tier = team_data['base_quality']['structural_tier']
        opponent_tier = opponent_data['base_quality']['structural_tier']
        team_elo = team_data['base_quality']['elo']
        opponent_elo = opponent_data['base_quality']['elo']
        
        # Calculate realistic probability based on ELO difference
        elo_diff = team_elo - opponent_elo
        if side == 'home':
            elo_diff += 100  # Home advantage
        
        realistic_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        probability_gap = abs(win_probability - realistic_prob)
        
        # 🚨 MAJOR FIX: Reduce confidence based on probability-reality gap
        if probability_gap > 0.15:
            reduction = min(0.5, probability_gap * 2)  # Up to 50% reduction
            prob_confidence = max(25, prob_confidence * (1 - reduction))
            print(f"🔍 CONFIDENCE ADJUSTMENT: Probability-reality gap {probability_gap:.2f}. Reducing confidence by {int(reduction*100)}%")
        
        # Additional quality-based sanity checks
        if team_tier == 'weak' and opponent_tier == 'strong' and win_probability > 0.5:
            reduction_factor = 0.5  # 50% reduction
            print(f"🔍 CONFIDENCE ADJUSTMENT: Weak team favored over strong team. Reducing confidence by {int((1-reduction_factor)*100)}%")
            prob_confidence = max(25, prob_confidence * reduction_factor)
        
        if team_tier == 'elite' and opponent_tier != 'elite' and win_probability < 0.4:
            reduction_factor = 0.6  # 40% reduction
            print(f"🔍 CONFIDENCE ADJUSTMENT: Elite team underdog against non-elite. Reducing confidence by {int((1-reduction_factor)*100)}%")
            prob_confidence = max(25, prob_confidence * reduction_factor)
        
        # Form trend adjustment (smaller impact)
        form_trend = team_data['form_trend']
        if form_trend > 0.05 and win_probability > 0.4:
            prob_confidence += 2
        elif form_trend < -0.05 and win_probability > 0.4:
            prob_confidence -= 2
        
        # 🚨 FIX: Better blending with context (context should have less influence)
        final_confidence = 0.8 * prob_confidence + 0.2 * context_confidence
        
        return min(90, max(25, final_confidence))

    def _calculate_draw_confidence(self, draw_probability, context_confidence, home_data, away_data):
        """Calculate confidence for draw outcome"""
        
        # 🚨 CRITICAL FIX: Draw confidence should be much more conservative
        if draw_probability > 0.35:
            prob_confidence = 55 + (draw_probability - 0.35) * 30  # 55-64%
        elif draw_probability > 0.25:
            prob_confidence = 45 + (draw_probability - 0.25) * 40  # 45-55%
        elif draw_probability > 0.15:
            prob_confidence = 35 + (draw_probability - 0.15) * 50  # 35-45%
        else:
            prob_confidence = 25 + draw_probability * 67  # 25-35%
        
        # 🚨 FIX: Draws are inherently less predictable - reduce confidence
        prob_confidence *= 0.9  # 10% reduction for draw uncertainty
        
        # Team quality mismatch adjustment
        home_tier = home_data['base_quality']['structural_tier']
        away_tier = away_data['base_quality']['structural_tier']
        
        # Lower confidence if elite vs weak teams have high draw probability
        if (home_tier == 'elite' and away_tier == 'weak' and draw_probability > 0.25) or \
           (away_tier == 'elite' and home_tier == 'weak' and draw_probability > 0.25):
            reduction_factor = 0.6  # 40% reduction
            print(f"🔍 DRAW CONFIDENCE ADJUSTMENT: Unlikely draw scenario (elite vs weak). Reducing confidence by {int((1-reduction_factor)*100)}%")
            prob_confidence = max(20, prob_confidence * reduction_factor)
        
        # ELO difference adjustment
        elo_diff = abs(home_data['base_quality']['elo'] - away_data['base_quality']['elo'])
        if elo_diff < 100:  # Close match
            prob_confidence += 5
        elif elo_diff > 250:  # Mismatch
            prob_confidence -= 10
        
        # 🚨 FIX: Context has even less influence on draw confidence
        final_confidence = 0.85 * prob_confidence + 0.15 * context_confidence
        
        return min(80, max(20, final_confidence))

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
        
        # 🚨 CRITICAL: Goal market confidence should scale with probability
        if market_type == "over_1.5":
            if probability > 0.85:
                confidence = 80 + (probability - 0.85) * 20  # 80-84%
            elif probability > 0.70:
                confidence = 70 + (probability - 0.70) * 33  # 70-75%
            elif probability > 0.55:
                confidence = 60 + (probability - 0.55) * 33  # 60-65%
            else:
                confidence = 50 + (probability - 0.40) * 50  # 50-60%
                
        elif market_type == "over_2.5":
            if probability > 0.75:
                confidence = 75 + (probability - 0.75) * 20  # 75-79%
            elif probability > 0.60:
                confidence = 65 + (probability - 0.60) * 33  # 65-70%
            elif probability > 0.45:
                confidence = 55 + (probability - 0.45) * 33  # 55-60%
            else:
                confidence = 45 + (probability - 0.30) * 33  # 45-50%
                
        else:  # over_3.5
            if probability > 0.60:
                confidence = 70 + (probability - 0.60) * 25  # 70-75%
            elif probability > 0.45:
                confidence = 60 + (probability - 0.45) * 33  # 60-65%
            elif probability > 0.30:
                confidence = 50 + (probability - 0.30) * 33  # 50-55%
            else:
                confidence = 40 + (probability - 0.15) * 33  # 40-45%
        
        # Adjust based on total goals expectation
        if total_goals > 4.0:
            confidence += 5  # Higher confidence for extreme totals
        elif total_goals < 2.0:
            confidence += 3  # Higher confidence for low totals
        
        return min(85, max(35, confidence))

    # For backward compatibility
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        """Legacy method - calculates overall match confidence"""
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        return context_confidence, factors
