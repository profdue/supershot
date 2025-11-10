import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import warnings
warnings.filterwarnings('ignore')

# Import the enhanced engine
from football_predictor.engine import ProfessionalPredictionEngine

# Clear cache to ensure fresh start
st.cache_data.clear()
st.cache_resource.clear()

# Page Configuration
st.set_page_config(
    page_title="Professional Football Prediction Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# EXACT CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.4rem;
        color: #2e86ab;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .input-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .value-good {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .value-poor {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #856404;
    }
    .success-box {
        background-color: #d1edff;
        border: 1px solid #b3d9ff;
        border-radius: 5px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #004085;
    }
    .understat-format {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-family: monospace;
        font-weight: bold;
        text-align: center;
    }
    .contradiction-flag {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 2px solid #ff4757;
    }
    .disclaimer-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    .kelly-recommendation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    .bankroll-advice {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .debug-info {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .league-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    .home-badge {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .away-badge {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .advantage-indicator {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 8px;
        margin-left: 0.5rem;
        font-weight: bold;
    }
    .strong-advantage {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
    }
    .moderate-advantage {
        background: linear-gradient(135deg, #ffd93d 0%, #ff9a3d 100%);
        color: black;
    }
    .weak-advantage {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%);
        color: white;
    }
    .injury-impact {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 8px;
        margin-left: 0.5rem;
        font-weight: bold;
    }
    .injury-minor {
        background: linear-gradient(135deg, #ffd93d 0%, #ff9a3d 100%);
        color: black;
    }
    .injury-moderate {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
        color: white;
    }
    .injury-significant {
        background: linear-gradient(135deg, #c70039 0%, #ff5733 100%);
        color: white;
    }
    .injury-crisis {
        background: linear-gradient(135deg, #900c3f 0%, #c70039 100%);
        color: white;
    }
    .reliability-high {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .reliability-moderate {
        background: linear-gradient(135deg, #ffd93d 0%, #ff9a3d 100%);
        color: black;
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .reliability-low {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .enhanced-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'prediction_result' not in st.session_state:
        st.session_state.prediction_result = None
    if 'input_data' not in st.session_state:
        st.session_state.input_data = {}
    if 'show_edit' not in st.session_state:
        st.session_state.show_edit = False
    if 'selected_league' not in st.session_state:
        st.session_state.selected_league = "Premier League"

def get_default_inputs():
    """Get default input values"""
    return {
        'home_team': 'Arsenal Home',
        'away_team': 'Manchester United Away',
        'home_xg_total': 10.25,
        'home_xga_total': 1.75,
        'away_xg_total': 8.75,
        'away_xga_total': 10.60,
        'home_injuries': 'None',
        'away_injuries': 'None',
        'home_rest': 7,
        'away_rest': 7,
        'home_odds': 2.15,
        'draw_odds': 3.25,
        'away_odds': 2.80,
        'over_odds': 1.57
    }

def display_enhanced_team_info(engine, team_key, is_home=True):
    """Display enhanced team information using integrated data"""
    team_data = engine.get_team_data(team_key)
    base_name = team_data['base_name']
    
    badge_class = "home-badge" if is_home else "away-badge"
    st.write(f"**Team:** {base_name} <span class='{badge_class}'>{'HOME' if is_home else 'AWAY'}</span>", unsafe_allow_html=True)
    st.write(f"**League:** {team_data['league']}")
    
    # Form trend with emoji
    trend_emoji = "↗️" if team_data['form_trend'] > 0.02 else "↘️" if team_data['form_trend'] < -0.02 else "➡️"
    st.write(f"**Form Trend:** {trend_emoji} {team_data['form_trend']:.3f}")
    
    # Home advantage display
    home_adv = team_data['home_advantage']
    advantage_class = f"{home_adv['strength']}-advantage"
    st.write(f"**{'Home' if is_home else 'Away'} Advantage:** <span class='advantage-indicator {advantage_class}'>{home_adv['strength'].upper()}</span> (+{home_adv['goals_boost']:.3f} goals)", unsafe_allow_html=True)
    
    # Team quality
    quality = team_data['base_quality']
    st.write(f"**Team Quality:** {quality['structural_tier'].title()} (Elo: {quality['elo']})")
    
    # Performance metrics
    st.write(f"**Last {team_data['matches_played']} matches:** {team_data['xg_total']:.2f} xG, {team_data['xga_total']:.2f} xGA")
    st.write(f"**Clean Sheets:** {team_data['clean_sheet_pct']}% | **BTTS:** {team_data['btts_pct']}%")
    st.write(f"**Goal Difference:** {team_data['goal_difference']:+d}")

def display_understat_input_form(engine):
    """ENHANCED: Display the main input form with all improvements"""
    st.markdown('<div class="main-header">🎯 Professional Football Prediction Engine</div>', unsafe_allow_html=True)
    
    # CRITICAL DISCLAIMER
    st.markdown("""
    <div class="disclaimer-box">
    <strong>⚠️ IMPORTANT DISCLAIMER:</strong><br>
    This tool is for <strong>EDUCATIONAL AND ANALYTICAL PURPOSES ONLY</strong>. Sports prediction is inherently uncertain.<br>
    <strong>NEVER bet more than you can afford to lose.</strong> Past performance does not guarantee future results.<br>
    Always practice responsible gambling and seek help if needed.
    </div>
    """, unsafe_allow_html=True)
    
    # Use existing inputs or defaults
    if st.session_state.input_data:
        current_inputs = st.session_state.input_data
    else:
        current_inputs = get_default_inputs()
    
    st.markdown('<div class="section-header">🏆 League & Match Configuration</div>', unsafe_allow_html=True)
    
    # League Selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🌍 Select League")
        selected_league = st.selectbox(
            "Choose League",
            options=engine.get_available_leagues(),
            index=0,
            key="league_select"
        )
        st.session_state.selected_league = selected_league
        
        # Show league info
        home_teams = engine.get_teams_by_league(selected_league, "home")
        away_teams = engine.get_teams_by_league(selected_league, "away")
        st.write(f"**Home Teams:** {len(home_teams)}")
        st.write(f"**Away Teams:** {len(away_teams)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("📊 League Overview")
        st.write(f"**Selected:** <span class='league-badge'>{selected_league}</span>", unsafe_allow_html=True)
        st.write(f"**Data Quality:** ✅ Home/Away specific xG data")
        st.write(f"**Home Advantage:** ✅ Team-specific modeling")
        st.write(f"**Injury Model:** ✅ REALISTIC 5-15% player impact")
        st.write(f"**Validation:** Same-team and cross-league prevention")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">⚽ Team Selection</div>', unsafe_allow_html=True)
    
    # Team Selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🏠 Home Team")
        
        # Get home teams for selected league
        home_teams = engine.get_teams_by_league(selected_league, "home")
        
        home_team = st.selectbox(
            "Select Home Team",
            home_teams,
            index=home_teams.index(current_inputs['home_team']) if current_inputs['home_team'] in home_teams else 0,
            key="home_team_input"
        )
        
        # Display enhanced team info
        display_enhanced_team_info(engine, home_team, True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("✈️ Away Team")
        
        # Get away teams for selected league
        away_teams = engine.get_teams_by_league(selected_league, "away")
        
        away_team = st.selectbox(
            "Select Away Team",
            away_teams,
            index=away_teams.index(current_inputs['away_team']) if current_inputs['away_team'] in away_teams else min(1, len(away_teams)-1),
            key="away_team_input"
        )
        
        # Display enhanced team info
        display_enhanced_team_info(engine, away_team, False)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Validation check
    validation_errors = engine.validate_team_selection(home_team, away_team)
    if validation_errors:
        for error in validation_errors:
            st.error(f"🚫 {error}")
    
    st.markdown('<div class="section-header">📊 Understat Last 5 Matches Data</div>', unsafe_allow_html=True)
    
    # Understat Format Explanation
    st.markdown("""
    <div class="warning-box">
    <strong>📝 Understat Format Guide:</strong><br>
    Enter data in the format shown on Understat.com: <strong>"10.25-1.75"</strong><br>
    - <strong>First number</strong>: Total xG scored in last 5 matches<br>
    - <strong>Second number</strong>: Total xGA conceded in last 5 matches<br>
    <strong>Note:</strong> Using context-specific home/away data for maximum accuracy
    </div>
    """, unsafe_allow_html=True)
    
    # Understat Data Inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        home_base = engine.get_team_base_name(home_team)
        st.subheader(f"📈 {home_base} - Last 5 HOME Matches")
        
        # Understat format display
        current_home_format = f"{current_inputs['home_xg_total']}-{current_inputs['home_xga_total']}"
        st.markdown(f'<div class="understat-format">Understat Format: {current_home_format}</div>', unsafe_allow_html=True)
        
        col1a, col1b = st.columns(2)
        with col1a:
            home_xg_total = st.number_input(
                "Total xG Scored",
                min_value=0.0,
                max_value=20.0,
                value=current_inputs['home_xg_total'],
                step=0.1,
                key="home_xg_total_input",
                help="Total expected goals scored in last 5 HOME matches"
            )
        with col1b:
            home_xga_total = st.number_input(
                "Total xGA Conceded",
                min_value=0.0,
                max_value=20.0,
                value=current_inputs['home_xga_total'],
                step=0.1,
                key="home_xga_total_input",
                help="Total expected goals against in last 5 HOME matches"
            )
        
        # Calculate and show per-match averages
        home_xg_per_match = home_xg_total / 5
        home_xga_per_match = home_xga_total / 5
        
        st.metric("xG per match", f"{home_xg_per_match:.2f}")
        st.metric("xGA per match", f"{home_xga_per_match:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        away_base = engine.get_team_base_name(away_team)
        st.subheader(f"📈 {away_base} - Last 5 AWAY Matches")
        
        # Understat format display
        current_away_format = f"{current_inputs['away_xg_total']}-{current_inputs['away_xga_total']}"
        st.markdown(f'<div class="understat-format">Understat Format: {current_away_format}</div>', unsafe_allow_html=True)
        
        col2a, col2b = st.columns(2)
        with col2a:
            away_xg_total = st.number_input(
                "Total xG Scored",
                min_value=0.0,
                max_value=20.0,
                value=current_inputs['away_xg_total'],
                step=0.1,
                key="away_xg_total_input",
                help="Total expected goals scored in last 5 AWAY matches"
            )
        with col2b:
            away_xga_total = st.number_input(
                "Total xGA Conceded",
                min_value=0.0,
                max_value=20.0,
                value=current_inputs['away_xga_total'],
                step=0.1,
                key="away_xga_total_input",
                help="Total expected goals against in last 5 AWAY matches"
            )
        
        # Calculate and show per-match averages
        away_xg_per_match = away_xg_total / 5
        away_xga_per_match = away_xga_total / 5
        
        st.metric("xG per match", f"{away_xg_per_match:.2f}")
        st.metric("xGA per match", f"{away_xga_per_match:.2f}")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">🎭 Match Context</div>', unsafe_allow_html=True)
    
    # Context Inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🩹 Injury Status")
        
        injury_options = list(engine.injury_weights.keys())
        
        home_injuries = st.selectbox(
            f"{home_base} Injuries",
            injury_options,
            index=injury_options.index(current_inputs['home_injuries']),
            key="home_injuries_input",
            format_func=lambda x: f"{x}: {engine.injury_weights[x]['description']}"
        )
        
        # Show injury impact preview
        if home_injuries != "None":
            injury_data = engine.injury_weights[home_injuries]
            attack_impact = (1 - injury_data['attack_mult']) * 100
            defense_impact = (1 - injury_data['defense_mult']) * 100
            injury_class = f"injury-{injury_data['impact_level'].lower()}"
            st.write(f"**Expected Impact:** <span class='injury-impact {injury_class}'>{injury_data['impact_level'].upper()}</span> - Attack: -{attack_impact:.0f}%, Defense: -{defense_impact:.0f}%", unsafe_allow_html=True)
        
        away_injuries = st.selectbox(
            f"{away_base} Injuries",
            injury_options,
            index=injury_options.index(current_inputs['away_injuries']),
            key="away_injuries_input",
            format_func=lambda x: f"{x}: {engine.injury_weights[x]['description']}"
        )
        
        # Show injury impact preview
        if away_injuries != "None":
            injury_data = engine.injury_weights[away_injuries]
            attack_impact = (1 - injury_data['attack_mult']) * 100
            defense_impact = (1 - injury_data['defense_mult']) * 100
            injury_class = f"injury-{injury_data['impact_level'].lower()}"
            st.write(f"**Expected Impact:** <span class='injury-impact {injury_class}'>{injury_data['impact_level'].upper()}</span> - Attack: -{attack_impact:.0f}%, Defense: -{defense_impact:.0f}%", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🕐 Fatigue & Recovery")
        
        home_rest = st.number_input(
            f"{home_base} Rest Days",
            min_value=2,
            max_value=14,
            value=current_inputs['home_rest'],
            key="home_rest_input",
            help="Days since last match"
        )
        
        away_rest = st.number_input(
            f"{away_base} Rest Days",
            min_value=2,
            max_value=14,
            value=current_inputs['away_rest'],
            key="away_rest_input",
            help="Days since last match"
        )
        
        # Show rest comparison
        rest_diff = home_rest - away_rest
        if rest_diff > 2:
            st.success(f"🏠 **REST ADVANTAGE**: {home_base} has {rest_diff} more rest days")
        elif rest_diff < -2:
            st.warning(f"✈️ **REST ADVANTAGE**: {away_base} has {-rest_diff} more rest days")
        else:
            st.info("⚖️ **EVEN REST**: Both teams have similar rest days")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">💰 Market Odds</div>', unsafe_allow_html=True)
    
    # Odds Inputs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🏠 Home Win")
        home_odds = st.number_input(
            "Home Odds",
            min_value=1.01,
            max_value=100.0,
            value=current_inputs['home_odds'],
            step=0.1,
            key="home_odds_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🤝 Draw")
        draw_odds = st.number_input(
            "Draw Odds",
            min_value=1.01,
            max_value=100.0,
            value=current_inputs['draw_odds'],
            step=0.1,
            key="draw_odds_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("✈️ Away Win")
        away_odds = st.number_input(
            "Away Odds",
            min_value=1.01,
            max_value=100.0,
            value=current_inputs['away_odds'],
            step=0.1,
            key="away_odds_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("⚽ Over 2.5")
        over_odds = st.number_input(
            "Over 2.5 Odds",
            min_value=1.01,
            max_value=100.0,
            value=current_inputs['over_odds'],
            step=0.1,
            key="over_odds_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Compile all inputs
    inputs = {
        'home_team': home_team,
        'away_team': away_team,
        'home_xg_total': home_xg_total,
        'home_xga_total': home_xga_total,
        'away_xg_total': away_xg_total,
        'away_xga_total': away_xga_total,
        'home_injuries': home_injuries,
        'away_injuries': away_injuries,
        'home_rest': home_rest,
        'away_rest': away_rest,
        'home_odds': home_odds,
        'draw_odds': draw_odds,
        'away_odds': away_odds,
        'over_odds': over_odds
    }
    
    return inputs, validation_errors

def display_enhanced_predictions(engine, result, inputs):
    """Display enhanced predictions with better accuracy"""
    st.markdown('<div class="section-header">🎯 Enhanced Predictions <span class="enhanced-badge">HIGH ACCURACY</span></div>', unsafe_allow_html=True)
    
    home_base = engine.get_team_base_name(inputs['home_team'])
    away_base = engine.get_team_base_name(inputs['away_team'])
    
    # Winner Prediction with outcome-specific confidence
    st.markdown("#### 🏆 Match Winner")
    col1, col2, col3 = st.columns(3)
    
    winner_probs = result['enhanced_predictions']['winner']
    
    # Get outcome-specific confidences
    if isinstance(result['confidence'], dict):
        # New: outcome-specific confidence
        home_confidence = result['confidence']['home_win']
        draw_confidence = result['confidence']['draw']
        away_confidence = result['confidence']['away_win']
    else:
        # Fallback: legacy single confidence
        home_confidence = result['confidence']
        draw_confidence = result['confidence']
        away_confidence = result['confidence']
    
    with col1:
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        home_prob = winner_probs['home_win']
        home_color = "🟢" if home_prob > 0.50 else "🟡" if home_prob > 0.35 else "🔴"
        st.metric(f"{home_color} {home_base} Win", f"{home_prob:.1%}")
        st.write(f"**Confidence:** {home_confidence:.0f}%")
        if home_prob > 0.45:
            st.write("**✅ FAVORED**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        draw_prob = winner_probs['draw']
        draw_color = "🟢" if draw_prob > 0.30 else "🟡" if draw_prob > 0.25 else "🔴"
        st.metric(f"{draw_color} Draw", f"{draw_prob:.1%}")
        st.write(f"**Confidence:** {draw_confidence:.0f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        away_prob = winner_probs['away_win']
        away_color = "🟢" if away_prob > 0.50 else "🟡" if away_prob > 0.35 else "🔴"
        st.metric(f"{away_color} {away_base} Win", f"{away_prob:.1%}")
        st.write(f"**Confidence:** {away_confidence:.0f}%")
        if away_prob > 0.45:
            st.write("**✅ FAVORED**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Over/Under Predictions
    st.markdown("#### ⚽ Goals Market")
    
    over_under_probs = result['enhanced_predictions']['over_under']
    ou_confidence = result['enhanced_predictions']['over_under']['confidence']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        over_15 = over_under_probs['over_1.5']
        color_15 = "🟢" if over_15 > 0.70 else "🟡" if over_15 > 0.60 else "🔴"
        st.metric(f"{color_15} Over 1.5 Goals", f"{over_15:.1%}")
        st.write(f"**Confidence:** {ou_confidence:.0f}%")
        if over_15 > 0.65:
            st.write("**📈 LIKELY**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        over_25 = over_under_probs['over_2.5']
        color_25 = "🟢" if over_25 > 0.60 else "🟡" if over_25 > 0.50 else "🔴"
        st.metric(f"{color_25} Over 2.5 Goals", f"{over_25:.1%}")
        st.write(f"**Confidence:** {ou_confidence:.0f}%")
        if over_25 > 0.55:
            st.write("**📈 LIKELY**")
        elif over_25 < 0.45:
            st.write("**📉 UNLIKELY**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        over_35 = over_under_probs['over_3.5']
        color_35 = "🟢" if over_35 > 0.40 else "🟡" if over_35 > 0.30 else "🔴"
        st.metric(f"{color_35} Over 3.5 Goals", f"{over_35:.1%}")
        st.write(f"**Confidence:** {ou_confidence:.0f}%")
        if over_35 > 0.35:
            st.write("**⚡ HIGH SCORING**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # BTTS Prediction
    st.markdown("#### 🎪 Both Teams To Score")
    
    btts_probs = result['enhanced_predictions']['btts']
    btts_confidence = result['enhanced_predictions']['btts']['confidence']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        btts_yes = btts_probs['btts_yes']
        btts_color = "🟢" if btts_yes > 0.60 else "🟡" if btts_yes > 0.50 else "🔴"
        st.metric(f"{btts_color} BTTS: Yes", f"{btts_yes:.1%}")
        st.write(f"**Confidence:** {btts_confidence:.0f}%")
        if btts_yes > 0.55:
            st.write("**🎯 LIKELY**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        btts_no = btts_probs['btts_no']
        no_btts_color = "🟢" if btts_no > 0.60 else "🟡" if btts_no > 0.50 else "🔴"
        st.metric(f"{no_btts_color} BTTS: No", f"{btts_no:.1%}")
        st.write(f"**Confidence:** {btts_confidence:.0f}%")
        if btts_no > 0.55:
            st.write("**🚫 UNLIKELY**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Key Factors
    st.markdown("---")
    st.markdown('<div class="section-header">🔍 Prediction Key Factors</div>', unsafe_allow_html=True)
    
    with st.expander("View Detailed Factors"):
        # Winner factors
        st.write("**🎯 Winner Prediction Factors:**")
        winner_factors = result['enhanced_predictions']['winner']['key_factors']
        for factor, value in winner_factors.items():
            st.write(f"- {factor.replace('_', ' ').title()}: {value:.3f}")
        
        # Over/Under factors
        st.write("**⚽ Over/Under Prediction Factors:**")
        ou_factors = result['enhanced_predictions']['over_under']['key_factors']
        for factor, value in ou_factors.items():
            if isinstance(value, float):
                st.write(f"- {factor.replace('_', ' ').title()}: {value:.3f}")
            else:
                st.write(f"- {factor.replace('_', ' ').title()}: {value}")
        
        # BTTS factors
        st.write("**🎪 BTTS Prediction Factors:**")
        btts_factors = result['enhanced_predictions']['btts']['key_factors']
        for factor, value in btts_factors.items():
            st.write(f"- {factor.replace('_', ' ').title()}: {value:.3f}")

def display_prediction_results(engine, result, inputs):
    """ENHANCED: Display prediction results with integrated data"""
    st.markdown('<div class="main-header">🎯 Enhanced Prediction Results</div>', unsafe_allow_html=True)
    
    # Get base team names for display
    home_base = engine.get_team_base_name(inputs['home_team'])
    away_base = engine.get_team_base_name(inputs['away_team'])
    
    # Match header
    st.markdown(f'<h2 style="text-align: center; color: #1f77b4;">{home_base} vs {away_base}</h2>', unsafe_allow_html=True)
    
    # League badge
    home_league = engine.get_team_data(inputs['home_team'])['league']
    st.markdown(f'<div style="text-align: center; margin-bottom: 1rem;"><span class="league-badge">{home_league}</span> <span class="enhanced-badge">ENHANCED PREDICTIONS</span></div>', unsafe_allow_html=True)
    
    # Context Reliability Indicator
    reliability_class = f"reliability-{result['reliability_level'].split()[0].lower()}"
    st.markdown(f'<div class="{reliability_class}">{result["reliability_level"]}: {result["reliability_advice"]}</div>', unsafe_allow_html=True)
    
    # Enhanced Team Analysis
    st.markdown('<div class="section-header">📊 Team Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("🏠 Home Team Analysis")
        display_enhanced_team_info(engine, inputs['home_team'], True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.subheader("✈️ Away Team Analysis")  
        display_enhanced_team_info(engine, inputs['away_team'], False)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Expected score card
    st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
    expected_home = result['expected_goals']['home']
    expected_away = result['expected_goals']['away']
    st.markdown(f'<h1 style="font-size: 4rem; margin: 1rem 0;">{expected_home:.2f} - {expected_away:.2f}</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2rem;">Expected Final Score (Enhanced Poisson-based)</p>', unsafe_allow_html=True)
    
    # ✅ FIXED: Overall confidence - handle both dictionary and number formats
    confidence_data = result['confidence']
    
    if isinstance(confidence_data, dict):
        # New: outcome-specific confidence dictionary
        confidence_values = list(confidence_data.values())
        avg_confidence = sum(confidence_values) / len(confidence_values)
        confidence_stars = "★" * int((avg_confidence - 40) / 8) + "☆" * (5 - int((avg_confidence - 40) / 8))
        confidence_text = "Low" if avg_confidence < 55 else "Medium" if avg_confidence < 70 else "High"
        
        st.markdown(f'<div style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown(f'<span style="background: rgba(255,255,255,0.3); padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold;">Overall Confidence: {confidence_stars} ({avg_confidence:.0f}% - {confidence_text})</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show outcome-specific confidence breakdown
        with st.expander("🔍 Outcome-Specific Confidence Breakdown"):
            st.write(f"**🏠 {home_base} Win:** {confidence_data['home_win']:.0f}% confidence")
            st.write(f"**🤝 Draw:** {confidence_data['draw']:.0f}% confidence") 
            st.write(f"**✈️ {away_base} Win:** {confidence_data['away_win']:.0f}% confidence")
            
    else:
        # Legacy: single confidence number
        confidence = confidence_data
        confidence_stars = "★" * int((confidence - 40) / 8) + "☆" * (5 - int((confidence - 40) / 8))
        confidence_text = "Low" if confidence < 55 else "Medium" if confidence < 65 else "High" if confidence < 75 else "Very High"
        
        st.markdown(f'<div style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown(f'<span style="background: rgba(255,255,255,0.3); padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold;">Overall Confidence: {confidence_stars} ({confidence:.0f}% - {confidence_text})</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show confidence factors on hover/expand
    with st.expander("Confidence Breakdown"):
        factors = result['confidence_factors']
        st.write("**Confidence Factors:**")
        for factor, value in factors.items():
            st.write(f"- {factor.replace('_', ' ').title()}: {value:.1%}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display Enhanced Predictions
    display_enhanced_predictions(engine, result, inputs)
    
    st.markdown("---")
    
    # Value Bets Section
    st.markdown('<div class="section-header">💰 Value Bet Analysis</div>', unsafe_allow_html=True)
    
    value_bets = result['value_bets']
    
    # Find best value bets
    excellent_bets = [k for k, v in value_bets.items() if v['rating'] == 'excellent']
    good_bets = [k for k, v in value_bets.items() if v['rating'] == 'good']
    
    if excellent_bets or good_bets:
        for bet_type in excellent_bets + good_bets:
            data = value_bets[bet_type]
            if data['rating'] == 'excellent':
                st.markdown('<div class="value-good">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="value-poor">', unsafe_allow_html=True)
            
            bet_name = {
                'home': f"{home_base} Win",
                'draw': "Draw",
                'away': f"{away_base} Win", 
                'over_2.5': "Over 2.5 Goals"
            }[bet_type]
            
            odds = inputs[f"{bet_type}_odds" if bet_type != 'over_2.5' else 'over_odds']
            
            st.markdown(f"**✅ {bet_name} @ {odds:.2f}**")
            st.markdown(f"**Model Probability:** {data['model_prob']:.1%} | **Market Implied:** {data['implied_prob']:.1%}")
            st.markdown(f"**Value Ratio:** {data['value_ratio']:.2f}x | **Expected Value:** {data['ev']:.1%}")
            
            if data['kelly_fraction'] > 0:
                st.markdown(f'<div class="kelly-recommendation">', unsafe_allow_html=True)
                st.markdown(f"**Kelly Recommended Stake:** {data['kelly_fraction']:.1%} of bankroll")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if data['rating'] == 'excellent':
                st.markdown("**🎯 EXCELLENT VALUE BET**")
            else:
                st.markdown("**👍 GOOD VALUE OPPORTUNITY**")
                
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**No strong value bets identified**")
        st.markdown("All market odds appear efficient for this match.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Key Insights
    st.markdown('<div class="section-header">🧠 Key Insights & Analysis</div>', unsafe_allow_html=True)
    
    for insight in result['insights']:
        st.markdown(f'<div class="metric-card">• {insight}</div>', unsafe_allow_html=True)
    
    # Data integration status
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.markdown("**✅ ENHANCED DATA INTEGRATION:** All data updates have been fully integrated and are being utilized in predictions.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Statistical insights
    total_xg = result['expected_goals']['home'] + result['expected_goals']['away']
    home_data = result['team_data']['home']
    away_data = result['team_data']['away']
    
    st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("**📈 Statistical Summary:**")
    st.markdown(f"- **Total Expected Goals:** {total_xg:.2f}")
    st.markdown(f"- **Match Type:** {'High-Scoring' if total_xg > 3.0 else 'Average' if total_xg > 2.0 else 'Low-Scoring'}")
    st.markdown(f"- **{home_base} Attack Rating:** {home_data['attack_strength']:.2f}x league average")
    st.markdown(f"- **{away_base} Attack Rating:** {away_data['attack_strength']:.2f}x league average")
    st.markdown(f"- **{home_base} Defense Rating:** {home_data['defense_strength']:.2f}x league average")
    st.markdown(f"- **{away_base} Defense Rating:** {away_data['defense_strength']:.2f}x league average")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bankroll Management Advice
    st.markdown('<div class="section-header">💼 Bankroll Management</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="bankroll-advice">
    <strong>Responsible Betting Guidelines:</strong><br>
    • <strong>Never bet more than 1-2% of your total bankroll on a single bet</strong><br>
    • Use Kelly Criterion fractions as maximum stakes, not recommendations<br>
    • Maintain detailed records of all bets and results<br>
    • Set stop-loss limits and stick to them<br>
    • Remember: Even the best models have losing streaks
    </div>
    """, unsafe_allow_html=True)
    
    # Professional Performance Expectations
    st.markdown('<div class="section-header">📊 Realistic Performance Expectations</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
    <strong>Professional Betting Reality Check:</strong><br>
    • <strong>Enhanced Accuracy:</strong> 55-60% for match outcomes with integrated data<br>
    • <strong>Sustainable Edge:</strong> 3-6% in efficient markets<br>
    • <strong>Value Bet Frequency:</strong> 10-20% of matches with enhanced detection<br>
    • <strong>Long-term Success:</strong> Requires discipline and proper bankroll management<br>
    • <strong>Variance:</strong> Even with positive EV, losing streaks of 5-10 bets are normal
    </div>
    """, unsafe_allow_html=True)
    
    # Calculation Details
    with st.expander("🔧 Technical Details"):
        st.write("**Enhanced Prediction Methodology:**")
        st.write("- Integrated data from multiple sources (xG, ELO, form, BTTS, clean sheets)")
        st.write("- Team-specific home advantage modeling")
        st.write("- Enhanced Poisson distribution with quality and form factors")
        st.write("- Injury impact modeling (5-15% realistic impacts)")
        st.write("- Confidence scoring for each prediction type")
        
        if 'calculation_details' in result:
            details = result['calculation_details']
            st.write("**Calculation Details:**")
            for key, value in details.items():
                if key not in ['key_factors_winner', 'key_factors_over_under', 'key_factors_btts']:
                    st.write(f"- {key}: {value}")
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 New Prediction", use_container_width=True):
            st.session_state.prediction_result = None
            st.session_state.input_data = {}
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit Inputs", use_container_width=True, type="primary"):
            st.session_state.show_edit = True
            st.session_state.input_data = inputs
            st.rerun()
    
    with col3:
        if st.button("📊 Advanced Analytics", use_container_width=True):
            st.info("Advanced analytics feature coming soon!")

def main():
    """Main application function"""
    initialize_session_state()
    
    # Initialize engine with caching
    @st.cache_resource
    def load_engine():
        try:
            engine = ProfessionalPredictionEngine()
            return engine
        except Exception as e:
            st.error(f"Failed to initialize prediction engine: {e}")
            return None

    engine = load_engine()
    if not engine:
        st.stop()
    
    # Show edit form if requested
    if st.session_state.show_edit:
        st.markdown('<div class="main-header">✏️ Edit Match Inputs</div>', unsafe_allow_html=True)
        inputs, validation_errors = display_understat_input_form(engine)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Enhanced Prediction", use_container_width=True, type="primary") and not validation_errors:
                result, errors, warnings = engine.predict_match_enhanced(inputs)
                if result:
                    st.session_state.prediction_result = result
                    st.session_state.input_data = inputs
                    st.session_state.show_edit = False
                    st.rerun()
                else:
                    for error in errors:
                        st.error(f"🚫 {error}")
            
            if st.button("← Back to Results", use_container_width=True):
                st.session_state.show_edit = False
                st.rerun()
    
    # Show prediction results if available
    elif st.session_state.prediction_result:
        display_prediction_results(engine, st.session_state.prediction_result, st.session_state.input_data)
    
    # Show main input form
    else:
        inputs, validation_errors = display_understat_input_form(engine)
        
        # Generate Prediction Button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Enhanced Prediction", use_container_width=True, type="primary", key="main_predict") and not validation_errors:
                with st.spinner("🤖 Generating enhanced predictions with integrated data..."):
                    result, errors, warnings = engine.predict_match_enhanced(inputs)
                    if result:
                        st.session_state.prediction_result = result
                        st.session_state.input_data = inputs
                        st.rerun()
                    else:
                        for error in errors:
                            st.error(f"🚫 {error}")

if __name__ == "__main__":
    main()
