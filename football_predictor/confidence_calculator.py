import numpy as np

class ConfidenceCalculator:
    def __init__(self, injury_analyzer, home_advantage):
        self.injury_analyzer = injury_analyzer
        self.home_advantage = home_advantage
        
        # Confidence weights for context factors
        self.confidence_weights = {
            'data_quality': 0.20,
            'predictability': 0.25, 
            'injury_stability': 0.25,
            'rest_balance': 0.15,
            'home_advantage_consistency': 0.15
        }

    def calculate_outcome_specific_confidence(self, probabilities, home_data, away_data, inputs):
        """Calculate confidence scores that work with the engine"""
        
        print("🔍 CALCULATING CONFIDENCE SCORES...")
        print(f"   Probabilities - Home: {probabilities['home_win']:.1%}, Draw: {probabilities['draw']:.1%}, Away: {probabilities['away_win']:.1%}")
        
        # Get base context confidence
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        print(f"   Context Confidence: {context_confidence:.1f}%")
        
        # Determine predicted winner
        max_prob = max(probabilities['home_win'], probabilities['away_win'], probabilities['draw'])
        predicted_outcome = [k for k, v in probabilities.items() if v == max_prob][0]
        print(f"   Predicted Winner: {predicted_outcome} ({max_prob:.1%})")
        
        # Calculate base confidences from probabilities
        home_base = self._probability_to_base_confidence(probabilities['home_win'], 'home_win')
        away_base = self._probability_to_base_confidence(probabilities['away_win'], 'away_win') 
        draw_base = self._probability_to_base_confidence(probabilities['draw'], 'draw')
        
        print(f"   Base Confidences - Home: {home_base}%, Away: {away_base}%, Draw: {draw_base}%")
        
        # Apply team-specific adjustments
        home_adj = self._calculate_team_adjustments(home_data, away_data, 'home', inputs)
        away_adj = self._calculate_team_adjustments(away_data, home_data, 'away', inputs)
        draw_adj = self._calculate_draw_adjustments(home_data, away_data)
        
        print(f"   Adjustments - Home: +{home_adj}%, Away: +{away_adj}%, Draw: +{draw_adj}%")
        
        # Apply predicted winner boost
        if predicted_outcome == 'home_win':
            home_adj += 15
            print("   🏆 Predicted Winner Boost: Home +15%")
        elif predicted_outcome == 'away_win':
            away_adj += 15
            print("   🏆 Predicted Winner Boost: Away +15%")
        elif predicted_outcome == 'draw':
            draw_adj += 10
            print("   🏆 Predicted Winner Boost: Draw +10%")
        
        # Calculate final confidences
        home_final = home_base + home_adj
        away_final = away_base + away_adj
        draw_final = draw_base + draw_adj
        
        # Apply context influence (30% weight)
        home_final = 0.7 * home_final + 0.3 * context_confidence
        away_final = 0.7 * away_final + 0.3 * context_confidence  
        draw_final = 0.7 * draw_final + 0.3 * context_confidence
        
        # Ensure predicted winner has highest confidence
        if predicted_outcome == 'home_win' and home_final <= max(away_final, draw_final):
            home_final = max(away_final, draw_final) + 5
        elif predicted_outcome == 'away_win' and away_final <= max(home_final, draw_final):
            away_final = max(home_final, draw_final) + 5
        elif predicted_outcome == 'draw' and draw_final <= max(home_final, away_final):
            draw_final = max(home_final, away_final) + 3
        
        outcome_confidences = {
            'home_win': min(85, max(40, home_final)),
            'draw': min(75, max(30, draw_final)),
            'away_win': min(85, max(40, away_final))
        }
        
        print(f"✅ FINAL CONFIDENCES - Home: {outcome_confidences['home_win']}%, Draw: {outcome_confidences['draw']}%, Away: {outcome_confidences['away_win']}%")
        
        return outcome_confidences, factors

    def _probability_to_base_confidence(self, probability, outcome_type):
        """Convert probability to sensible base confidence"""
        if outcome_type == 'draw':
            # Draws are less predictable
            if probability >= 0.35: return 50
            elif probability >= 0.25: return 45
            elif probability >= 0.15: return 40
            else: return 35
        else:
            # Win outcomes
            if probability >= 0.70: return 65
            elif probability >= 0.60: return 60
            elif probability >= 0.50: return 55
            elif probability >= 0.40: return 50
            elif probability >= 0.30: return 45
            elif probability >= 0.20: return 40
            else: return 35

    def _calculate_team_adjustments(self, team_data, opponent_data, side, inputs):
        """Calculate team-specific confidence adjustments"""
        adjustments = 0
        
        # Elite team boost
        if team_data['base_quality']['structural_tier'] == 'elite':
            adjustments += 8
            print(f"      {side.upper()} Elite Team: +8%")
        
        # Home advantage boost
        if side == 'home' and team_data['home_advantage']['strength'] == 'strong':
            adjustments += 6
            print(f"      {side.upper()} Strong Home Advantage: +6%")
        
        # Injury penalties
        injury_key = 'home_injuries' if side == 'home' else 'away_injuries'
        if inputs[injury_key] == 'Significant':
            adjustments -= 8
            print(f"      {side.upper()} Significant Injuries: -8%")
        elif inputs[injury_key] == 'Crisis':
            adjustments -= 12
            print(f"      {side.upper()} Injury Crisis: -12%")
        
        # Form trend
        if team_data['form_trend'] > 0.05:
            adjustments += 3
            print(f"      {side.upper()} Positive Form: +3%")
        elif team_data['form_trend'] < -0.05:
            adjustments -= 3
            print(f"      {side.upper()} Negative Form: -3%")
        
        return adjustments

    def _calculate_draw_adjustments(self, home_data, away_data):
        """Calculate draw-specific adjustments"""
        adjustments = 0
        
        # Close ELO rating increases draw confidence
        elo_diff = abs(home_data['base_quality']['elo'] - away_data['base_quality']['elo'])
        if elo_diff < 100:
            adjustments += 5
            print("      DRAW Close Match: +5%")
        elif elo_diff > 250:
            adjustments -= 5
            print("      DRAW Mismatch: -5%")
        
        return adjustments

    def _calculate_context_confidence(self, home_data, away_data, inputs):
        """Calculate overall match context confidence"""
        factors = {}
        
        # Data Quality (based on matches played)
        home_matches = max(1, home_data['matches_played'])
        away_matches = max(1, away_data['matches_played'])
        data_quality = min(home_matches / 5, away_matches / 5, 1.0)
        factors['data_quality'] = data_quality
        
        # Predictability (team consistency)
        home_consistency = self._calculate_team_consistency(home_data)
        away_consistency = self._calculate_team_consistency(away_data)
        predictability = (home_consistency + away_consistency) / 2
        factors['predictability'] = predictability
        
        # Injury Stability
        injury_stability = self._calculate_injury_stability(inputs['home_injuries'], inputs['away_injuries'])
        factors['injury_stability'] = injury_stability
        
        # Rest Balance
        rest_balance = self._calculate_rest_balance(inputs['home_rest'], inputs['away_rest'])
        factors['rest_balance'] = rest_balance
        
        # Home Advantage Consistency
        home_adv_consistency = self._calculate_home_advantage_consistency(home_data)
        factors['home_advantage_consistency'] = home_adv_consistency
        
        # Weighted context confidence
        context_confidence = (
            factors['data_quality'] * self.confidence_weights['data_quality'] +
            factors['predictability'] * self.confidence_weights['predictability'] +
            factors['injury_stability'] * self.confidence_weights['injury_stability'] +
            factors['rest_balance'] * self.confidence_weights['rest_balance'] +
            factors['home_advantage_consistency'] * self.confidence_weights['home_advantage_consistency']
        ) * 100
        
        return min(90, max(50, context_confidence)), factors

    def _calculate_team_consistency(self, team_data):
        """Calculate team consistency score"""
        clean_sheet_consistency = team_data['clean_sheet_pct'] / 100
        btts_consistency = 1.0 - abs(team_data['btts_pct'] - 50) / 50
        return (clean_sheet_consistency + btts_consistency) / 2

    def _calculate_injury_stability(self, home_injuries, away_injuries):
        """Calculate injury stability score"""
        injury_impact = {
            "None": 1.0, "Minor": 0.9, "Moderate": 0.8, 
            "Significant": 0.6, "Crisis": 0.4
        }
        home_stability = injury_impact.get(home_injuries, 0.8)
        away_stability = injury_impact.get(away_injuries, 0.8)
        return (home_stability + away_stability) / 2

    def _calculate_rest_balance(self, home_rest, away_rest):
        """Calculate rest balance score"""
        rest_diff = abs(home_rest - away_rest)
        if rest_diff <= 2: return 1.0
        elif rest_diff <= 4: return 0.9
        else: return 0.7

    def _calculate_home_advantage_consistency(self, home_data):
        """Calculate home advantage consistency"""
        home_adv = home_data['home_advantage']
        if home_adv['strength'] == 'strong': return 0.95
        elif home_adv['strength'] == 'moderate': return 0.85
        else: return 0.7

    def calculate_goal_market_confidence(self, total_goals, probability, market_type="over_2.5"):
        """Calculate goal market confidence"""
        if market_type == "over_1.5":
            if probability >= 0.85: return 75
            elif probability >= 0.70: return 68
            elif probability >= 0.55: return 61
            else: return 54
        elif market_type == "over_2.5":
            if probability >= 0.75: return 72
            elif probability >= 0.60: return 65
            elif probability >= 0.45: return 58
            else: return 51
        else:  # over_3.5
            if probability >= 0.65: return 70
            elif probability >= 0.50: return 63
            elif probability >= 0.35: return 56
            else: return 49

    def calculate_btts_confidence(self, btts_probability, home_data, away_data, home_goal_exp, away_goal_exp):
        """Calculate BTTS confidence with proper logic"""
        distance_from_50 = abs(btts_probability - 0.5)
        
        if distance_from_50 > 0.20: base = 65
        elif distance_from_50 > 0.15: base = 58
        elif distance_from_50 > 0.10: base = 52
        elif distance_from_50 > 0.05: base = 46
        else: base = 40
        
        # Historical consistency adjustment
        hist_home = home_data.get("btts_pct", 50) / 100.0
        hist_away = away_data.get("btts_pct", 50) / 100.0
        hist_avg = (hist_home + hist_away) / 2.0
        
        if abs(hist_avg - btts_probability) > 0.2:
            base = max(35, base - 8)
        
        # Different confidence for Yes/No
        if btts_probability > 0.5:
            confidence = min(75, base + 4)  # Yes gets higher confidence
        else:
            confidence = min(75, base)  # No gets base confidence
        
        print(f"🔍 BTTS Confidence: {confidence}% (prob: {btts_probability:.1%})")
        return confidence

    # Backward compatibility
    def calculate_confidence(self, home_xg, away_xg, home_xga, away_xga, inputs):
        """Legacy method"""
        home_data = inputs.get('home_data', {})
        away_data = inputs.get('away_data', {})
        context_confidence, factors = self._calculate_context_confidence(home_data, away_data, inputs)
        return context_confidence, factors
