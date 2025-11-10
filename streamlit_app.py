# streamlit_app.py
import streamlit as st
import pandas as pd
import logging
from football_predictor.engine import ProfessionalPredictionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables"""
    if 'engine' not in st.session_state:
        st.session_state.engine = ProfessionalPredictionEngine()
    if 'prediction_result' not in st.session_state:
        st.session_state.prediction_result = None
    if 'input_data' not in st.session_state:
        st.session_state.input_data = {}
    if 'show_diagnostics' not in st.session_state:
        st.session_state.show_diagnostics = False

def show_diagnostics():
    """Show system diagnostics"""
    st.title("🔍 System Diagnostics")
    
    engine = st.session_state.engine
    
    # Team database
    st.subheader("📊 Team Database")
    teams_df = engine.data_loader.load_teams()
    st.write(f"**Total Teams:** {len(teams_df)}")
    
    if not teams_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Teams by League:**")
            league_counts = teams_df['league'].value_counts()
            st.write(league_counts)
        with col2:
            st.write("**Sample Teams:**")
            st.dataframe(teams_df.head(10))
    
    # Team quality
    st.subheader("🏆 Team Quality")
    quality_df = engine.data_loader.load_team_quality()
    if not quality_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Quality Distribution:**")
            tier_counts = quality_df['structural_tier'].value_counts()
            st.write(tier_counts)
        with col2:
            st.write("**Elite Teams:**")
            elite_teams = quality_df[quality_df['structural_tier'] == 'elite']['team_base'].tolist()
            st.write(", ".join(elite_teams))
    
    # Test team lookup
    st.subheader("🔎 Test Team Lookup")
    test_team = st.text_input("Enter team name to test", "Arsenal Home")
    if st.button("Test Lookup"):
        team_data = engine.get_team_data(test_team)
        team_quality = engine.team_quality.get_team_quality(test_team)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Team Data:**")
            st.json(team_data)
        with col2:
            st.write("**Team Quality:**")
            st.write(team_quality)

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Professional Football Prediction Engine",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Predict", "Diagnostics"])
    
    if page == "Predict":
        show_prediction_interface()
    elif page == "Diagnostics":
        show_diagnostics()

def show_prediction_interface():
    """Show main prediction interface"""
    st.title("🎯 Professional Football Prediction Engine")
    
    engine = st.session_state.engine
    
    # League selection
    leagues = engine.get_available_leagues()
    selected_league = st.selectbox("Select League", leagues)
    
    # Team selection
    home_teams = engine.get_teams_by_league(selected_league, "home")
    away_teams = engine.get_teams_by_league(selected_league, "away")
    
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = st.selectbox("Home Team", home_teams)
        home_data = engine.get_team_data(home_team)
        home_quality = engine.team_quality.get_team_quality(home_team)
        
        st.write(f"**Team:** {engine.get_team_base_name(home_team)}")
        st.write(f"**Quality:** {home_quality.upper()}")
        st.write(f"**Form:** {home_data['last_5_xg_total']:.2f} xG, {home_data['last_5_xga_total']:.2f} xGA")
    
    with col2:
        away_team = st.selectbox("Away Team", away_teams)
        away_data = engine.get_team_data(away_team)
        away_quality = engine.team_quality.get_team_quality(away_team)
        
        st.write(f"**Team:** {engine.get_team_base_name(away_team)}")
        st.write(f"**Quality:** {away_quality.upper()}")
        st.write(f"**Form:** {away_data['last_5_xg_total']:.2f} xG, {away_data['last_5_xga_total']:.2f} xGA")
    
    # Input validation
    validation_errors = engine.validate_team_selection(home_team, away_team)
    if validation_errors:
        for error in validation_errors:
            st.error(error)
        return
    
    # Match inputs
    st.subheader("📊 Match Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**{engine.get_team_base_name(home_team)} - Last 5 Home Matches**")
        home_xg_total = st.number_input("Total xG Scored", value=home_data['last_5_xg_total'], key="home_xg")
        home_xga_total = st.number_input("Total xGA Conceded", value=home_data['last_5_xga_total'], key="home_xga")
        home_injuries = st.selectbox("Injury Status", ["None", "Minor", "Moderate", "Significant", "Crisis"], key="home_inj")
        home_rest = st.number_input("Rest Days", value=7, min_value=2, max_value=14, key="home_rest")
    
    with col2:
        st.write(f"**{engine.get_team_base_name(away_team)} - Last 5 Away Matches**")
        away_xg_total = st.number_input("Total xG Scored", value=away_data['last_5_xg_total'], key="away_xg")
        away_xga_total = st.number_input("Total xGA Conceded", value=away_data['last_5_xga_total'], key="away_xga")
        away_injuries = st.selectbox("Injury Status", ["None", "Minor", "Moderate", "Significant", "Crisis"], key="away_inj")
        away_rest = st.number_input("Rest Days", value=7, min_value=2, max_value=14, key="away_rest")
    
    # Odds inputs
    st.subheader("💰 Market Odds")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        home_odds = st.number_input("Home Win Odds", value=2.15, min_value=1.01, key="home_odds")
    with col2:
        draw_odds = st.number_input("Draw Odds", value=3.25, min_value=1.01, key="draw_odds")
    with col3:
        away_odds = st.number_input("Away Win Odds", value=2.80, min_value=1.01, key="away_odds")
    with col4:
        over_odds = st.number_input("Over 2.5 Goals", value=1.57, min_value=1.01, key="over_odds")
    
    # Prediction button
    if st.button("🚀 Generate Prediction", type="primary"):
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
        
        with st.spinner("Calculating prediction..."):
            result = engine.predict_match(inputs)
            
        if 'error' in result:
            for error in result['error']:
                st.error(error)
        else:
            st.session_state.prediction_result = result
            st.session_state.input_data = inputs
    
    # Show results if available
    if st.session_state.prediction_result:
        show_prediction_results()

def show_prediction_results():
    """Show prediction results"""
    result = st.session_state.prediction_result
    inputs = st.session_state.input_data
    
    st.markdown("---")
    st.subheader("📈 Prediction Results")
    
    # Expected score
    expected_home = result['expected_goals']['home']
    expected_away = result['expected_goals']['away']
    
    st.markdown(f"### Expected Score: **{expected_home:.2f} - {expected_away:.2f}**")
    
    # Probabilities
    probs = result['probabilities']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Home Win", f"{probs['home_win']:.1%}")
    with col2:
        st.metric("Draw", f"{probs['draw']:.1%}")
    with col3:
        st.metric("Away Win", f"{probs['away_win']:.1%}")
    
    # Goals market
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Over 2.5 Goals", f"{probs['over_2.5']:.1%}")
    with col2:
        st.metric("Under 2.5 Goals", f"{probs['under_2.5']:.1%}")
    
    # Value bets
    st.subheader("💰 Value Bets")
    value_bets = result['value_bets']
    
    for market, data in value_bets.items():
        if data['rating'] in ['excellent', 'good']:
            market_name = {
                'home': 'Home Win', 'draw': 'Draw', 
                'away': 'Away Win', 'over_2.5': 'Over 2.5 Goals'
            }[market]
            
            st.success(
                f"**{market_name}** @ {inputs[f'{market}_odds']:.2f} - "
                f"EV: {data['ev']:.1%} ({data['rating'].upper()})"
            )
    
    # Insights
    st.subheader("🧠 Match Insights")
    for insight in result['insights']:
        st.write(f"• {insight}")

if __name__ == "__main__":
    main()
