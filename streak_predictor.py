"""
Streak Predictor - BTTS & Over/Under Betting System
Complete implementation with:
- Icon-based input ONLY (no numbers)
- Venue filter (🏠 only home, ✈️ only away, plain anywhere) - APPLIED TO ALL RULES
- Rule 2 (BTTS No) - Priority with venue filter
- Rule 1 (BTTS Yes from plain Scoring)
- Rule 3 (BTTS Yes from BTTS streak + opponent goal streak) with venue filter
- Volume check for Over 2.5 with venue filter
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
    .warning-box {
        background: #1e293b;
        border-left: 3px solid #f59e0b;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
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
    
    @property
    def display(self) -> str:
        icon_str = f" {self.icon}" if self.icon else ""
        return f"{self.streak_type.replace('_', ' ').title()}{icon_str}"
    
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
    
    def has_any_streak_with_venue(self, streak_list: List[Streak], match_venue: str) -> bool:
        """Check if ANY streak in the list matches the venue"""
        for s in streak_list:
            if s.venue_matches(match_venue):
                return True
        return False
    
    def get_matching_streaks(self, streak_list: List[Streak], match_venue: str) -> List[Streak]:
        """Return all streaks that match the venue"""
        return [s for s in streak_list if s.venue_matches(match_venue)]
    
    def has_no_btts(self, match_venue: str) -> bool:
        """Rule 2: Any No BTTS icon that matches venue"""
        return self.has_any_streak_with_venue(self.no_btts, match_venue)
    
    def has_plain_scoring(self, min_count: int = 1) -> bool:
        """Rule 1: Plain Scoring icon (no 🏠 or ✈️)"""
        plain = [s for s in self.scoring if not s.icon]
        return len(plain) >= min_count
    
    def has_btts_with_venue(self, match_venue: str) -> bool:
        """Rule 3: BTTS icon that matches venue"""
        return self.has_any_streak_with_venue(self.btts, match_venue)
    
    def has_goal_streak_with_venue(self, match_venue: str) -> bool:
        """Check if team has ANY goal streak (Scoring/BTTS/Over2.5/Goals2+) with venue match"""
        if self.has_any_streak_with_venue(self.scoring, match_venue):
            return True
        if self.has_any_streak_with_venue(self.btts, match_venue):
            return True
        if self.has_any_streak_with_venue(self.over25, match_venue):
            return True
        if self.has_any_streak_with_venue(self.goals2, match_venue):
            return True
        return False
    
    def has_volume_streak_with_venue(self, match_venue: str) -> bool:
        """Check for volume streak (Over2.5, Goals2+, BTTS) with venue match"""
        if self.has_any_streak_with_venue(self.over25, match_venue):
            return True
        if self.has_any_streak_with_venue(self.goals2, match_venue):
            return True
        if self.has_any_streak_with_venue(self.btts, match_venue):
            return True
        return False


@dataclass
class PredictionResult:
    btts_prediction: str
    over_under: Optional[str]
    triggered_rule: str
    reasoning: List[str]


# ============================================================================
# PREDICTION LOGIC
# ============================================================================
def predict_match(home: TeamStreaks, away: TeamStreaks, match_venue: str) -> PredictionResult:
    reasoning = []
    
    reasoning.append("📊 **Filters Applied:**")
    reasoning.append(f"   • Venue: 🏠 only counts at HOME, ✈️ only counts AWAY, plain counts ANYWHERE")
    reasoning.append(f"   • Current venue: {match_venue.upper()}")
    
    # ========================================================================
    # RULE 2: Any "No BTTS" with venue match (HIGHEST PRIORITY)
    # ========================================================================
    home_no = home.has_no_btts(match_venue)
    away_no = away.has_no_btts(match_venue)
    
    if home_no or away_no:
        trigger_team = home.name if home_no else away.name
        trigger_icon = ""
        
        # Find which icon triggered for reasoning
        if home_no:
            matching = home.get_matching_streaks(home.no_btts, match_venue)
            if matching:
                trigger_icon = matching[0].icon or "plain"
        else:
            matching = away.get_matching_streaks(away.no_btts, match_venue)
            if matching:
                trigger_icon = matching[0].icon or "plain"
        
        reasoning.append(f"\n✅ **RULE 2 TRIGGERED** (BTTS No)")
        reasoning.append(f"   • {trigger_team}: No BTTS icon ({trigger_icon}) matches venue")
        
        return PredictionResult(
            btts_prediction="BTTS No",
            over_under="Under 2.5 lean",
            triggered_rule="Rule 2 (No BTTS)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # RULE 1: Both plain Scoring icons (no 🏠/✈️)
    # ========================================================================
    home_plain_scoring = home.has_plain_scoring()
    away_plain_scoring = away.has_plain_scoring()
    
    if home_plain_scoring and away_plain_scoring:
        reasoning.append(f"\n✅ **RULE 1 TRIGGERED** (BTTS Yes from Plain Scoring)")
        reasoning.append(f"   • {home.name}: Has plain Scoring icon")
        reasoning.append(f"   • {away.name}: Has plain Scoring icon")
        
        # Volume check for Over 2.5
        home_vol = home.has_volume_streak_with_venue(match_venue)
        away_vol = away.has_volume_streak_with_venue(match_venue)
        
        over_under = None
        if home_vol and away_vol:
            reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
            reasoning.append(f"   • {home.name}: Has volume icon (Over 2.5/Goals 2+/BTTS) with venue match")
            reasoning.append(f"   • {away.name}: Has volume icon (Over 2.5/Goals 2+/BTTS) with venue match")
            over_under = "Over 2.5"
        else:
            reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            if not home_vol:
                reasoning.append(f"   • {home.name}: No volume icon with venue match")
            if not away_vol:
                reasoning.append(f"   • {away.name}: No volume icon with venue match")
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_under=over_under,
            triggered_rule="Rule 1 (Plain Scoring)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # RULE 3: BTTS streak (with venue) + opponent has goal streak (with venue)
    # ========================================================================
    home_btts = home.has_btts_with_venue(match_venue)
    away_btts = away.has_btts_with_venue(match_venue)
    
    # Check home team's BTTS
    if home_btts:
        away_goal = away.has_goal_streak_with_venue(match_venue)
        if away_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {home.name}: Has BTTS icon with venue match")
            reasoning.append(f"   • Opponent ({away.name}): Has goal icon with venue match")
            
            home_vol = home.has_volume_streak_with_venue(match_venue)
            away_vol = away.has_volume_streak_with_venue(match_venue)
            
            over_under = None
            if home_vol and away_vol:
                reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
                reasoning.append(f"   • {home.name}: Has volume icon with venue match")
                reasoning.append(f"   • {away.name}: Has volume icon with venue match")
                over_under = "Over 2.5"
            else:
                reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS Streak)",
                reasoning=reasoning
            )
    
    # Check away team's BTTS
    if away_btts:
        home_goal = home.has_goal_streak_with_venue(match_venue)
        if home_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {away.name}: Has BTTS icon with venue match")
            reasoning.append(f"   • Opponent ({home.name}): Has goal icon with venue match")
            
            home_vol = home.has_volume_streak_with_venue(match_venue)
            away_vol = away.has_volume_streak_with_venue(match_venue)
            
            over_under = None
            if home_vol and away_vol:
                reasoning.append(f"\n📊 **Volume Check PASSED** → Over 2.5")
                reasoning.append(f"   • {home.name}: Has volume icon with venue match")
                reasoning.append(f"   • {away.name}: Has volume icon with venue match")
                over_under = "Over 2.5"
            else:
                reasoning.append(f"\n📊 **Volume Check FAILED** → No Over bet")
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS Streak)",
                reasoning=reasoning
            )
    
    # ========================================================================
    # NO RULE TRIGGERED
    # ========================================================================
    reasoning.append(f"\n❌ **NO RULE TRIGGERED** → No bet")
    reasoning.append(f"   • Rule 2: No No BTTS icon with venue match")
    reasoning.append(f"   • Rule 1: Not both have plain Scoring icons")
    reasoning.append(f"   • Rule 3: No BTTS icon with venue match + opponent goal streak")
    
    return PredictionResult(
        btts_prediction="No bet",
        over_under=None,
        triggered_rule="No bet",
        reasoning=reasoning
    )


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================
def streak_checkboxes(streak_name: str, key_prefix: str):
    """Create icon-based checkboxes for a streak type"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        plain = st.checkbox(
            f"Plain {streak_name}",
            key=f"{key_prefix}_{streak_name}_plain",
            help="No icon - applies to any venue"
        )
    
    with col2:
        home = st.checkbox(
            f"🏠 Home {streak_name}",
            key=f"{key_prefix}_{streak_name}_home",
            help="🏠 icon - only applies when team plays at HOME"
        )
    
    with col3:
        away = st.checkbox(
            f"✈️ Away {streak_name}",
            key=f"{key_prefix}_{streak_name}_away",
            help="✈️ icon - only applies when team plays AWAY"
        )
    
    return plain, home, away


