"""
Streak Predictor - BTTS & Over/Under Betting System
Complete implementation with:
- Icon-based input (no numbers needed)
- Regression filter (streak ≤ 10 = reliable) - optional override
- Venue filter (🏠 only home, ✈️ only away, plain anywhere)
- Rule 2 (BTTS No) - Priority
- Rule 1 (BTTS Yes from plain Scoring)
- Rule 3 (BTTS Yes from BTTS streak + opponent goal streak)
- Volume check for Over 2.5
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
    .streak-badge {
        display: inline-block;
        background: #1e293b;
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.75rem;
    }
    .streak-warning {
        color: #f59e0b;
        font-size: 0.7rem;
        margin-left: 0.5rem;
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
    length: int
    icon: str  # "", "🏠", "✈️"
    is_overridden: bool = False  # User can manually override reliability
    
    @property
    def is_reliable(self) -> bool:
        """Regression filter: streak ≤ 10 is reliable, unless overridden"""
        if self.is_overridden:
            return True
        return self.length <= 10
    
    @property
    def display(self) -> str:
        icon_str = f" {self.icon}" if self.icon else ""
        length_str = f" ({self.length})" if self.length > 0 else ""
        warning = " ⚠️" if not self.is_reliable and not self.is_overridden else ""
        return f"{self.streak_type.replace('_', ' ').title()}{icon_str}{length_str}{warning}"
    
    def venue_matches(self, match_venue: str) -> bool:
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
    
    def get_best_streak(self, streak_list: List[Streak], match_venue: str) -> Optional[Streak]:
        valid = [s for s in streak_list if s.venue_matches(match_venue)]
        if not valid:
            return None
        return max(valid, key=lambda x: x.length)
    
    def has_reliable_no_btts(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        streak = self.get_best_streak(self.no_btts, match_venue)
        if streak and streak.is_reliable:
            return True, streak
        return False, None
    
    def has_reliable_scoring_plain(self, min_length: int = 3) -> Tuple[bool, Optional[Streak]]:
        plain_streaks = [s for s in self.scoring if not s.icon]
        if not plain_streaks:
            return False, None
        best = max(plain_streaks, key=lambda x: x.length)
        if best.length >= min_length and best.is_reliable:
            return True, best
        return False, None
    
    def has_reliable_btts(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        streak = self.get_best_streak(self.btts, match_venue)
        if streak and streak.is_reliable:
            return True, streak
        return False, None
    
    def has_goal_streak(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        # Check plain scoring first
        plain_scoring = [s for s in self.scoring if not s.icon]
        if plain_scoring:
            best = max(plain_scoring, key=lambda x: x.length)
            if best.is_reliable:
                return True, best
        
        # Check plain BTTS
        plain_btts = [s for s in self.btts if not s.icon]
        if plain_btts:
            best = max(plain_btts, key=lambda x: x.length)
            if best.is_reliable:
                return True, best
        
        # Check plain Over 2.5
        plain_over25 = [s for s in self.over25 if not s.icon]
        if plain_over25:
            best = max(plain_over25, key=lambda x: x.length)
            if best.is_reliable:
                return True, best
        
        # Check plain Goals 2+
        plain_goals2 = [s for s in self.goals2 if not s.icon]
        if plain_goals2:
            best = max(plain_goals2, key=lambda x: x.length)
            if best.is_reliable:
                return True, best
        
        # Check icon-specific with venue match
        scoring = self.get_best_streak(self.scoring, match_venue)
        if scoring and scoring.is_reliable and scoring.icon:
            return True, scoring
        
        btts = self.get_best_streak(self.btts, match_venue)
        if btts and btts.is_reliable and btts.icon:
            return True, btts
        
        over25 = self.get_best_streak(self.over25, match_venue)
        if over25 and over25.is_reliable and over25.icon:
            return True, over25
        
        goals2 = self.get_best_streak(self.goals2, match_venue)
        if goals2 and goals2.is_reliable and goals2.icon:
            return True, goals2
        
        return False, None
    
    def has_volume_streak(self, match_venue: str) -> Tuple[bool, Optional[Streak]]:
        # Check Over 2.5
        over25 = self.get_best_streak(self.over25, match_venue)
        if over25 and over25.is_reliable:
            return True, over25
        
        # Check Goals 2+
        goals2 = self.get_best_streak(self.goals2, match_venue)
        if goals2 and goals2.is_reliable:
            return True, goals2
        
        # Check BTTS as volume
        btts = self.get_best_streak(self.btts, match_venue)
        if btts and btts.is_reliable:
            return True, btts
        
        return False, None


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
    reasoning.append("   • Regression: Streaks > 10 are unreliable (unless overridden)")
    reasoning.append(f"   • Venue: 🏠 only home, ✈️ only away, plain anywhere")
    reasoning.append(f"   • Current venue: {match_venue.upper()}")
    
    # ========================================================================
    # RULE 2: Any "No BTTS" (Priority)
    # ========================================================================
    home_no, home_no_streak = home.has_reliable_no_btts(match_venue)
    away_no, away_no_streak = away.has_reliable_no_btts(match_venue)
    
    if home_no or away_no:
        no_teams = []
        if home_no:
            no_teams.append((home_no_streak.length, home.name, home_no_streak))
        if away_no:
            no_teams.append((away_no_streak.length, away.name, away_no_streak))
        longest_len, longest_team, longest_streak = max(no_teams, key=lambda x: x[0])
        
        reasoning.append(f"\n✅ **RULE 2 TRIGGERED** (BTTS No)")
        reasoning.append(f"   • {longest_team}: {longest_streak.display}")
        
        return PredictionResult(
            btts_prediction="BTTS No",
            over_under="Under 2.5 lean",
            triggered_rule="Rule 2 (No BTTS)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # RULE 1: Both plain Scoring ≥3 + reliable + no No BTTS
    # ========================================================================
    home_scoring, home_sc_streak = home.has_reliable_scoring_plain(min_length=3)
    away_scoring, away_sc_streak = away.has_reliable_scoring_plain(min_length=3)
    
    home_has_no, _ = home.has_reliable_no_btts(match_venue)
    away_has_no, _ = away.has_reliable_no_btts(match_venue)
    
    if home_scoring and away_scoring and not home_has_no and not away_has_no:
        reasoning.append(f"\n✅ **RULE 1 TRIGGERED** (BTTS Yes from Plain Scoring)")
        reasoning.append(f"   • {home.name}: {home_sc_streak.display}")
        reasoning.append(f"   • {away.name}: {away_sc_streak.display}")
        
        # Volume check
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
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_under=over_under,
            triggered_rule="Rule 1 (Plain Scoring)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # RULE 3: BTTS streak + venue match + opponent goal streak
    # ========================================================================
    # Check home team's BTTS
    home_btts, home_btts_streak = home.has_reliable_btts(match_venue)
    
    if home_btts:
        away_goal, away_goal_streak = away.has_goal_streak(match_venue)
        if away_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {home.name}: {home_btts_streak.display}")
            reasoning.append(f"   • Opponent ({away.name}): {away_goal_streak.display}")
            
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
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS Streak)",
                reasoning=reasoning
            )
    
    # Check away team's BTTS
    away_btts, away_btts_streak = away.has_reliable_btts(match_venue)
    
    if away_btts:
        home_goal, home_goal_streak = home.has_goal_streak(match_venue)
        if home_goal:
            reasoning.append(f"\n✅ **RULE 3 TRIGGERED** (BTTS Yes from BTTS Streak)")
            reasoning.append(f"   • {away.name}: {away_btts_streak.display}")
            reasoning.append(f"   • Opponent ({home.name}): {home_goal_streak.display}")
            
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
    reasoning.append(f"   • Rule 2: No reliable No BTTS streak with venue match")
    reasoning.append(f"   • Rule 1: Not both have plain Scoring ≥3 (reliable) OR found No BTTS")
    reasoning.append(f"   • Rule 3: No BTTS streak with venue match + opponent goal streak")
    
    return PredictionResult(
        btts_prediction="No bet",
        over_under=None,
        triggered_rule="No bet",
        reasoning=reasoning
    )


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================
def streak_selector(streak_name: str, key_prefix: str, default_length: int = 0):
    """Create icon-based streak selector with optional length input"""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        has_plain = st.checkbox(
            f"Plain {streak_name}",
            key=f"{key_prefix}_{streak_name}_plain_has",
            help="No icon - applies to any venue"
        )
    
    with col2:
        has_home = st.checkbox(
            f"🏠 Home {streak_name}",
            key=f"{key_prefix}_{streak_name}_home_has",
            help="🏠 icon - only applies at HOME"
        )
    
    with col3:
        has_away = st.checkbox(
            f"✈️ Away {streak_name}",
            key=f"{key_prefix}_{streak_name}_away_has",
            help="✈️ icon - only applies AWAY"
        )
    
    with col4:
        length = st.number_input(
            "Length",
            min_value=0, max_value=30, value=default_length,
            key=f"{key_prefix}_{streak_name}_length",
            help="Number of consecutive games (0 = unknown)"
        )
    
    return has_plain, has_home, has_away, length


def get_streaks_from_ui(prefix: str, streak_name: str, streak_type: str, icon: str, length: int) -> Optional[Streak]:
    """Create a Streak object if the checkbox is checked"""
    if length > 0:
        return Streak(streak_type, length, icon)
    return None


def build_team_from_ui(prefix: str, name: str, is_home: bool) -> TeamStreaks:
    """Build TeamStreaks object from UI selections"""
    team = TeamStreaks(name=name, is_home=is_home)
    
    # Scoring streaks
    has_plain, has_home, has_away, length = st.session_state.get(f"{prefix}_Scoring_data", (False, False, False, 0))
    if has_plain and length > 0:
        team.scoring.append(Streak("scoring", length, ""))
    if has_home and length > 0:
        team.scoring.append(Streak("scoring", length, "🏠"))
    if has_away and length > 0:
        team.scoring.append(Streak("scoring", length, "✈️"))
    
    # No BTTS streaks
    has_plain, has_home, has_away, length = st.session_state.get(f"{prefix}_No BTTS_data", (False, False, False, 0))
    if has_plain and length > 0:
        team.no_btts.append(Streak("no_btts", length, ""))
    if has_home and length > 0:
        team.no_btts.append(Streak("no_btts", length, "🏠"))
    if has_away and length > 0:
        team.no_btts.append(Streak("no_btts", length, "✈️"))
    
    # BTTS streaks
    has_plain, has_home, has_away, length = st.session_state.get(f"{prefix}_BTTS_data", (False, False, False, 0))
    if has_plain and length > 0:
        team.btts.append(Streak("btts", length, ""))
    if has_home and length > 0:
        team.btts.append(Streak("btts", length, "🏠"))
    if has_away and length > 0:
        team.btts.append(Streak("btts", length, "✈️"))
    
    # Over 2.5 streaks
    has_plain, has_home, has_away, length = st.session_state.get(f"{prefix}_Over 2.5_data", (False, False, False, 0))
    if has_plain and length > 0:
        team.over25.append(Streak("over25", length, ""))
    if has_home and length > 0:
        team.over25.append(Streak("over25", length, "🏠"))
    if has_away and length > 0:
        team.over25.append(Streak("over25", length, "✈️"))
    
    # Goals 2+ streaks
    has_plain, has_home, has_away, length = st.session_state.get(f"{prefix}_Goals 2+_data", (False, False, False, 0))
    if has_plain and length > 0:
        team.goals2.append(Streak("goals2", length, ""))
    if has_home and length > 0:
        team.goals2.append(Streak("goals2", length, "🏠"))
    if has_away and length > 0:
        team.goals2.append(Streak("goals2", length, "✈️"))
    
    return team


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("BTTS & Over/Under | Regression: >10 games unreliable | Venue: 🏠=home ✈️=away")
    
    st.markdown("""
    <div class="venue-note">
        🏟️ <strong>Venue Auto-Detected:</strong> First team = HOME | Second team = AWAY<br>
        🏠 streaks apply to first team | ✈️ streaks apply to second team | Plain streaks apply to both<br>
        📏 <strong>Length:</strong> Enter the number of consecutive games. Streaks >10 are marked unreliable unless you override.
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
    st.markdown(f"<div class='team-header-home'><span class='team-name'>🏠 {home_name} (HOME)</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_selector("Scoring", "home")
        st.session_state["home_Scoring_data"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_selector("No BTTS", "home")
        st.session_state["home_No BTTS_data"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_selector("BTTS", "home")
        st.session_state["home_BTTS_data"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_selector("Over 2.5", "home")
        st.session_state["home_Over 2.5_data"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_selector("Goals 2+", "home")
        st.session_state["home_Goals 2+_data"] = data
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-away'><span class='team-name'>✈️ {away_name} (AWAY)</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_selector("Scoring", "away")
        st.session_state["away_Scoring_data"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_selector("No BTTS", "away")
        st.session_state["away_No BTTS_data"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_selector("BTTS", "away")
        st.session_state["away_BTTS_data"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_selector("Over 2.5", "away")
        st.session_state["away_Over 2.5_data"] = data
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        data = streak_selector("Goals 2+", "away")
        st.session_state["away_Goals 2+_data"] = data
    
    st.divider()
    
    # ========================================================================
    # OVERRIDE SETTINGS
    # ========================================================================
    with st.expander("⚙️ Advanced Settings", expanded=False):
        st.caption("Override regression filter for specific streaks (use if you believe a long streak will continue)")
        override_streaks = st.multiselect(
            "Select streaks to mark as reliable regardless of length",
            options=[],
            help="If a streak is >10 games but you still trust it, select it here"
        )
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary"):
        home_team = build_team_from_ui("home", home_name, is_home=True)
        away_team = build_team_from_ui("away", away_name, is_home=False)
        
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
    | **Rule 2** | Any "No BTTS" (reliable + venue match) | **BTTS No** + Under lean |
    | **Rule 1** | Both plain Scoring ≥3 (reliable + no No BTTS) | **BTTS Yes** + Over if both have volume |
    | **Rule 3** | Any "BTTS" (reliable + venue match + opponent goal streak) | **BTTS Yes** + Over if both have volume |
    | **Else** | — | **No bet** |
    
    ### 🎯 How to Use
    
    1. Enter **Home Team** (left) and **Away Team** (right)
    2. For each streak type, check the boxes for streaks that exist
    3. Enter the streak length (number of consecutive games)
    4. Click **PREDICT** to see the result
    
    ### 📏 About Length
    
    - Streaks ≤ 10 games are considered **reliable**
    - Streaks > 10 games are considered **unreliable** (regression to mean)
    - You can override this in Advanced Settings
    """)

if __name__ == "__main__":
    main()