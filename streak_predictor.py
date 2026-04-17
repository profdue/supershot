"""
STREAK PREDICTOR - CONTRADICTION-BASED SYSTEM
Core Principle: A prediction is only valid if NO streak contradicts it.

Rules:
1. Check for ANY contradiction → If found → NO BET
2. Apply prediction based on remaining non-contradictory streaks
3. If multiple predictions possible → take highest confidence

This system is designed to be unpenetratable because it only bets when ALL signals agree.
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

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
        font-size: 2rem;
        font-weight: 800;
        color: #10b981;
    }
    .prediction-btts-no {
        font-size: 2rem;
        font-weight: 800;
        color: #ef4444;
    }
    .prediction-under25 {
        font-size: 1.3rem;
        font-weight: 600;
        color: #8b5cf6;
        margin-top: 0.5rem;
    }
    .prediction-home-win {
        font-size: 1.3rem;
        font-weight: 600;
        color: #3b82f6;
        margin-top: 0.5rem;
    }
    .prediction-away-draw {
        font-size: 1.3rem;
        font-weight: 600;
        color: #f59e0b;
        margin-top: 0.5rem;
    }
    .prediction-away-win {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ef4444;
        margin-top: 0.5rem;
    }
    .prediction-uncertain {
        font-size: 1rem;
        font-weight: 500;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    .prediction-skip {
        font-size: 2rem;
        font-weight: 700;
        color: #f59e0b;
    }
    .score-prediction {
        font-size: 1.1rem;
        font-weight: 500;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    .contradiction-warning {
        background: #1e293b;
        border-left: 3px solid #ef4444;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #ef4444;
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
    btts: List[Streak] = field(default_factory=list)
    over05: List[Streak] = field(default_factory=list)
    over25: List[Streak] = field(default_factory=list)
    unbeaten: List[Streak] = field(default_factory=list)
    without_win: List[Streak] = field(default_factory=list)
    no_btts: List[Streak] = field(default_factory=list)
    
    @property
    def venue(self) -> str:
        return "home" if self.is_home else "away"
    
    def has_streak_matching_venue(self, streak_list: List[Streak], icon_filter: str = None) -> bool:
        for s in streak_list:
            if s.venue_matches(self.venue):
                if icon_filter is None or s.icon == icon_filter:
                    return True
        return False
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    def has_btts_away(self) -> bool:
        if self.is_home:
            return False
        return self.has_streak_matching_venue(self.btts, "✈️")
    
    def has_without_win_away(self) -> bool:
        if self.is_home:
            return False
        return self.has_streak_matching_venue(self.without_win, "✈️")
    
    def has_unbeaten_away(self) -> bool:
        if self.is_home:
            return False
        return self.has_streak_matching_venue(self.unbeaten, "✈️")
    
    def has_over05_away(self) -> bool:
        if self.is_home:
            return False
        return self.has_streak_matching_venue(self.over05, "✈️")
    
    def has_no_btts_away(self) -> bool:
        if self.is_home:
            return False
        return self.has_streak_matching_venue(self.no_btts, "✈️")
    
    # ========================================================================
    # HOME TEAM STREAKS
    # ========================================================================
    def has_any_scoring(self) -> bool:
        return self.has_streak_matching_venue(self.scoring)
    
    def has_scoring_home(self) -> bool:
        if not self.is_home:
            return False
        return self.has_streak_matching_venue(self.scoring, "🏠")
    
    def has_over05_home(self) -> bool:
        if not self.is_home:
            return False
        return self.has_streak_matching_venue(self.over05, "🏠")
    
    def has_no_btts_home(self) -> bool:
        if not self.is_home:
            return False
        return self.has_streak_matching_venue(self.no_btts, "🏠")


@dataclass
class PredictionResult:
    btts: Optional[str]
    over_under: Optional[str]
    winner: Optional[str]
    score: Optional[str]
    pattern: str
    reasoning: List[str]
    contradictions: List[str]


# ============================================================================
# CONTRADICTION-BASED PREDICTION LOGIC
# ============================================================================
def predict_match(home: TeamStreaks, away: TeamStreaks) -> PredictionResult:
    reasoning = []
    contradictions = []
    
    reasoning.append("📊 **Contradiction-Based Analysis:**")
    reasoning.append(f"   • {home.name}: Playing at HOME")
    reasoning.append(f"   • {away.name}: Playing AWAY")
    reasoning.append(f"   • System only bets when NO contradiction exists")
    
    # ========================================================================
    # STEP 1: Identify All Signals
    # ========================================================================
    
    # Signals that suggest BTTS YES
    btts_yes_signals = []
    
    # Signal 1: Away has BTTS ✈️
    if away.has_btts_away():
        btts_yes_signals.append(f"{away.name} has BTTS ✈️")
    
    # Signal 2: Both teams have scoring streaks
    if home.has_any_scoring() and away.has_any_scoring():
        btts_yes_signals.append(f"Both teams have scoring streaks")
    
    # Signal 3: Away has Over 0.5 ✈️ + Unbeaten ✈️
    if away.has_over05_away() and away.has_unbeaten_away():
        btts_yes_signals.append(f"{away.name} has Over 0.5 ✈️ + Unbeaten ✈️")
    
    # Signals that suggest BTTS NO
    btts_no_signals = []
    
    # Signal 1: Any team has No BTTS matching venue
    if home.has_no_btts_home():
        btts_no_signals.append(f"{home.name} has No BTTS 🏠")
    if away.has_no_btts_away():
        btts_no_signals.append(f"{away.name} has No BTTS ✈️")
    
    # Signal 2: Away has Without Win ✈️
    if away.has_without_win_away():
        btts_no_signals.append(f"{away.name} has Without Win ✈️")
    
    # Signal 3: Away has Unbeaten ✈️ only (no Over 0.5 ✈️) AND home has no scoring
    if away.has_unbeaten_away() and not away.has_over05_away() and not home.has_any_scoring():
        btts_no_signals.append(f"{away.name} has Unbeaten ✈️ only (home no scoring)")
    
    # Signal 4: Away has Over 0.5 ✈️ only (no other streaks)
    if away.has_over05_away() and not away.has_unbeaten_away() and not away.has_without_win_away() and not away.has_btts_away():
        btts_no_signals.append(f"{away.name} has Over 0.5 ✈️ only")
    
    # Signals for Winner
    home_win_signals = []
    away_win_signals = []
    draw_signals = []
    
    # Home win signals
    if away.has_without_win_away():
        home_win_signals.append(f"{away.name} has Without Win ✈️ → cannot win")
    
    # Away win signals
    if away.has_unbeaten_away() and not away.has_over05_away() and not home.has_any_scoring():
        away_win_signals.append(f"{away.name} has Unbeaten ✈️ only + home no scoring")
    
    # Away/Draw signals
    if away.has_unbeaten_away() and away.has_over05_away():
        draw_signals.append(f"{away.name} has Unbeaten ✈️ + Over 0.5 ✈️ → avoids defeat")
    
    if away.has_btts_away():
        draw_signals.append(f"{away.name} has BTTS ✈️ → winner uncertain")
    
    # Signals for Over/Under
    under_signals = []
    
    # Under signals
    if away.has_over05_away() and not away.has_unbeaten_away() and not away.has_without_win_away() and not away.has_btts_away():
        under_signals.append(f"{away.name} has Over 0.5 ✈️ only → Under 2.5 likely")
    
    if away.has_without_win_away():
        under_signals.append(f"{away.name} has Without Win ✈️ → Under 2.5 likely")
    
    # ========================================================================
    # STEP 2: Check for Contradictions
    # ========================================================================
    
    # Contradiction 1: Both BTTS YES and BTTS NO signals present
    if btts_yes_signals and btts_no_signals:
        contradictions.append(f"CONTRADICTION: BTTS YES signals ({', '.join(btts_yes_signals)}) vs BTTS NO signals ({', '.join(btts_no_signals)})")
    
    # Contradiction 2: Without Win ✈️ (away cannot win) vs Unbeaten ✈️ (away cannot lose)
    if away.has_without_win_away() and away.has_unbeaten_away():
        contradictions.append(f"CONTRADICTION: {away.name} has both Without Win ✈️ (cannot win) and Unbeaten ✈️ (cannot lose) → impossible")
    
    # Contradiction 3: Without Win ✈️ vs BTTS ✈️
    if away.has_without_win_away() and away.has_btts_away():
        contradictions.append(f"CONTRADICTION: {away.name} has Without Win ✈️ (BTTS NO) and BTTS ✈️ (BTTS YES)")
    
    # Contradiction 4: Unbeaten ✈️ only (away win) vs home scoring
    if away.has_unbeaten_away() and not away.has_over05_away() and home.has_any_scoring():
        contradictions.append(f"CONTRADICTION: {away.name} has Unbeaten ✈️ only (Away Win) but {home.name} has scoring streak → Home will score")
    
    # ========================================================================
    # STEP 3: If Contradictions Exist → NO BET
    # ========================================================================
    
    if contradictions:
        reasoning.append(f"\n⚠️ **CONTRADICTIONS DETECTED:**")
        for c in contradictions:
            reasoning.append(f"   • {c}")
        reasoning.append(f"\n❌ **NO BET** - Contradictions make prediction unreliable")
        
        return PredictionResult(
            btts=None,
            over_under=None,
            winner=None,
            score=None,
            pattern="NO BET (Contradiction)",
            reasoning=reasoning,
            contradictions=contradictions
        )
    
    # ========================================================================
    # STEP 4: No Contradictions → Make Predictions
    # ========================================================================
    
    reasoning.append(f"\n✅ **No contradictions detected** → Proceeding with predictions")
    
    # BTTS Prediction
    btts_prediction = None
    if btts_yes_signals and not btts_no_signals:
        btts_prediction = "YES"
        reasoning.append(f"\n📊 **BTTS Decision:** YES ({', '.join(btts_yes_signals)})")
    elif btts_no_signals and not btts_yes_signals:
        btts_prediction = "NO"
        reasoning.append(f"\n📊 **BTTS Decision:** NO ({', '.join(btts_no_signals)})")
    else:
        reasoning.append(f"\n📊 **BTTS Decision:** No clear signals → Not predicted")
    
    # Winner Prediction
    winner_prediction = None
    if home_win_signals:
        winner_prediction = f"{home.name} WIN"
        reasoning.append(f"\n🏆 **Winner Decision:** {winner_prediction} ({', '.join(home_win_signals)})")
    elif away_win_signals:
        winner_prediction = f"{away.name} WIN"
        reasoning.append(f"\n🏆 **Winner Decision:** {winner_prediction} ({', '.join(away_win_signals)})")
    elif draw_signals:
        winner_prediction = f"{away.name} or DRAW"
        reasoning.append(f"\n🏆 **Winner Decision:** {winner_prediction} ({', '.join(draw_signals)})")
    else:
        reasoning.append(f"\n🏆 **Winner Decision:** No clear signals → Not predicted")
    
    # Over/Under Prediction
    over_under_prediction = None
    if under_signals:
        over_under_prediction = "Under 2.5"
        reasoning.append(f"\n📈 **Over/Under Decision:** {over_under_prediction} ({', '.join(under_signals)})")
    
    # Score Prediction (only for Pattern A style)
    score_prediction = None
    if away.has_without_win_away():
        if home.has_over05_home():
            score_prediction = "1-0"
            reasoning.append(f"\n🎯 **Score Prediction:** {score_prediction} ({home.name} has Over 0.5 🏠)")
        else:
            score_prediction = "0-0"
            reasoning.append(f"\n🎯 **Score Prediction:** {score_prediction} ({home.name} no Over 0.5 🏠)")
    
    # Determine pattern name
    pattern_name = "Contradiction-Based Prediction"
    if away.has_btts_away():
        pattern_name = "Pattern: BTTS ✈️"
    elif away.has_without_win_away():
        pattern_name = "Pattern: Without Win ✈️"
    elif away.has_unbeaten_away() and away.has_over05_away():
        pattern_name = "Pattern: Unbeaten ✈️ + Over 0.5 ✈️"
    elif away.has_unbeaten_away() and not away.has_over05_away():
        pattern_name = "Pattern: Unbeaten ✈️ only"
    elif away.has_over05_away() and not away.has_unbeaten_away() and not away.has_without_win_away():
        pattern_name = "Pattern: Over 0.5 ✈️ only"
    
    return PredictionResult(
        btts=btts_prediction,
        over_under=over_under_prediction,
        winner=winner_prediction,
        score=score_prediction,
        pattern=pattern_name,
        reasoning=reasoning,
        contradictions=contradictions
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
    
    # BTTS
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_BTTS", (False, False, False))
    if plain:
        team.btts.append(Streak("btts", ""))
    if home_icon:
        team.btts.append(Streak("btts", "🏠"))
    if away_icon:
        team.btts.append(Streak("btts", "✈️"))
    
    # No BTTS
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_No BTTS", (False, False, False))
    if plain:
        team.no_btts.append(Streak("no_btts", ""))
    if home_icon:
        team.no_btts.append(Streak("no_btts", "🏠"))
    if away_icon:
        team.no_btts.append(Streak("no_btts", "✈️"))
    
    # Over 0.5
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Over 0.5", (False, False, False))
    if plain:
        team.over05.append(Streak("over05", ""))
    if home_icon:
        team.over05.append(Streak("over05", "🏠"))
    if away_icon:
        team.over05.append(Streak("over05", "✈️"))
    
    # Over 2.5
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Over 2.5", (False, False, False))
    if plain:
        team.over25.append(Streak("over25", ""))
    if home_icon:
        team.over25.append(Streak("over25", "🏠"))
    if away_icon:
        team.over25.append(Streak("over25", "✈️"))
    
    # Unbeaten
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Unbeaten", (False, False, False))
    if plain:
        team.unbeaten.append(Streak("unbeaten", ""))
    if home_icon:
        team.unbeaten.append(Streak("unbeaten", "🏠"))
    if away_icon:
        team.unbeaten.append(Streak("unbeaten", "✈️"))
    
    # Without Win
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Without Win", (False, False, False))
    if plain:
        team.without_win.append(Streak("without_win", ""))
    if home_icon:
        team.without_win.append(Streak("without_win", "🏠"))
    if away_icon:
        team.without_win.append(Streak("without_win", "✈️"))
    
    return team


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.title("⚽ Streak Predictor")
    st.caption("Contradiction-Based System | Only bets when ALL signals agree")
    
    st.markdown("""
    <div class="venue-note">
        🏟️ <strong>Core Principle:</strong> A prediction is only valid if NO streak contradicts it.<br>
        🏠 Home streaks apply | ✈️ Away streaks apply | Plain streaks apply to both<br>
        ✅ <strong>Simply check the boxes</strong> for streaks that exist. No numbers needed.<br>
        ⚠️ <strong>If contradictions detected → NO BET</strong>
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
    st.markdown(f"<div class='team-header-home'><span class='team-name'>🏠 {home_name} (HOME)</span><br><span style='font-size:0.7rem;'>🏠 streaks apply | ✈️ streaks are IGNORED | Plain streaks apply</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_checkboxes("Scoring", "home")
        st.session_state["home_Scoring"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_checkboxes("BTTS", "home")
        st.session_state["home_BTTS"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_checkboxes("No BTTS", "home")
        st.session_state["home_No BTTS"] = data
    
    with st.expander("📈 Over 0.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 0.5", "home")
        st.session_state["home_Over 0.5"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 2.5", "home")
        st.session_state["home_Over 2.5"] = data
    
    with st.expander("🛡️ Unbeaten Streaks", expanded=False):
        data = streak_checkboxes("Unbeaten", "home")
        st.session_state["home_Unbeaten"] = data
    
    with st.expander("📉 Without Win Streaks", expanded=False):
        data = streak_checkboxes("Without Win", "home")
        st.session_state["home_Without Win"] = data
    
    st.divider()
    
    # ========================================================================
    # AWAY TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-away'><span class='team-name'>✈️ {away_name} (AWAY)</span><br><span style='font-size:0.7rem;'>✈️ streaks apply | 🏠 streaks are IGNORED | Plain streaks apply</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_checkboxes("Scoring", "away")
        st.session_state["away_Scoring"] = data
    
    with st.expander("⚡ BTTS Streaks", expanded=False):
        data = streak_checkboxes("BTTS", "away")
        st.session_state["away_BTTS"] = data
    
    with st.expander("🚫 No BTTS Streaks", expanded=False):
        data = streak_checkboxes("No BTTS", "away")
        st.session_state["away_No BTTS"] = data
    
    with st.expander("📈 Over 0.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 0.5", "away")
        st.session_state["away_Over 0.5"] = data
    
    with st.expander("📈 Over 2.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 2.5", "away")
        st.session_state["away_Over 2.5"] = data
    
    with st.expander("🛡️ Unbeaten Streaks", expanded=False):
        data = streak_checkboxes("Unbeaten", "away")
        st.session_state["away_Unbeaten"] = data
    
    with st.expander("📉 Without Win Streaks", expanded=False):
        data = streak_checkboxes("Without Win", "away")
        st.session_state["away_Without Win"] = data
    
    st.divider()
    
    # ========================================================================
    # PREDICT BUTTON
    # ========================================================================
    if st.button("🔮 PREDICT", type="primary"):
        home_team = build_team_from_checkboxes("home", home_name, is_home=True)
        away_team = build_team_from_checkboxes("away", away_name, is_home=False)
        
        result = predict_match(home_team, away_team)
        
        if result.pattern == "NO BET (Contradiction)":
            pred_html = f'<div class="prediction-skip">⏸️ NO BET - Contradiction detected</div>'
            over_html = ""
            winner_html = ""
            score_html = ""
        elif result.btts is None and result.winner is None:
            pred_html = f'<div class="prediction-skip">⏸️ NO BET - No clear signals</div>'
            over_html = ""
            winner_html = ""
            score_html = ""
        else:
            btts_html = ""
            if result.btts == "YES":
                btts_html = f'<div class="prediction-btts-yes">✅ BTTS YES</div>'
            elif result.btts == "NO":
                btts_html = f'<div class="prediction-btts-no">🚫 BTTS NO</div>'
            
            over_html = ""
            if result.over_under == "Under 2.5":
                over_html = f'<div class="prediction-under25">📉 {result.over_under}</div>'
            
            winner_html = ""
            if result.winner == f"{home_team.name} WIN":
                winner_html = f'<div class="prediction-home-win">🏆 {result.winner}</div>'
            elif result.winner == f"{away_team.name} or DRAW":
                winner_html = f'<div class="prediction-away-draw">🤝 {result.winner}</div>'
            elif result.winner == f"{away_team.name} WIN":
                winner_html = f'<div class="prediction-away-win">🏆 {result.winner}</div>'
            elif result.winner == "Winner uncertain":
                winner_html = f'<div class="prediction-uncertain">❓ {result.winner}</div>'
            
            score_html = ""
            if result.score:
                score_html = f'<div class="score-prediction">🎯 Predicted score: {result.score}</div>'
            
            pred_html = f'{btts_html}{over_html}{winner_html}{score_html}'
        
        st.markdown(f"""
        <div class="prediction-card">
            {pred_html}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b;">
                {result.pattern}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if result.contradictions:
            with st.expander("⚠️ Contradictions Detected", expanded=True):
                for c in result.contradictions:
                    st.error(c)
        
        with st.expander("📋 Detailed Reasoning", expanded=True):
            for line in result.reasoning:
                if "✅" in line:
                    st.success(line)
                elif "❌" in line:
                    st.error(line)
                elif "⚠️" in line:
                    st.warning(line)
                elif "📊" in line or "🏆" in line or "📈" in line or "🎯" in line:
                    st.info(line)
                else:
                    st.write(line)
    
    st.divider()
    st.markdown("""
    ### 📋 Contradiction-Based System Rules
    
    | Signal | Predicts |
    |--------|----------|
    | BTTS ✈️ (away) | BTTS YES |
    | Both teams have scoring | BTTS YES |
    | Over 0.5 ✈️ + Unbeaten ✈️ | BTTS YES + Away/Draw |
    | No BTTS (any) | BTTS NO |
    | Without Win ✈️ | BTTS NO + Home Win |
    | Unbeaten ✈️ only (home no scoring) | BTTS NO + Away Win |
    | Over 0.5 ✈️ only | BTTS NO + Under 2.5 |
    
    ### ⚠️ Contradictions That Trigger NO BET
    
    - BTTS YES and BTTS NO signals both present
    - Without Win ✈️ and Unbeaten ✈️ on same team
    - Without Win ✈️ and BTTS ✈️ on same team
    - Unbeaten ✈️ only (Away Win) but Home has scoring
    
    ### 🎯 How to Use
    
    1. Enter **Home Team** (left) and **Away Team** (right)
    2. For each streak type, **check the boxes** for streaks that exist
    3. Pay attention to icons:
       - 🏠 = home streak (only counts for home team)
       - ✈️ = away streak (only counts for away team)
       - Plain = applies to both
    4. Click **PREDICT**
    
    ### ✅ Core Principle
    
    **A prediction is only valid if NO streak contradicts it.**
    
    If contradictions exist → NO BET. This ensures you only bet when all signals agree.
    """)

if __name__ == "__main__":
    main()