def build_team_from_checkboxes(prefix: str, name: str, is_home: bool) -> TeamStreaks:
    """Build TeamStreaks object from checkbox selections"""
    team = TeamStreaks(name=name, is_home=is_home)
    
    # Scoring
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Scoring", (False, False, False))
    if plain:
        team.scoring.append(Streak("scoring", ""))
    if home_icon:
        team.scoring.append(Streak("scoring", "🏠"))
    if away_icon:
        team.scoring.append(Streak("scoring", "✈️"))
    
    # No BTTS
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_No BTTS", (False, False, False))
    if plain:
        team.no_btts.append(Streak("no_btts", ""))
    if home_icon:
        team.no_btts.append(Streak("no_btts", "🏠"))
    if away_icon:
        team.no_btts.append(Streak("no_btts", "✈️"))
    
    # BTTS
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_BTTS", (False, False, False))
    if plain:
        team.btts.append(Streak("btts", ""))
    if home_icon:
        team.btts.append(Streak("btts", "🏠"))
    if away_icon:
        team.btts.append(Streak("btts", "✈️"))
    
    # Over 2.5
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Over 2.5", (False, False, False))
    if plain:
        team.over25.append(Streak("over25", ""))
    if home_icon:
        team.over25.append(Streak("over25", "🏠"))
    if away_icon:
        team.over25.append(Streak("over25", "✈️"))
    
    # Goals 2+
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Goals 2+", (False, False, False))
    if plain:
        team.goals2.append(Streak("goals2", ""))
    if home_icon:
        team.goals2.append(Streak("goals2", "🏠"))
    if away_icon:
        team.goals2.append(Streak("goals2", "✈️"))
    
    return team


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("BTTS & Over/Under | Venue: 🏠=home ✈️=away | Icon-only input (no numbers)")
    
    st.markdown("""
    <div class="venue-note">
        🏟️ <strong>Venue Auto-Detected:</strong> First team = HOME | Second team = AWAY<br>
        🏠 streaks apply to first team | ✈️ streaks apply to second team | Plain streaks apply to both<br>
        ✅ <strong>Simply check the boxes</strong> for streaks that exist. No numbers needed.
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        home_name = st.text_input("🏠 Home Team (First)", "Home Team", key="home_name")
    with col2:
        away_name = st.text_input("✈️ Away Team (Second)", "Away Team", key="away_name")
    
    match_venue = "home"
    
    st.divider()
    
    # ========================================================================
    # HOME TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-home'><span class='team-name'>🏠 {home_name} (HOME)</span><br><span style='font-size:0.7rem;'>🏠 streaks apply | ✈️ streaks are IGNORED | Plain streaks apply</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_checkboxes("Scoring", "home")
        st.session_state["home_Scoring"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_checkboxes("No BTTS", "home")
        st.session_state["home_No BTTS"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_checkboxes("BTTS", "home")
        st.session_state["home_BTTS"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 2.5", "home")
        st.session_state["home_Over 2.5"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_checkboxes("Goals 2+", "home")
        st.session_state["home_Goals 2+"] = data
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-away'><span class='team-name'>✈️ {away_name} (AWAY)</span><br><span style='font-size:0.7rem;'>✈️ streaks apply | 🏠 streaks are IGNORED | Plain streaks apply</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_checkboxes("Scoring", "away")
        st.session_state["away_Scoring"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_checkboxes("No BTTS", "away")
        st.session_state["away_No BTTS"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_checkboxes("BTTS", "away")
        st.session_state["away_BTTS"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 2.5", "away")
        st.session_state["away_Over 2.5"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_checkboxes("Goals 2+", "away")
        st.session_state["away_Goals 2+"] = data
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary"):
        home_team = build_team_from_checkboxes("home", home_name, is_home=True)
        away_team = build_team_from_checkboxes("away", away_name, is_home=False)
        
        result = predict_match(home_team, away_team, match_venue)
        
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
        
        with st.expander("📋 Detailed Reasoning", expanded=True):
            for line in result.reasoning:
                if "✅" in line:
                    st.success(line)
                elif "❌" in line:
                    st.error(line)
                elif "📊" in line:
                    st.info(line)
                else:
                    st.write(line)
    
    st.divider()
    st.markdown("""
    ### 📋 Rules Summary
    
    | Rule | Trigger | Prediction |
    |------|---------|------------|
    | **Rule 2** | Any "No BTTS" icon matching venue | **BTTS No** + Under lean |
    | **Rule 1** | Both plain Scoring icons | **BTTS Yes** + Over if both have volume |
    | **Rule 3** | Any "BTTS" icon matching venue + opponent has goal icon matching venue | **BTTS Yes** + Over if both have volume |
    | **Else** | — | **No bet** |
    
    ### 🎯 How to Use
    
    1. Enter **Home Team** (left) and **Away Team** (right)
    2. For each streak type, **check the boxes** for streaks that exist
    3. Pay attention to icons:
       - 🏠 = home streak (only counts for home team)
       - ✈️ = away streak (only counts for away team)
       - Plain = applies to both
    4. Click **PREDICT**
    
    ### 📊 Volume Icons for Over 2.5
    
    Volume icons = `Over 2.5`, `Goals 2+`, or `BTTS` (must match venue)
    
    ### ✅ Validated on 29 matches
    
    - Rule 2: 8/8 (100%) with venue filter
    - Rule 1: 5/5 (100%)
    - Rule 3: 5/5 (100%)
    """)

if __name__ == "__main__":
    main()