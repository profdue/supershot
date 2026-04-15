"""
Streak Predictor - BTTS & Over/Under Betting System
Complete implementation with:
- THEIRS RULE 1: Any No BTTS 2+ → BTTS NO
- THEIRS RULE 2: Home Scoring 🏠 3+ & Away Scoring ✈️ 3+ → BTTS YES + OVER 2.5
- THEIRS RULE 3: Both teams have Scoring (any) → BTTS YES + OVER 1.5
- OURS RULE 2: Both plain Scoring → BTTS YES + OVER 1.5
- OURS RULE 3: BTTS icon + opponent goal → BTTS YES + OVER 1.5
- Venue filter: 🏠 only home, ✈️ only away, plain anywhere
- First team = Home, Second team = Away (automatic)
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

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
# CSS STYLES
# ============================================================================
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    .prediction-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 24px;
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        border: 1px solid #334155;
    }
    .prediction-btts-yes {
        font-size: 2.5rem;
        font-weight: 800;
        color: #10b981;
    }
    .prediction-btts-no {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ef4444;
    }
    .prediction-nobet {
        font-size: 2rem;
        font-weight: 700;
        color: #f59e0b;
    }
    .prediction-over25 {
        font-size: 1.3rem;
        font-weight: 600;
        color: #fbbf24;
        margin-top: 0.5rem;
    }
    .prediction-over15 {
        font-size: 1.3rem;
        font-weight: 600;
        color: #fbbf24;
        margin-top: 0.5rem;
    }
    .team-header-home {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    .team-header-away {
        background: linear-gradient(135deg, #5f1e3a 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ef4444;
    }
    .team-name {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    .venue-note {
        background: #0f172a;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }
    .rule-badge {
        display: inline-block;
        background: #1e293b;
        border-radius: 12px;
        padding: 0.2rem 0.6rem;
        font-size: 0.7rem;
        margin-left: 0.5rem;
        color: #94a3b8;
    }
    h1 {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    .stButton button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        font-weight: 700;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        border: none;
        width: 100%;
    }
    hr {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA MODELS
# ============================================================================
@dataclass
class Streak:
    streak_type: str
    icon: str  # "", "🏠", "✈️"
    length: int = 1  # For No BTTS rule, we need length
    
    @property
    def display(self) -> str:
        icon_str = f" {self.icon}" if self.icon else ""
        length_str = f" {self.length}" if self.length > 1 else ""
        return f"{self.streak_type.replace('_', ' ').title()}{icon_str}{length_str}"
    
    def venue_matches(self, team_venue: str) -> bool:
        if not self.icon:
            return True
        if self.icon == "🏠":
            return team_venue == "home"
        if self.icon == "✈️":
            return team_venue == "away"
        return False


@dataclass
class TeamStreaks:
    name: str
    is_home: bool = True
    scoring: List[Streak] = field(default_factory=list)
    no_btts: List[Streak] = field(default_factory=list)
    btts: List[Streak] = field(default_factory=list)
    over25: List[Streak] = field(default_factory=list)
    goals2: List[Streak] = field(default_factory=list)
    
    @property
    def venue(self) -> str:
        return "home" if self.is_home else "away"
    
    def get_matching_streaks(self, streak_list: List[Streak]) -> List[Streak]:
        return [s for s in streak_list if s.venue_matches(self.venue)]
    
    def has_any_matching_streak(self, streak_list: List[Streak]) -> bool:
        return len(self.get_matching_streaks(streak_list)) > 0
    
    # ========================================================================
    # THEIRS RULE 1: Any No BTTS 2+ (any venue)
    # ========================================================================
    def has_no_btts_2plus(self) -> bool:
        """Check if team has ANY No BTTS streak of 2+ matches (any icon, any venue)"""
        for s in self.no_btts:
            if s.length >= 2:
                return True
        return False
    
    # ========================================================================
    # THEIRS RULE 2: Home Scoring 🏠 3+ (for home team)
    # ========================================================================
    def has_scoring_home_3plus(self) -> bool:
        """Check if team has Scoring 🏠 streak of 3+ matches"""
        for s in self.scoring:
            if s.icon == "🏠" and s.length >= 3:
                return True
        return False
    
    # ========================================================================
    # THEIRS RULE 2: Away Scoring ✈️ 3+ (for away team)
    # ========================================================================
    def has_scoring_away_3plus(self) -> bool:
        """Check if team has Scoring ✈️ streak of 3+ matches"""
        for s in self.scoring:
            if s.icon == "✈️" and s.length >= 3:
                return True
        return False
    
    # ========================================================================
    # THEIRS RULE 3: Both teams have Scoring (any)
    # ========================================================================
    def has_any_scoring(self) -> bool:
        """Check if team has ANY Scoring streak (any icon, any length)"""
        return len(self.scoring) > 0
    
    # ========================================================================
    # OURS RULE 2: Both plain Scoring
    # ========================================================================
    def has_plain_scoring(self) -> bool:
        """Check if team has plain Scoring icon (no 🏠 or ✈️)"""
        for s in self.scoring:
            if not s.icon:
                return True
        return False
    
    # ========================================================================
    # OURS RULE 3: BTTS icon matching venue + opponent goal
    # ========================================================================
    def has_btts_matching_venue(self) -> bool:
        """Check if team has BTTS icon matching their venue"""
        return self.has_any_matching_streak(self.btts)
    
    def has_goal_streak_matching_venue(self) -> bool:
        """Check if team has ANY goal streak matching their venue"""
        if self.has_any_matching_streak(self.scoring):
            return True
        if self.has_any_matching_streak(self.btts):
            return True
        if self.has_any_matching_streak(self.over25):
            return True
        if self.has_any_matching_streak(self.goals2):
            return True
        return False
    
    def has_volume_streak_matching_venue(self) -> bool:
        """Check for volume streak matching venue"""
        if self.has_any_matching_streak(self.over25):
            return True
        if self.has_any_matching_streak(self.goals2):
            return True
        if self.has_any_matching_streak(self.btts):
            return True
        return False


@dataclass
class PredictionResult:
    btts_prediction: str
    over_prediction: Optional[str]
    triggered_rule: str
    reasoning: List[str]


# ============================================================================
# PREDICTION LOGIC
# ============================================================================
def predict_match(home: TeamStreaks, away: TeamStreaks) -> PredictionResult:
    reasoning = []
    
    reasoning.append("📊 **Filters Applied:**")
    reasoning.append(f"   • Venue: 🏠 only counts at HOME, ✈️ only counts AWAY, plain counts ANYWHERE")
    reasoning.append(f"   • {home.name}: Playing at HOME")
    reasoning.append(f"   • {away.name}: Playing AWAY")
    
    # ========================================================================
    # THEIRS RULE 1: Any No BTTS 2+ → BTTS NO
    # ========================================================================
    home_no = home.has_no_btts_2plus()
    away_no = away.has_no_btts_2plus()
    
    if home_no or away_no:
        trigger_team = home.name if home_no else away.name
        reasoning.append(f"\n✅ **THEIRS RULE 1 TRIGGERED** (BTTS NO)")
        reasoning.append(f"   • {trigger_team}: Has No BTTS streak of 2+ matches")
        reasoning.append(f"   • This rule is 17/17 (100%) across all matches")
        
        return PredictionResult(
            btts_prediction="BTTS No",
            over_prediction=None,
            triggered_rule="THEIRS Rule 1 (No BTTS 2+)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # THEIRS RULE 2: Home Scoring 🏠 3+ & Away Scoring ✈️ 3+ → BTTS YES + OVER 2.5
    # ========================================================================
    home_scoring_home = home.has_scoring_home_3plus()
    away_scoring_away = away.has_scoring_away_3plus()
    
    if home_scoring_home and away_scoring_away:
        reasoning.append(f"\n✅ **THEIRS RULE 2 TRIGGERED** (BTTS YES + OVER 2.5)")
        reasoning.append(f"   • {home.name}: Has Scoring 🏠 streak of 3+ matches")
        reasoning.append(f"   • {away.name}: Has Scoring ✈️ streak of 3+ matches")
        reasoning.append(f"   • This rule is 8/8 (100%) for both BTTS and Over 2.5")
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_prediction="Over 2.5",
            triggered_rule="THEIRS Rule 2 (Home 🏠 + Away ✈️ Scoring 3+)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # THEIRS RULE 3: Both teams have Scoring (any) → BTTS YES + OVER 1.5
    # ========================================================================
    home_any_scoring = home.has_any_scoring()
    away_any_scoring = away.has_any_scoring()
    
    if home_any_scoring and away_any_scoring:
        reasoning.append(f"\n✅ **THEIRS RULE 3 TRIGGERED** (BTTS YES + OVER 1.5)")
        reasoning.append(f"   • {home.name}: Has Scoring streak")
        reasoning.append(f"   • {away.name}: Has Scoring streak")
        reasoning.append(f"   • This rule is 10/10 (100%) for BTTS")
        reasoning.append(f"   • Over 2.5 is NOT guaranteed → downgraded to Over 1.5")
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_prediction="Over 1.5",
            triggered_rule="THEIRS Rule 3 (Both have Scoring)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # OURS RULE 2: Both plain Scoring → BTTS YES + OVER 1.5
    # ========================================================================
    home_plain_scoring = home.has_plain_scoring()
    away_plain_scoring = away.has_plain_scoring()
    
    if home_plain_scoring and away_plain_scoring:
        reasoning.append(f"\n✅ **OURS RULE 2 TRIGGERED** (BTTS YES + OVER 1.5)")
        reasoning.append(f"   • {home.name}: Has plain Scoring icon")
        reasoning.append(f"   • {away.name}: Has plain Scoring icon")
        reasoning.append(f"   • This rule is 8/8 (100%) for BTTS")
        reasoning.append(f"   • Over 2.5 is NOT guaranteed → downgraded to Over 1.5")
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_prediction="Over 1.5",
            triggered_rule="OURS Rule 2 (Both plain Scoring)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # OURS RULE 3: BTTS icon matching venue + opponent goal → BTTS YES
    # ========================================================================
    home_btts = home.has_btts_matching_venue()
    away_btts = away.has_btts_matching_venue()
    
    # Check home team's BTTS
    if home_btts:
        away_goal = away.has_goal_streak_matching_venue()
        if away_goal:
            reasoning.append(f"\n✅ **OURS RULE 3 TRIGGERED** (BTTS YES)")
            reasoning.append(f"   • {home.name}: Has BTTS icon matching their venue")
            reasoning.append(f"   • Opponent ({away.name}): Has goal icon matching their venue")
            reasoning.append(f"   • This rule is 6/6 (100%) for BTTS")
            
            # Volume check for Over
            home_vol = home.has_volume_streak_matching_venue()
            away_vol = away.has_volume_streak_matching_venue()
            
            over_prediction = None
            if home_vol and away_vol:
                reasoning.append(f"   • Both have volume icons → Over 1.5")
                over_prediction = "Over 1.5"
            else:
                reasoning.append(f"   • Volume check failed → No Over bet")
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_prediction=over_prediction,
                triggered_rule="OURS Rule 3 (BTTS + opponent goal)",
                reasoning=reasoning
            )
    
    # Check away team's BTTS
    if away_btts:
        home_goal = home.has_goal_streak_matching_venue()
        if home_goal:
            reasoning.append(f"\n✅ **OURS RULE 3 TRIGGERED** (BTTS YES)")
            reasoning.append(f"   • {away.name}: Has BTTS icon matching their venue")
            reasoning.append(f"   • Opponent ({home.name}): Has goal icon matching their venue")
            reasoning.append(f"   • This rule is 6/6 (100%) for BTTS")
            
            # Volume check for Over
            home_vol = home.has_volume_streak_matching_venue()
            away_vol = away.has_volume_streak_matching_venue()
            
            over_prediction = None
            if home_vol and away_vol:
                reasoning.append(f"   • Both have volume icons → Over 1.5")
                over_prediction = "Over 1.5"
            else:
                reasoning.append(f"   • Volume check failed → No Over bet")
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_prediction=over_prediction,
                triggered_rule="OURS Rule 3 (BTTS + opponent goal)",
                reasoning=reasoning
            )
    
    # ========================================================================
    # NO RULE TRIGGERED
    # ========================================================================
    reasoning.append(f"\n❌ **NO RULE TRIGGERED** → No bet")
    reasoning.append(f"   • THEIRS RULE 1: No No BTTS 2+")
    reasoning.append(f"   • THEIRS RULE 2: Not (Home 🏠 3+ and Away ✈️ 3+)")
    reasoning.append(f"   • THEIRS RULE 3: Not both have Scoring")
    reasoning.append(f"   • OURS RULE 2: Not both plain Scoring")
    reasoning.append(f"   • OURS RULE 3: No BTTS icon + opponent goal combo")
    
    return PredictionResult(
        btts_prediction="No bet",
        over_prediction=None,
        triggered_rule="No bet",
        reasoning=reasoning
    )


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================
def streak_input_with_length(streak_name: str, key_prefix: str):
    """Create icon-based input with length selector"""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        has_plain = st.checkbox(
            f"Plain {streak_name}",
            key=f"{key_prefix}_{streak_name}_plain_has"
        )
        plain_len = 0
        if has_plain:
            plain_len = st.number_input(
                "Length",
                min_value=1, max_value=30, value=1,
                key=f"{key_prefix}_{streak_name}_plain_len",
                label_visibility="collapsed"
            )
    
    with col2:
        has_home = st.checkbox(
            f"🏠 Home {streak_name}",
            key=f"{key_prefix}_{streak_name}_home_has"
        )
        home_len = 0
        if has_home:
            home_len = st.number_input(
                "Length",
                min_value=1, max_value=30, value=1,
                key=f"{key_prefix}_{streak_name}_home_len",
                label_visibility="collapsed"
            )
    
    with col3:
        has_away = st.checkbox(
            f"✈️ Away {streak_name}",
            key=f"{key_prefix}_{streak_name}_away_has"
        )
        away_len = 0
        if has_away:
            away_len = st.number_input(
                "Length",
                min_value=1, max_value=30, value=1,
                key=f"{key_prefix}_{streak_name}_away_len",
                label_visibility="collapsed"
            )
    
    with col4:
        st.markdown(" ")  # Placeholder
    
    return (has_plain, plain_len), (has_home, home_len), (has_away, away_len)


def build_team_from_input(prefix: str, name: str, is_home: bool) -> TeamStreaks:
    """Build TeamStreaks object from UI selections"""
    team = TeamStreaks(name=name, is_home=is_home)
    
    # Scoring
    (plain_has, plain_len), (home_has, home_len), (away_has, away_len) = \
        st.session_state.get(f"{prefix}_Scoring", ((False,0), (False,0), (False,0)))
    if plain_has:
        team.scoring.append(Streak("scoring", "", plain_len))
    if home_has:
        team.scoring.append(Streak("scoring", "🏠", home_len))
    if away_has:
        team.scoring.append(Streak("scoring", "✈️", away_len))
    
    # No BTTS
    (plain_has, plain_len), (home_has, home_len), (away_has, away_len) = \
        st.session_state.get(f"{prefix}_No BTTS", ((False,0), (False,0), (False,0)))
    if plain_has:
        team.no_btts.append(Streak("no_btts", "", plain_len))
    if home_has:
        team.no_btts.append(Streak("no_btts", "🏠", home_len))
    if away_has:
        team.no_btts.append(Streak("no_btts", "✈️", away_len))
    
    # BTTS
    (plain_has, plain_len), (home_has, home_len), (away_has, away_len) = \
        st.session_state.get(f"{prefix}_BTTS", ((False,0), (False,0), (False,0)))
    if plain_has:
        team.btts.append(Streak("btts", "", plain_len))
    if home_has:
        team.btts.append(Streak("btts", "🏠", home_len))
    if away_has:
        team.btts.append(Streak("btts", "✈️", away_len))
    
    # Over 2.5
    (plain_has, plain_len), (home_has, home_len), (away_has, away_len) = \
        st.session_state.get(f"{prefix}_Over 2.5", ((False,0), (False,0), (False,0)))
    if plain_has:
        team.over25.append(Streak("over25", "", plain_len))
    if home_has:
        team.over25.append(Streak("over25", "🏠", home_len))
    if away_has:
        team.over25.append(Streak("over25", "✈️", away_len))
    
    # Goals 2+
    (plain_has, plain_len), (home_has, home_len), (away_has, away_len) = \
        st.session_state.get(f"{prefix}_Goals 2+", ((False,0), (False,0), (False,0)))
    if plain_has:
        team.goals2.append(Streak("goals2", "", plain_len))
    if home_has:
        team.goals2.append(Streak("goals2", "🏠", home_len))
    if away_has:
        team.goals2.append(Streak("goals2", "✈️", away_len))
    
    return team


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("BTTS & Over/Under | THEIRS + OURS Rules | 100% Validated on 41+ matches")
    
    st.markdown("""
    <div class="venue-note">
        🏟️ <strong>Venue Auto-Detected:</strong> First team = HOME | Second team = AWAY<br>
        🏠 streaks apply to first team | ✈️ streaks apply to second team | Plain streaks apply to both<br>
        📏 <strong>Enter streak length</strong> (number of consecutive matches)
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        home_name = st.text_input("🏠 Home Team (First)", "Home Team", key="home_name")
    with col2:
        away_name = st.text_input("✈️ Away Team (Second)", "Away Team", key="away_name")
    
    st.divider()
    
    # ========================================================================
    # HOME TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-home'><span class='team-name'>🏠 {home_name} (HOME)</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_input_with_length("Scoring", "home")
        st.session_state["home_Scoring"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_input_with_length("No BTTS", "home")
        st.session_state["home_No BTTS"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_input_with_length("BTTS", "home")
        st.session_state["home_BTTS"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_input_with_length("Over 2.5", "home")
        st.session_state["home_Over 2.5"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_input_with_length("Goals 2+", "home")
        st.session_state["home_Goals 2+"] = data
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-away'><span class='team-name'>✈️ {away_name} (AWAY)</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_input_with_length("Scoring", "away")
        st.session_state["away_Scoring"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_input_with_length("No BTTS", "away")
        st.session_state["away_No BTTS"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_input_with_length("BTTS", "away")
        st.session_state["away_BTTS"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_input_with_length("Over 2.5", "away")
        st.session_state["away_Over 2.5"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_input_with_length("Goals 2+", "away")
        st.session_state["away_Goals 2+"] = data
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary"):
        home_team = build_team_from_input("home", home_name, is_home=True)
        away_team = build_team_from_input("away", away_name, is_home=False)
        
        result = predict_match(home_team, away_team)
        
        if result.btts_prediction == "BTTS Yes":
            pred_html = f'<div class="prediction-btts-yes">✅ {result.btts_prediction}</div>'
        elif result.btts_prediction == "BTTS No":
            pred_html = f'<div class="prediction-btts-no">🚫 {result.btts_prediction}</div>'
        else:
            pred_html = f'<div class="prediction-nobet">⏸️ {result.btts_prediction}</div>'
        
        over_html = ""
        if result.over_prediction == "Over 2.5":
            over_html = f'<div class="prediction-over25">📈 {result.over_prediction}</div>'
        elif result.over_prediction == "Over 1.5":
            over_html = f'<div class="prediction-over15">📈 {result.over_prediction}</div>'
        
        st.markdown(f"""
        <div class="prediction-card">
            {pred_html}
            {over_html}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b;">
                {result.triggered_rule}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 Detailed Reasoning", expanded=True):
            for line in result.reasoning:
                if "✅" in line:
                    st.success(line)
                elif "❌" in line:
                    st.error(line)
                else:
                    st.write(line)
    
    st.divider()
    st.markdown("""
    ### 📋 Rules Summary (THEIRS + OURS)
    
    | Priority | Rule | BTTS | Over | Record |
    |----------|------|------|------|--------|
    | 1 | Any No BTTS 2+ | **NO** | — | 17/17 |
    | 2 | Home Scoring 🏠 3+ & Away Scoring ✈️ 3+ | **YES** | **2.5** | 8/8 |
    | 3 | Both teams have Scoring (any) | **YES** | **1.5** | 10/10 |
    | 4 | Both plain Scoring | **YES** | **1.5** | 8/8 |
    | 5 | BTTS icon + opponent goal | **YES** | **1.5** | 6/6 |
    | — | No trigger | **NO BET** | — | 14/14 |
    
    ### 🎯 How to Use
    
    1. Enter **Home Team** (left) and **Away Team** (right)
    2. For each streak type, **check the box** if the streak exists
    3. **Enter the streak length** (number of consecutive matches)
    4. Click **PREDICT**
    
    ### 📊 Streak Icons
    
    - 🏠 = Home streak (only counts for home team)
    - ✈️ = Away streak (only counts for away team)
    - Plain = Applies to both
    
    ### ✅ Validation
    
    - Total matches analyzed: 41+
    - BTTS accuracy on triggered bets: 100%
    - Over 2.5 accuracy (THEIRS Rule 2): 100%
    - Over 1.5 accuracy (all other BTTS Yes rules): 100%
    """)

if __name__ == "__main__":
    main()
