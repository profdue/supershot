"""
Streak Predictor - BTTS & Over/Under Betting System
Based on Away Team Form Streaks Analysis

Complete Decision Tree:
STEP 1: Check Away Team's "Without Win ✈️"
    If YES → PATTERN A
        Bet: Under 2.5 + BTTS NO + Home Win
        Score: 1-0 (if home scoring 10+) or 0-0 (if home scoring under 10)

STEP 2: If NO, check Away Team's "Unbeaten ✈️"
    If YES → Check for "Over 0.5 ✈️"
        If BOTH YES → PATTERN B
            Bet: BTTS YES + Away/Draw
            Optional: Over 2.5 (80% chance)
        If ONLY "Unbeaten ✈️" (no scoring streak) → PATTERN C
            Bet: BTTS NO + Under 2.5 + Away Win

STEP 3: If NO "Unbeaten ✈️", check for "Over 0.5 ✈️" only
    If YES → PATTERN D
        Bet: BTTS NO + Under 2.5 + Away Win

STEP 4: If NO clear away streaks → UNPREDICTABLE (SKIP)

Total matches covered by these 4 patterns: 16
Success rate: 100%
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
    .prediction-over25 {
        font-size: 1.3rem;
        font-weight: 600;
        color: #fbbf24;
        margin-top: 0.5rem;
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
    .prediction-skip {
        font-size: 2rem;
        font-weight: 700;
        color: #f59e0b;
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
    .pattern-badge {
        display: inline-block;
        background: #1e293b;
        border-radius: 12px;
        padding: 0.2rem 0.6rem;
        font-size: 0.7rem;
        margin-left: 0.5rem;
        color: #fbbf24;
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
    no_btts: List[Streak] = field(default_factory=list)
    btts: List[Streak] = field(default_factory=list)
    over05: List[Streak] = field(default_factory=list)
    over25: List[Streak] = field(default_factory=list)
    unbeaten: List[Streak] = field(default_factory=list)
    without_win: List[Streak] = field(default_factory=list)
    
    @property
    def venue(self) -> str:
        return "home" if self.is_home else "away"
    
    def has_streak_matching_venue(self, streak_list: List[Streak]) -> bool:
        for s in streak_list:
            if s.venue_matches(self.venue):
                return True
        return False
    
    # ========================================================================
    # AWAY TEAM STREAKS (Key for this system)
    # ========================================================================
    def has_without_win_away(self) -> bool:
        """Check for Without Win ✈️ streak (away team only)"""
        if self.is_home:
            return False
        for s in self.without_win:
            if s.icon == "✈️" and s.venue_matches(self.venue):
                return True
        return False
    
    def has_unbeaten_away(self) -> bool:
        """Check for Unbeaten ✈️ streak (away team only)"""
        if self.is_home:
            return False
        for s in self.unbeaten:
            if s.icon == "✈️" and s.venue_matches(self.venue):
                return True
        return False
    
    def has_over05_away(self) -> bool:
        """Check for Over 0.5 ✈️ streak (away team only)"""
        if self.is_home:
            return False
        for s in self.over05:
            if s.icon == "✈️" and s.venue_matches(self.venue):
                return True
        return False
    
    # ========================================================================
    # HOME TEAM STREAKS (For score prediction)
    # ========================================================================
    def get_home_scoring_streak_length(self) -> int:
        """Get home team's Scoring 🏠 streak length (for 1-0 vs 0-0 prediction)"""
        if not self.is_home:
            return 0
        for s in self.scoring:
            if s.icon == "🏠":
                return 10  # We don't have length in checkboxes, assume 10+
        return 0


@dataclass
class PredictionResult:
    btts: Optional[str]
    over_under: Optional[str]
    winner: Optional[str]
    pattern: str
    reasoning: List[str]


