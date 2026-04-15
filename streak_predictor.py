"""
Streak Predictor - BTTS & Over/Under Betting System
Based on 3-rule logic with regression check (streak ≤ 10)
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
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
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* Card styles */
    .card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    .team-card {
        background: #0f172a;
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    /* Prediction card */
    .prediction-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
        border: 1px solid #334155;
    }
    
    .prediction-btts {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 2px;
    }
    
    .prediction-over {
        font-size: 1.5rem;
        font-weight: 600;
        color: #fbbf24;
    }
    
    .prediction-nobet {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ef4444;
    }
    
    /* Streak badges */
    .streak-badge {
        display: inline-block;
        background: #1e293b;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        margin: 0.2rem 0.3rem;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .streak-reliable {
        border-left: 3px solid #10b981;
    }
    
    .streak-unreliable {
        border-left: 3px solid #ef4444;
        opacity: 0.7;
    }
    
    /* Rule trigger highlight */
    .rule-trigger {
        background: #1e3a2f;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #10b981;
        font-size: 0.85rem;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    /* Divider */
    hr {
        margin: 1.5rem 0;
        border-color: #334155;
    }
    
    /* Input labels */
    .stNumberInput label, .stTextInput label {
        font-weight: 600;
        color: #cbd5e1;
    }
    
    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        font-weight: 700;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        border: none;
        transition: transform 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA MODELS
# ============================================================================
@dataclass
class Streaks:
    """Container for all streak types for a team"""
    # Plain streaks
    scoring_plain: int = 0           # Plain "Scoring"
    no_btts_plain: int = 0           # Plain "No BTTS"
    btts_plain: int = 0              # Plain "BTTS"
    over_25_plain: int = 0           # Plain "Over 2.5 Goals"
    goals2_plain: int = 0            # Plain "Goals 2+"
    
    # Home streaks (🏠)
    scoring_home: int = 0
    no_btts_home: int = 0
    btts_home: int = 0
    over_25_home: int = 0
    goals2_home: int = 0
    
    # Away streaks (✈️)
    scoring_away: int = 0
    no_btts_away: int = 0
    btts_away: int = 0
    over_25_away: int = 0
    goals2_away: int = 0
    
    def get_max_streak(self, streak_type: str) -> Tuple[int, str]:
        """Get max length and location (plain/home/away) for a streak type"""
        locations = {
            'scoring': [
                (self.scoring_plain, 'plain'),
                (self.scoring_home, '🏠 home'),
                (self.scoring_away, '✈️ away')
            ],
            'no_btts': [
                (self.no_btts_plain, 'plain'),
                (self.no_btts_home, '🏠 home'),
                (self.no_btts_away, '✈️ away')
            ],
            'btts': [
                (self.btts_plain, 'plain'),
                (self.btts_home, '🏠 home'),
                (self.btts_away, '✈️ away')
            ],
            'over_25': [
                (self.over_25_plain, 'plain'),
                (self.over_25_home, '🏠 home'),
                (self.over_25_away, '✈️ away')
            ],
            'goals2': [
                (self.goals2_plain, 'plain'),
                (self.goals2_home, '🏠 home'),
                (self.goals2_away, '✈️ away')
            ]
        }
        
        items = locations.get(streak_type, [])
        if not items:
            return 0, ''
        
        max_len, max_loc = max(items, key=lambda x: x[0])
        return max_len, max_loc if max_len > 0 else ''
    
    def has_reliable_no_btts(self) -> Tuple[bool, int, str]:
        """Check if team has reliable No BTTS streak (≤10)"""
        for loc in ['plain', 'home', 'away']:
            length = getattr(self, f'no_btts_{loc}', 0)
            if length > 0 and length <= 10:
                return True, length, loc
        return False, 0, ''
    
    def has_reliable_btts(self, venue: str = None) -> Tuple[bool, int, str]:
        """
        Check if team has reliable BTTS streak (≤10)
        venue: 'home', 'away', or None for any
        """
        locs = ['plain', 'home', 'away'] if not venue else [venue]
        for loc in locs:
            length = getattr(self, f'btts_{loc}', 0)
            if length > 0 and length <= 10:
                return True, length, loc
        return False, 0, ''
    
    def has_reliable_scoring(self, min_length: int = 3) -> Tuple[bool, int, str]:
        """Check if team has reliable Scoring streak (≤10 and ≥ min_length)"""
        for loc in ['plain', 'home', 'away']:
            length = getattr(self, f'scoring_{loc}', 0)
            if length >= min_length and length <= 10:
                return True, length, loc
        return False, 0, ''
    
    def has_volume_streak(self, venue: str = None) -> Tuple[bool, int, str, str]:
        """
        Check for volume streaks (Over 2.5 or Goals 2+)
        Returns: (has_streak, length, location, type)
        """
        types = ['over_25', 'goals2']
        locs = ['plain', 'home', 'away'] if not venue else [venue]
        
        for streak_type in types:
            for loc in locs:
                length = getattr(self, f'{streak_type}_{loc}', 0)
                if length > 0 and length <= 10:
                    return True, length, loc, streak_type
        return False, 0, '', ''
    
    def has_goal_streak(self) -> bool:
        """Check if team has ANY goal-related streak (Scoring, BTTS, volume)"""
        # Check scoring
        if self.scoring_plain > 0 or self.scoring_home > 0 or self.scoring_away > 0:
            return True
        # Check BTTS
        if self.btts_plain > 0 or self.btts_home > 0 or self.btts_away > 0:
            return True
        # Check volume
        if self.over_25_plain > 0 or self.over_25_home > 0 or self.over_25_away > 0:
            return True
        if self.goals2_plain > 0 or self.goals2_home > 0 or self.goals2_away > 0:
            return True
        return False


@dataclass
class TeamData:
    name: str
    streaks: Streaks
    is_home: bool = True
    
    @property
    def venue(self) -> str:
        return 'home' if self.is_home else 'away'


@dataclass
class PredictionResult:
    btts_prediction: str  # "BTTS Yes", "BTTS No", or "No bet"
    over_under: Optional[str]  # "Over 2.5", "Under 2.5 lean", or None
    triggered_rule: str  # "Rule 2 (No BTTS)", "Rule 1 (Scoring)", "Rule 3 (BTTS)", "No bet"
    reasoning: List[str]
    home_score: Optional[int] = None
    away_score: Optional[int] = None


# ============================================================================
# PREDICTION LOGIC
# ============================================================================
def predict_match(home: TeamData, away: TeamData) -> PredictionResult:
    """
    Main prediction function implementing the 3-rule system
    """
    reasoning = []
    
    # ========================================================================
    # STEP 1: Rule 2 - Check No BTTS streaks
    # ========================================================================
    home_has_no_btts, home_no_len, home_no_loc = home.streaks.has_reliable_no_btts()
    away_has_no_btts, away_no_len, away_no_loc = away.streaks.has_reliable_no_btts()
    
    if home_has_no_btts or away_has_no_btts:
        # Find the longest reliable No BTTS streak
        no_btts_teams = []
        if home_has_no_btts:
            no_btts_teams.append((home_no_len, home.name, home_no_loc))
        if away_has_no_btts:
            no_btts_teams.append((away_no_len, away.name, away_no_loc))
        
        longest_len, longest_team, longest_loc = max(no_btts_teams, key=lambda x: x[0])
        reasoning.append(f"✅ Rule 2 triggered: {longest_team} has No BTTS streak of {longest_len} ({longest_loc})")
        reasoning.append(f"📊 Regression check passed: {longest_len} ≤ 10")
        
        return PredictionResult(
            btts_prediction="BTTS No",
            over_under="Under 2.5 lean",
            triggered_rule="Rule 2 (No BTTS)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # STEP 2: Rule 1 - Check both plain Scoring ≥ 3
    # ========================================================================
    home_has_scoring, home_sc_len, home_sc_loc = home.streaks.has_reliable_scoring(min_length=3)
    away_has_scoring, away_sc_len, away_sc_loc = away.streaks.has_reliable_scoring(min_length=3)
    
    # Also need to ensure no No BTTS streaks (already checked above, but double-check)
    if home_has_scoring and away_has_scoring:
        reasoning.append(f"✅ Rule 1 condition met:")
        reasoning.append(f"   • {home.name}: Scoring {home_sc_len} ({home_sc_loc}) - reliable ✓")
        reasoning.append(f"   • {away.name}: Scoring {away_sc_len} ({away_sc_loc}) - reliable ✓")
        reasoning.append(f"   • No reliable No BTTS streaks ✓")
        
        # Check volume streaks for Over 2.5
        home_vol, home_vol_len, home_vol_loc, home_vol_type = home.streaks.has_volume_streak()
        away_vol, away_vol_len, away_vol_loc, away_vol_type = away.streaks.has_volume_streak()
        
        over_under = None
        if home_vol and away_vol:
            reasoning.append(f"📊 Volume check: Both teams have reliable volume streaks")
            reasoning.append(f"   • {home.name}: {home_vol_type.replace('_', ' ').title()} {home_vol_len} ({home_vol_loc})")
            reasoning.append(f"   • {away.name}: {away_vol_type.replace('_', ' ').title()} {away_vol_len} ({away_vol_loc})")
            over_under = "Over 2.5"
        else:
            reasoning.append(f"📊 Volume check: Not both teams have volume streaks → No Over bet")
        
        return PredictionResult(
            btts_prediction="BTTS Yes",
            over_under=over_under,
            triggered_rule="Rule 1 (Scoring streaks)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # STEP 3: Rule 3 - Check BTTS streaks with venue matching
    # ========================================================================
    # Check home team's home BTTS streaks
    home_btts_at_home, home_btts_len, home_btts_loc = home.streaks.has_reliable_btts(venue='home')
    # Check away team's away BTTS streaks
    away_btts_away, away_btts_len, away_btts_loc = away.streaks.has_reliable_btts(venue='away')
    # Also check plain BTTS for either (plain works anywhere)
    home_btts_plain, home_btts_plain_len, _ = home.streaks.has_reliable_btts(venue='plain')
    away_btts_plain, away_btts_plain_len, _ = away.streaks.has_reliable_btts(venue='plain')
    
    # Check each team's BTTS streaks with venue matching
    home_has_valid_btts = home_btts_at_home or home_btts_plain
    away_has_valid_btts = away_btts_away or away_btts_plain
    
    # Determine which team triggers the rule
    trigger_team = None
    trigger_len = 0
    trigger_loc = ""
    
    if home_has_valid_btts:
        # Get the best streak for home
        best_len = 0
        best_loc = ""
        if home_btts_at_home and home_btts_len > best_len:
            best_len = home_btts_len
            best_loc = f"🏠 home ({home_btts_len})"
        if home_btts_plain and home_btts_plain_len > best_len:
            best_len = home_btts_plain_len
            best_loc = f"plain ({home_btts_plain_len})"
        trigger_team = home
        trigger_len = best_len
        trigger_loc = best_loc
    
    if away_has_valid_btts:
        best_len = 0
        best_loc = ""
        if away_btts_away and away_btts_len > best_len:
            best_len = away_btts_len
            best_loc = f"✈️ away ({away_btts_len})"
        if away_btts_plain and away_btts_plain_len > best_len:
            best_len = away_btts_plain_len
            best_loc = f"plain ({away_btts_plain_len})"
        # If away has longer streak than home (or home didn't trigger)
        if trigger_team is None or best_len > trigger_len:
            trigger_team = away
            trigger_len = best_len
            trigger_loc = best_loc
    
    if trigger_team is not None:
        opponent = away if trigger_team == home else home
        
        # Check if opponent has ANY goal streak
        if opponent.streaks.has_goal_streak():
            reasoning.append(f"✅ Rule 3 triggered: {trigger_team.name} has BTTS streak of {trigger_len} ({trigger_loc})")
            reasoning.append(f"   • Venue matches: {trigger_team.name} is {'home' if trigger_team.is_home else 'away'} ✓")
            reasoning.append(f"   • Opponent ({opponent.name}) has goal streak(s) ✓")
            
            # Check volume streaks for Over 2.5
            home_vol, home_vol_len, home_vol_loc, home_vol_type = home.streaks.has_volume_streak()
            away_vol, away_vol_len, away_vol_loc, away_vol_type = away.streaks.has_volume_streak()
            
            over_under = None
            if home_vol and away_vol:
                reasoning.append(f"📊 Volume check: Both teams have reliable volume streaks")
                reasoning.append(f"   • {home.name}: {home_vol_type.replace('_', ' ').title()} {home_vol_len} ({home_vol_loc})")
                reasoning.append(f"   • {away.name}: {away_vol_type.replace('_', ' ').title()} {away_vol_len} ({away_vol_loc})")
                over_under = "Over 2.5"
            else:
                reasoning.append(f"📊 Volume check: Not both teams have volume streaks → No Over bet")
            
            return PredictionResult(
                btts_prediction="BTTS Yes",
                over_under=over_under,
                triggered_rule="Rule 3 (BTTS streaks)",
                reasoning=reasoning
            )
        else:
            reasoning.append(f"⚠️ Rule 3 candidate: {trigger_team.name} has BTTS streak but opponent lacks goal streak → Not triggered")
    
    # ========================================================================
    # STEP 4: No bet
    # ========================================================================
    reasoning.append("❌ No rule triggered → No bet")
    return PredictionResult(
        btts_prediction="No bet",
        over_under=None,
        triggered_rule="No bet",
        reasoning=reasoning
    )


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================
def streak_input_row(label: str, key_prefix: str, col1, col2, col3):
    """Create 3-column input row for plain/home/away streaks"""
    with col1:
        return st.number_input(
            f"{label} (plain)",
            min_value=0, max_value=30, value=0, key=f"{key_prefix}_plain"
        )
    with col2:
        return st.number_input(
            f"{label} (🏠 home)",
            min_value=0, max_value=30, value=0, key=f"{key_prefix}_home"
        )
    with col3:
        return st.number_input(
            f"{label} (✈️ away)",
            min_value=0, max_value=30, value=0, key=f"{key_prefix}_away"
        )


def create_streaks_from_session(prefix: str) -> Streaks:
    """Create Streaks object from session state values"""
    return Streaks(
        scoring_plain=st.session_state.get(f"{prefix}_scoring_plain", 0),
        scoring_home=st.session_state.get(f"{prefix}_scoring_home", 0),
        scoring_away=st.session_state.get(f"{prefix}_scoring_away", 0),
        no_btts_plain=st.session_state.get(f"{prefix}_no_btts_plain", 0),
        no_btts_home=st.session_state.get(f"{prefix}_no_btts_home", 0),
        no_btts_away=st.session_state.get(f"{prefix}_no_btts_away", 0),
        btts_plain=st.session_state.get(f"{prefix}_btts_plain", 0),
        btts_home=st.session_state.get(f"{prefix}_btts_home", 0),
        btts_away=st.session_state.get(f"{prefix}_btts_away", 0),
        over_25_plain=st.session_state.get(f"{prefix}_over25_plain", 0),
        over_25_home=st.session_state.get(f"{prefix}_over25_home", 0),
        over_25_away=st.session_state.get(f"{prefix}_over25_away", 0),
        goals2_plain=st.session_state.get(f"{prefix}_goals2_plain", 0),
        goals2_home=st.session_state.get(f"{prefix}_goals2_home", 0),
        goals2_away=st.session_state.get(f"{prefix}_goals2_away", 0),
    )


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("BTTS & Over/Under Betting System | Regression Check: Streak ≤ 10")
    
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
        c1, c2, c3 = st.columns(3)
        streak_input_row("Scoring", f"home_scoring", c1, c2, c3)
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("No BTTS", f"home_no_btts", c1, c2, c3)
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("BTTS", f"home_btts", c1, c2, c3)
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("Over 2.5", f"home_over25", c1, c2, c3)
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("Goals 2+", f"home_goals2", c1, c2, c3)
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"### ✈️ {away_name}")
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        c1, c2, c3 = st.columns(3)
        streak_input_row("Scoring", f"away_scoring", c1, c2, c3)
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("No BTTS", f"away_no_btts", c1, c2, c3)
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("BTTS", f"away_btts", c1, c2, c3)
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("Over 2.5", f"away_over25", c1, c2, c3)
    
    with st.expander("🎯 Goals 2+ Streaks", expanded=False):
        c1, c2, c3 = st.columns(3)
        streak_input_row("Goals 2+", f"away_goals2", c1, c2, c3)
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON & OUTPUT
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary", use_container_width=True):
        # Create streaks from session state
        home_streaks = create_streaks_from_session("home")
        away_streaks = create_streaks_from_session("away")
        
        home_team = TeamData(name=home_name, streaks=home_streaks, is_home=True)
        away_team = TeamData(name=away_name, streaks=away_streaks, is_home=False)
        
        result = predict_match(home_team, away_team)
        
        # Display prediction card
        if result.btts_prediction == "BTTS Yes":
            pred_color = "#10b981"
            pred_html = f'<div class="prediction-btts" style="color: {pred_color};">✅ {result.btts_prediction}</div>'
        elif result.btts_prediction == "BTTS No":
            pred_color = "#ef4444"
            pred_html = f'<div class="prediction-btts" style="color: {pred_color};">🚫 {result.btts_prediction}</div>'
        else:
            pred_color = "#f59e0b"
            pred_html = f'<div class="prediction-nobet">⏸️ {result.btts_prediction}</div>'
        
        over_html = ""
        if result.over_under:
            over_html = f'<div class="prediction-over">📊 {result.over_under}</div>'
        
        st.markdown(f"""
        <div class="prediction-card">
            {pred_html}
            {over_html}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b;">
                Triggered: {result.triggered_rule}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show reasoning
        with st.expander("📋 Show Reasoning & Rule Check", expanded=True):
            for line in result.reasoning:
                if line.startswith("✅"):
                    st.success(line)
                elif line.startswith("❌"):
                    st.error(line)
                elif line.startswith("⚠️"):
                    st.warning(line)
                elif line.startswith("📊"):
                    st.info(line)
                else:
                    st.write(line)
            
            # Show regression check reminder
            st.divider()
            st.caption("📐 Regression Check: All streaks > 10 are considered UNRELIABLE and ignored by the system.")
    
    # Footer
    st.divider()
    st.caption("""
    **Rules:**
    1. **Rule 2 (Priority)**: Reliable No BTTS streak → **BTTS No + Under 2.5 lean**
    2. **Rule 1**: Both teams have plain Scoring ≥ 3 (reliable) → **BTTS Yes** + Over 2.5 if both have volume streaks
    3. **Rule 3**: Team has BTTS streak with venue match + opponent has goal streak → **BTTS Yes** + Over 2.5 if both have volume streaks
    4. **Otherwise**: No bet
    
    **Reliable = streak length ≤ 10 games**
    """)


if __name__ == "__main__":
    main()
