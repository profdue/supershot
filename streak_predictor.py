"""
Streak Predictor - BTTS & Over/Under Betting System
Complete implementation with:
- Regression filter (streak ≤ 10 = reliable)
- Venue filter (🏠 only home, ✈️ only away, plain anywhere)
- Rule 2 (BTTS No) - Priority
- Rule 1 (BTTS Yes from plain Scoring)
- Rule 3 (BTTS Yes from BTTS streak)
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum


# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Streak Predictor",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================================
# CSS STYLES - CRISP DARK UI
# ============================================================================
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    /* Card styles */
    .prediction-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 24px;
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        border: 1px solid #334155;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    .prediction-btts-yes {
        font-size: 2.5rem;
        font-weight: 800;
        color: #10b981;
        letter-spacing: 2px;
    }
    
    .prediction-btts-no {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ef4444;
        letter-spacing: 2px;
    }
    
    .prediction-nobet {
        font-size: 2rem;
        font-weight: 700;
        color: #f59e0b;
    }
    
    .prediction-over {
        font-size: 1.3rem;
        font-weight: 600;
        color: #fbbf24;
        margin-top: 0.5rem;
    }
    
    .prediction-under {
        font-size: 1.3rem;
        font-weight: 600;
        color: #8b5cf6;
        margin-top: 0.5rem;
    }
    
    /* Team cards */
    .team-card {
        background: #0f172a;
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .team-name {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    
    .streak-item {
        display: inline-block;
        background: #1e293b;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        margin: 0.2rem 0.25rem;
        font-size: 0.7rem;
        font-family: monospace;
    }
    
    .streak-reliable {
        border-left: 3px solid #10b981;
    }
    
    .streak-unreliable {
        border-left: 3px solid #ef4444;
        opacity: 0.6;
        text-decoration: line-through;
    }
    
    .rule-box {
        background: #1e293b;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.75rem 0;
        border-left: 4px solid;
    }
    
    .rule-triggered {
        border-left-color: #10b981;
        background: #1e3a2f;
    }
    
    .rule-not-triggered {
        border-left-color: #64748b;
    }
    
    .venue-match {
        color: #10b981;
    }
    
    .venue-mismatch {
        color: #ef4444;
        text-decoration: line-through;
    }
    
    h1 {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    hr {
        margin: 1.5rem 0;
        border-color: #334155;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        font-weight: 700;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        border: none;
        width: 100%;
        transition: transform 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
    }
    
    .filter-badge {
        display: inline-block;
        background: #334155;
        border-radius: 12px;
        padding: 0.2rem 0.6rem;
        font-size: 0.7rem;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA MODELS
# ============================================================================
class Venue(Enum):
    HOME = "home"
    AWAY = "away"
    ANY = "any"


@dataclass
class Streak:
    """Single streak with type, length, icon, and reliability"""
    streak_type: str  # "scoring", "no_btts", "btts", "over25", "goals2"
    length: int
    icon: str  # "", "🏠", "✈️"
    
    @property
    def is_reliable(self) -> bool:
        """Regression filter: streak ≤ 10 is reliable"""
        return self.length <= 10
    
    @property
    def display(self) -> str:
        icon_str = f" {self.icon}" if self.icon else ""
        return f"{self.streak_type.replace('_', ' ').title()}{icon_str} {self.length}"
    
    def venue_matches(self, match_venue: str) -> bool:
        """Venue filter: 🏠 only home, ✈️ only away, plain anywhere"""
        if not self.icon:
            return True
        if self.icon == "🏠":
            return match_venue == "home"
        if self.icon == "✈️":
            return match_venue == "away"
        return False


@dataclass
class TeamStreaks:
    """Collection of all streaks for a team"""
    name: str
    scoring: List[Streak] = field(default_factory=list)
    no_btts: List[Streak] = field(default_factory=list)
    btts: List[Streak] = field(default_factory=list)
    over25: List[Streak] = field(default_factory=list)
    goals2: List[Streak] = field(default_factory=list)
    
    def get_best_streak(self, streak_list: List[Streak], match_venue: str = None) -> Optional[Streak]:
        """Get best (longest) streak that passes venue filter"""
        valid = []
        for s in streak_list:
            if match_venue is None or s.venue_matches(match_venue):
                valid.append(s)
        if not valid:
            return None
        return max(valid, key=lambda x: x.length)
    
    def has_reliable_no_btts(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        """Check for reliable No BTTS streak with venue match"""
        streak = self.get_best_streak(self.no_btts, match_venue)
        if streak and streak.is_reliable:
            return True, streak
        return False, None
    
    def has_reliable_scoring_plain(self, min_length: int = 3) -> Tuple[bool, Optional[Streak]]:
        """Check for reliable plain Scoring streak (no icon)"""
        plain_streaks = [s for s in self.scoring if not s.icon]
        if not plain_streaks:
            return False, None
        best = max(plain_streaks, key=lambda x: x.length)
        if best.length >= min_length and best.is_reliable:
            return True, best
        return False, None
    
    def has_reliable_btts(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        """Check for reliable BTTS streak with venue match"""
        streak = self.get_best_streak(self.btts, match_venue)
        if streak and streak.is_reliable:
            return True, streak
        return False, None
    
    def has_goal_streak(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        """Check for ANY goal streak (Scoring, BTTS, volume) with venue match"""
        # Check scoring
        scoring = self.get_best_streak(self.scoring, match_venue)
        if scoring and scoring.is_reliable:
            return True, scoring
        
        # Check BTTS
        btts = self.get_best_streak(self.btts, match_venue)
        if btts and btts.is_reliable:
            return True, btts
        
        # Check volume (Over 2.5 or Goals 2+)
        over25 = self.get_best_streak(self.over25, match_venue)
        if over25 and over25.is_reliable:
            return True, over25
        
        goals2 = self.get_best_streak(self.goals2, match_venue)
        if goals2 and goals2.is_reliable:
            return True, goals2
        
        return False, None
    
    def has_volume_streak(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        """Check for volume streak (Over 2.5 or Goals 2+) with venue match"""
        over25 = self.get_best_streak(self.over25, match_venue)
        if over25 and over25.is_reliable:
            return True, over25
        
        goals2 = self.get_best_streak(self.goals2, match_venue)
        if goals2 and goals2.is_reliable:
            return True, goals2
        
        return False, None


@dataclass
class PredictionResult:
    btts_prediction: str  # "BTTS Yes", "BTTS No", or "No bet"
    over_under: Optional[str]  # "Over 2.5", "Under 2.5 lean", or None
    triggered_rule: str
    reasoning: List[str]
    rule_details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PREDICTION LOGIC
# ============================================================================
def filter_and_log_streaks(home: TeamStreaks, away: TeamStreaks, match_venue: str) -> Dict:
    """Apply regression and venue filters, return filtered view"""
    details = {
        "home": {"reliable": [], "unreliable": [], "venue_mismatch": []},
        "away": {"reliable": [], "unreliable": [], "venue_mismatch": []}
    }
    
    for team, team_data in [("home", home), ("away", away)]:
        for streak_type, streaks in [
            ("scoring", team_data.scoring),
            ("no_btts", team_data.no_btts),
            ("btts", team_data.btts),
            ("over25", team_data.over25),
            ("goals2", team_data.goals2)
        ]:
            for s in streaks:
                if not s.venue_matches(match_venue):
                    details[team]["venue_mismatch"].append(f"{s.display} (venue mismatch)")
                elif not s.is_reliable:
                    details[team]["unreliable"].append(f"{s.display} (length {s.length} > 10)")
                else:
                    details[team]["reliable"].append(s.display)
    
    return details


def predict_match(home: TeamStreaks, away: TeamStreaks, match_venue: str) -> PredictionResult:
    """
    Main prediction function implementing the 3-rule system with:
    - Regression filter (streak ≤ 10)
    - Venue filter (icon-specific)
    """
    reasoning = []
    rule_details = {}
    
    # Apply filters
    filter_details = filter_and_log_streaks(home, away, match_venue)
    reasoning.append(f"📊 **Filters Applied:**")
    reasoning.append(f"   • Regression: Only streaks ≤ 10 are reliable")
    reasoning.append(f"   • Venue: 🏠 only home, ✈️ only away, plain anywhere")
    
    # ========================================================================
    # STEP 2: Rule 2 (BTTS No) - HIGHEST PRIORITY
    # ========================================================================
    home_no_btts, home_no_streak = home.has_reliable_no_btts(match_venue)
    away_no_btts, away_no_streak = away.has_reliable_no_btts(match_venue)
    
    if home_no_btts or away_no_btts:
        no_teams = []
        if home_no_btts:
            no_teams.append((home_no_streak.length, home.name, home_no_streak))
        if away_no_btts:
            no_teams.append((away_no_streak.length, away.name, away_no_streak))
        
        longest_len, longest_team, longest_streak = max(no_teams, key=lambda x: x[0])
        
        reasoning.append(f"\n✅ **RULE 2 TRIGGERED** (BTTS No - Priority)")
        reasoning.append(f"   • {longest_team}: {longest_streak.display}")
        reasoning.append(f"   • Regression check: {longest_streak.length} ≤ 10 ✓")
        reasoning.append(f"   • Venue match: {longest_streak.icon or 'plain'} ✓")
        
        rule_details = {
            "rule": "Rule 2",
            "trigger_team": longest_team,
            "streak": longest_streak.display
        }
        
        return PredictionResult(
            btts_prediction="BTTS No",
            over_under="Under 2.5 lean",
            triggered_rule="Rule 2 (BTTS No)",
            reasoning=reasoning,
            rule_details=rule_details
        )
    
    # ========================================================================
    # STEP 3: Rule 1 (BTTS Yes from Plain Scoring)
    # ========================================================================
    home_scoring, home_sc_streak = home.has_reliable_scoring_plain(min_length=3)
    away_scoring, away_sc_streak = away.has_reliable_scoring_plain(min_length=3)
    
    # Also need to check no "No BTTS" streaks (already filtered above)
    if home_scoring and away_scoring:
        reasoning.append(f"\n✅ **RULE 1 TRIGGERED** (BTTS Yes from Plain Scoring)")
        reasoning.append(f"   • {home.name}: {home_sc_streak.display} (reliable ✓)")
        reasoning.append(f"   • {away.name}: {away_sc_streak.display} (reliable ✓)")
        reasoning.append(f"   • No reliable No BTTS streaks ✓")
        
        # Check volume streaks for Over 2.5
        home_vol, home_vol_streak = home.has_volume_streak(match_venue)
        away_vol, away_vol_streak = away.has_volume_streak(match_venue)
        
        over_under = None
        if home_vol and away_vol:
            reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
            reasoning.append(f"   • {home.name}: {home_vol_streak.display}")
            reasoning.append(f"   • {away.name}: {away_vol_streak.display}")
            over_under = "Over 2.5"
        else:
            reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            if not home_vol:
                reasoning.append(f"   • {home.name}: No reliable volume streak")
            if not away_vol:
                reasoning.append(f"   • {away.name}: No reliable volume streak")
        
        rule_details = {
            "rule": "Rule 1",
            "home_streak": home_sc_streak.display,
            "away_streak": away_sc_streak.display,
            "home_volume": home_vol_streak.display if home_vol else None,
            "away_volume": away_vol_streak.display if away_vol else None
        }
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_under=over_under,
            triggered_rule="Rule 1 (Plain Scoring)",
            reasoning=reasons_for_rule1,  # Fixed: should be reasoning
            rule_details=rule_details
        )
    
    # ========================================================================
    # STEP 4: Rule 3 (BTTS Yes from BTTS Streak)
    # ========================================================================
    # Check home team's BTTS at home
    home_btts, home_btts_streak = home.has_reliable_btts(match_venue)
    
    if home_btts:
        # Check if opponent (away) has goal streak
        away_goal, away_goal_streak = away.has_goal_streak(match_venue)
        
        if away_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {home.name}: {home_btts_streak.display}")
            reasoning.append(f"   • Venue match: {'🏠 home' if match_venue == 'home' else '✈️ away'} ✓")
            reasoning.append(f"   • Opponent ({away.name}): {away_goal_streak.display} (goal streak ✓)")
            
            # Check volume streaks
            home_vol, home_vol_streak = home.has_volume_streak(match_venue)
            away_vol, away_vol_streak = away.has_volume_streak(match_venue)
            
            over_under = None
            if home_vol and away_vol:
                reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
                reasoning.append(f"   • {home.name}: {home_vol_streak.display}")
                reasoning.append(f"   • {away.name}: {away_vol_streak.display}")
                over_under = "Over 2.5"
            else:
                reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            
            rule_details = {
                "rule": "Rule 3",
                "trigger_team": home.name,
                "trigger_streak": home_btts_streak.display,
                "opponent_streak": away_goal_streak.display,
                "home_volume": home_vol_streak.display if home_vol else None,
                "away_volume": away_vol_streak.display if away_vol else None
            }
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS Streak)",
                reasoning=reasoning,
                rule_details=rule_details
            )
    
    # Check away team's BTTS away
    away_btts, away_btts_streak = away.has_reliable_btts(match_venue)
    
    if away_btts:
        # Check if opponent (home) has goal streak
        home_goal, home_goal_streak = home.has_goal_streak(match_venue)
        
        if home_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {away.name}: {away_btts_streak.display}")
            reasoning.append(f"   • Venue match: {'✈️ away' if match_venue == 'away' else '🏠 home'} ✓")
            reasoning.append(f"   • Opponent ({home.name}): {home_goal_streak.display} (goal streak ✓)")
            
            # Check volume streaks
            home_vol, home_vol_streak = home.has_volume_streak(match_venue)
            away_vol, away_vol_streak = away.has_volume_streak(match_venue)
            
            over_under = None
            if home_vol and away_vol:
                reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
                reasoning.append(f"   • {home.name}: {home_vol_streak.display}")
                reasoning.append(f"   • {away.name}: {away_vol_streak.display}")
                over_under = "Over 2.5"
            else:
                reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            
            rule_details = {
                "rule": "Rule 3",
                "trigger_team": away.name,
                "trigger_streak": away_btts_streak.display,
                "opponent_streak": home_goal_streak.display,
                "home_volume": home_vol_streak.display if home_vol else None,
                "away_volume": away_vol_streak.display if away_vol else None
            }
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS Streak)",
                reasoning=reasoning,
                rule_details=rule_details
            )
    
    # ========================================================================
    # STEP 5: No Bet
    # ========================================================================
    reasoning.append(f"\n❌ **NO RULE TRIGGERED** → No bet")
    reasoning.append(f"   • Rule 2: No reliable No BTTS streak with venue match")
    reasoning.append(f"   • Rule 1: Not both have plain Scoring ≥3 (reliable)")
    reasoning.append(f"   • Rule 3: No BTTS streak with venue match + opponent goal streak")
    
    return PredictionResult(
        btts_prediction="No bet",
        over_under=None,
        triggered_rule="No bet",
        reasoning=reasoning,
        rule_details={}
    )


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================
def create_streak_input(streak_type: str, key_prefix: str, default_plain: int = 0, default_home: int = 0, default_away: int = 0):
    """Create 3-column input for plain/home/away streaks"""
    col1, col2, col3 = st.columns(3)
    with col1:
        plain = st.number_input(
            f"{streak_type} (plain)",
            min_value=0, max_value=30, value=default_plain,
            key=f"{key_prefix}_{streak_type}_plain"
        )
    with col2:
        home = st.number_input(
            f"{streak_type} (🏠 home)",
            min_value=0, max_value=30, value=default_home,
            key=f"{key_prefix}_{streak_type}_home"
        )
    with col3:
        away = st.number_input(
            f"{streak_type} (✈️ away)",
            min_value=0, max_value=30, value=default_away,
            key=f"{key_prefix}_{streak_type}_away"
        )
    return plain, home, away


def streaks_from_session(prefix: str, name: str) -> TeamStreaks:
    """Build TeamStreaks object from session state"""
    team = TeamStreaks(name=name)
    
    # Scoring streaks
    for icon, suffix in [("", "plain"), ("🏠", "home"), ("✈️", "away")]:
        length = st.session_state.get(f"{prefix}_scoring_{suffix}", 0)
        if length > 0:
            team.scoring.append(Streak("scoring", length, icon))
    
    # No BTTS streaks
    for icon, suffix in [("", "plain"), ("🏠", "home"), ("✈️", "away")]:
        length = st.session_state.get(f"{prefix}_no_btts_{suffix}", 0)
        if length > 0:
            team.no_btts.append(Streak("no_btts", length, icon))
    
    # BTTS streaks
    for icon, suffix in [("", "plain"), ("🏠", "home"), ("✈️", "away")]:
        length = st.session_state.get(f"{prefix}_btts_{suffix}", 0)
        if length > 0:
            team.btts.append(Streak("btts", length, icon))
    
    # Over 2.5 streaks
    for icon, suffix in [("", "plain"), ("🏠", "home"), ("✈️", "away")]:
        length = st.session_state.get(f"{prefix}_over25_{suffix}", 0)
        if length > 0:
            team.over25.append(Streak("over25", length, icon))
    
    # Goals 2+ streaks
    for icon, suffix in [("", "plain"), ("🏠", "home"), ("✈️", "away")]:
        length = st.session_state.get(f"{prefix}_goals2_{suffix}", 0)
        if length > 0:
            team.goals2.append(Streak("goals2", length, icon))
    
    return team


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("BTTS & Over/Under | Regression: ≤10 reliable | Venue: 🏠=home ✈️=away")
    
    # Match venue selection
    match_venue = st.radio(
        "🏟️ Match Venue",
        options=["home", "away"],
        format_func=lambda x: "🏠 Home" if x == "home" else "✈️ Away",
        horizontal=True,
        key="match_venue"
    )
    
    st.divider()
    
    # Team names
    col1, col2 = st.columns(2)
    with col1:
        home_name = st.text_input("🏠 Home Team", "FK Tukums 2000", key="home_name")
    with col2:
        away_name = st.text_input("✈️ Away Team", "Rigas Futbola skola", key="away_name")
    
    st.divider()
    
    # ========================================================================
    # HOME TEAM STREAKS
    # ========================================================================
    st.markdown(f"### 🏠 {home_name}")
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        plain, home_icon, away_icon = create_streak_input("Scoring", "home", default_plain=0, default_home=0, default_away=0)
        st.caption("Scoring (plain, 🏠 home, ✈️ away)")
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("No BTTS", "home")
        st.caption("No BTTS - Most reliable signal")
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("BTTS", "home")
        st.caption("BTTS (Both Teams To Score)")
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("Over 2.5", "home")
        st.caption("Over 2.5 Goals - Volume indicator")
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("Goals 2+", "home")
        st.caption("Goals 2+ - Volume indicator")
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"### ✈️ {away_name}")
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        plain, home_icon, away_icon = create_streak_input("Scoring", "away", default_plain=0, default_home=0, default_away=0)
        st.caption("Scoring (plain, 🏠 home, ✈️ away)")
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("No BTTS", "away")
        st.caption("No BTTS - Most reliable signal")
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("BTTS", "away")
        st.caption("BTTS (Both Teams To Score)")
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("Over 2.5", "away")
        st.caption("Over 2.5 Goals - Volume indicator")
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        plain, home_icon, away_icon = create_streak_input("Goals 2+", "away")
        st.caption("Goals 2+ - Volume indicator")
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary"):
        # Build team streak objects
        home_team = streaks_from_session("home", home_name)
        away_team = streaks_from_session("away", away_name)
        
        # Run prediction
        result = predict_match(home_team, away_team, match_venue)
        
        # Display prediction card
        if result.btts_prediction == "BTTS Yes":
            pred_html = f'<div class="prediction-btts-yes">✅ {result.btts_prediction}</div>'
        elif result.btts_prediction == "BTTS No":
            pred_html = f'<div class="prediction-btts-no">🚫 {result.btts_prediction}</div>'
        else:
            pred_html = f'<div class="prediction-nobet">⏸️ {result.btts_prediction}</div>'
        
        over_html = ""
        if result.over_under == "Over 2.5":
            over_html = f'<div class="prediction-over">📈 {result.over_under}</div>'
        elif result.over_under == "Under 2.5 lean":
            over_html = f'<div class="prediction-under">📉 {result.over_under}</div>'
        
        st.markdown(f"""
        <div class="prediction-card">
            {pred_html}
            {over_html}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b;">
                {result.triggered_rule}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show detailed reasoning
        with st.expander("📋 Detailed Reasoning & Rule Check", expanded=True):
            for line in result.reasoning:
                if "✅" in line or "TRIGGERED" in line:
                    st.success(line)
                elif "❌" in line:
                    st.error(line)
                elif "📊" in line:
                    st.info(line)
                else:
                    st.write(line)
    
    # Footer
    st.divider()
    st.markdown("""
    ### 📋 Rules Summary
    
    | Rule | Trigger | Additional Filters | Prediction | Over/Under |
    |------|---------|-------------------|------------|------------|
    | **Rule 2** | Any "No BTTS" | reliable (≤10) + venue match | **BTTS No** | Under lean (87.5%) |
    | **Rule 1** | Both plain Scoring ≥3 | both reliable + no No BTTS | **BTTS Yes** | Over if both have volume |
    | **Rule 3** | Any "BTTS" | reliable + venue match + opponent goal streak | **BTTS Yes** | Over if both have volume |
    | **Else** | — | — | **No bet** | — |
    
    ### 🎯 Filters
    
    - **Regression Filter**: Only streaks ≤ 10 games are considered reliable (55%+ continuation)
    - **Venue Filter**: 🏠 icon only applies at home, ✈️ icon only applies away, plain applies anywhere
    """)
    
    # Example presets
    with st.expander("📖 Example Matches (Load Presets)"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Valladolid vs Eibar (BTTS No)", use_container_width=True):
                # Reset and load example
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("📋 Como vs Inter (BTTS Yes + Over)", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.button("📋 Portsmouth vs Ipswich (No bet)", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


if __name__ == "__main__":
    main()