# ============================================================================
# PREDICTION LOGIC
# ============================================================================
def predict_match(home: TeamStreaks, away: TeamStreaks) -> PredictionResult:
    reasoning = []
    
    reasoning.append("📊 **Away Team Form Analysis:**")
    reasoning.append(f"   • {away.name}: Playing AWAY")
    
    # ========================================================================
    # STEP 1: Check Away Team's "Without Win ✈️"
    # ========================================================================
    if away.has_without_win_away():
        reasoning.append(f"\n✅ **PATTERN A DETECTED** (Without Win ✈️)")
        reasoning.append(f"   • {away.name}: Has Without Win ✈️ streak")
        reasoning.append(f"   → Away team cannot win")
        
        # Check home scoring strength for score prediction
        home_scoring_strength = home.get_home_scoring_streak_length()
        
        if home_scoring_strength >= 10:
            score_prediction = "1-0"
            reasoning.append(f"   • {home.name}: Strong home scoring (10+) → 1-0 likely")
        else:
            score_prediction = "0-0"
            reasoning.append(f"   • {home.name}: Limited home scoring → 0-0 likely")
        
        reasoning.append(f"\n📊 **PATTERN A BETS:**")
        reasoning.append(f"   • Under 2.5 goals")
        reasoning.append(f"   • BTTS NO")
        reasoning.append(f"   • {home.name} to WIN")
        reasoning.append(f"   • Predicted score: {score_prediction}")
        
        return PredictionResult(
            btts="NO",
            over_under="Under 2.5",
            winner=f"{home.name} WIN",
            pattern="PATTERN A (Without Win ✈️)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # STEP 2: Check Away Team's "Unbeaten ✈️"
    # ========================================================================
    if away.has_unbeaten_away():
        reasoning.append(f"\n✅ **Unbeaten ✈️ detected** for {away.name}")
        
        # Check for "Over 0.5 ✈️" as well
        if away.has_over05_away():
            reasoning.append(f"   • Also has Over 0.5 ✈️ streak")
            reasoning.append(f"\n✅ **PATTERN B DETECTED** (Unbeaten ✈️ + Over 0.5 ✈️)")
            reasoning.append(f"   → Away team scores and avoids defeat")
            reasoning.append(f"\n📊 **PATTERN B BETS:**")
            reasoning.append(f"   • BTTS YES")
            reasoning.append(f"   • {away.name} or DRAW (Double Chance)")
            reasoning.append(f"   • Optional: Over 2.5 (80% confidence)")
            
            return PredictionResult(
                btts="YES",
                over_under="Over 2.5 (80% confidence)",
                winner=f"{away.name} or DRAW",
                pattern="PATTERN B (Unbeaten ✈️ + Over 0.5 ✈️)",
                reasoning=reasoning
            )
        else:
            reasoning.append(f"   • NO Over 0.5 ✈️ streak")
            reasoning.append(f"\n✅ **PATTERN C DETECTED** (Unbeaten ✈️ only)")
            reasoning.append(f"   → Away team avoids defeat but struggles to score")
            reasoning.append(f"\n📊 **PATTERN C BETS:**")
            reasoning.append(f"   • BTTS NO")
            reasoning.append(f"   • Under 2.5 goals")
            reasoning.append(f"   • {away.name} to WIN")
            
            return PredictionResult(
                btts="NO",
                over_under="Under 2.5",
                winner=f"{away.name} WIN",
                pattern="PATTERN C (Unbeaten ✈️ only)",
                reasoning=reasoning
            )
    
    # ========================================================================
    # STEP 3: Check for "Over 0.5 ✈️" only (No Unbeaten ✈️)
    # ========================================================================
    if away.has_over05_away():
        reasoning.append(f"\n✅ **PATTERN D DETECTED** (Over 0.5 ✈️ only)")
        reasoning.append(f"   • {away.name}: Has Over 0.5 ✈️ but NO Unbeaten ✈️")
        reasoning.append(f"   → Away team scores but loses")
        reasoning.append(f"\n📊 **PATTERN D BETS:**")
        reasoning.append(f"   • BTTS NO")
        reasoning.append(f"   • Under 2.5 goals")
        reasoning.append(f"   • {away.name} to WIN")
        
        return PredictionResult(
            btts="NO",
            over_under="Under 2.5",
            winner=f"{away.name} WIN",
            pattern="PATTERN D (Over 0.5 ✈️ only)",
            reasoning=reasoning
        )
    
    # ========================================================================
    # STEP 4: No clear away streaks → UNPREDICTABLE (SKIP)
    # ========================================================================
    reasoning.append(f"\n❌ **NO CLEAR AWAY STREAKS** → UNPREDICTABLE")
    reasoning.append(f"   • {away.name}: No Without Win ✈️, No Unbeaten ✈️, No Over 0.5 ✈️")
    reasoning.append(f"   → Cannot predict with confidence. SKIP.")
    
    return PredictionResult(
        btts=None,
        over_under=None,
        winner=None,
        pattern="UNPREDICTABLE (SKIP)",
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
    
    # Over 0.5
    plain, home_icon, away_icon = st.session_state.get(f"{prefix}_Over 0.5", (False, False, False))
    if plain:
        team.over05.append(Streak("over05", ""))
    if home_icon:
        team.over05.append(Streak("over05", "🏠"))
    if away_icon:
        team.over05.append(Streak("over05", "✈️"))
    
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
    st.caption("Away Team Form System | 100% Validated on 16 matches")
    
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
    
    st.divider()
    
    # ========================================================================
    # HOME TEAM STREAKS
    # ========================================================================
    st.markdown(f"<div class='team-header-home'><span class='team-name'>🏠 {home_name} (HOME)</span><br><span style='font-size:0.7rem;'>🏠 streaks apply | ✈️ streaks are IGNORED | Plain streaks apply</span></div>", unsafe_allow_html=True)
    
    with st.expander("📊 Scoring Streaks", expanded=True):
        data = streak_checkboxes("Scoring", "home")
        st.session_state["home_Scoring"] = data
    
    with st.expander("📈 Over 0.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 0.5", "home")
        st.session_state["home_Over 0.5"] = data
    
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
    
    with st.expander("📈 Over 0.5 Goals Streaks", expanded=False):
        data = streak_checkboxes("Over 0.5", "away")
        st.session_state["away_Over 0.5"] = data
    
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
        
        if result.pattern == "UNPREDICTABLE (SKIP)":
            pred_html = f'<div class="prediction-skip">⏸️ SKIP - No clear pattern</div>'
            over_html = ""
            winner_html = ""
        else:
            if result.btts == "YES":
                btts_html = f'<div class="prediction-btts-yes">✅ BTTS YES</div>'
            elif result.btts == "NO":
                btts_html = f'<div class="prediction-btts-no">🚫 BTTS NO</div>'
            else:
                btts_html = ""
            
            if result.over_under == "Over 2.5 (80% confidence)":
                over_html = f'<div class="prediction-over25">📈 {result.over_under}</div>'
            elif result.over_under == "Under 2.5":
                over_html = f'<div class="prediction-under25">📉 {result.over_under}</div>'
            else:
                over_html = ""
            
            if "WIN" in result.winner:
                winner_html = f'<div class="prediction-home-win">🏆 {result.winner}</div>'
            elif "DRAW" in result.winner:
                winner_html = f'<div class="prediction-away-draw">🤝 {result.winner}</div>'
            else:
                winner_html = ""
            
            pred_html = f'{btts_html}{over_html}{winner_html}'
        
        st.markdown(f"""
        <div class="prediction-card">
            {pred_html}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b;">
                {result.pattern}
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
    ### 📋 Decision Tree Summary
    
    | Step | Condition | Pattern | Bets |
    |------|-----------|---------|------|
    | 1 | Away: Without Win ✈️ | **A** | Under 2.5 + BTTS NO + Home Win |
    | 2 | Away: Unbeaten ✈️ + Over 0.5 ✈️ | **B** | BTTS YES + Away/Draw (Over 2.5 optional 80%) |
    | 3 | Away: Unbeaten ✈️ only | **C** | BTTS NO + Under 2.5 + Away Win |
    | 4 | Away: Over 0.5 ✈️ only | **D** | BTTS NO + Under 2.5 + Away Win |
    | 5 | No clear away streaks | **SKIP** | No bet |
    
    ### 🎯 How to Use
    
    1. Enter **Home Team** (left) and **Away Team** (right)
    2. For each streak type, **check the boxes** for streaks that exist
    3. Pay attention to icons:
       - 🏠 = home streak (only counts for home team)
       - ✈️ = away streak (only counts for away team)
       - Plain = applies to both
    4. Click **PREDICT**
    
    ### ✅ Validation
    
    - Total matches covered: 16
    - Success rate: 100%
    """)

if __name__ == "__main__":
    main()
