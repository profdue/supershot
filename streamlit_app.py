import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import warnings
import logging
import os
import sys

# Add current directory to path to find our modules
sys.path.insert(0, os.path.dirname(__file__))

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page Configuration
st.set_page_config(
    page_title="Professional Football Prediction Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Styling
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
    .success-box {
        background-color: #d1edff;
        border: 1px solid #b3d9ff;
        border-radius: 5px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #004085;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'engine' not in st.session_state:
        st.session_state.engine = None
    if 'prediction_result' not in st.session_state:
        st.session_state.prediction_result = None
    if 'input_data' not in st.session_state:
        st.session_state.input_data = {}

def load_engine():
    """Load the prediction engine with error handling"""
    try:
        from football_predictor.engine import ProfessionalPredictionEngine
        return ProfessionalPredictionEngine()
    except Exception as e:
        st.error(f"❌ Error loading prediction engine: {str(e)}")
        return None

def show_simple_interface():
    """Show a simple working interface"""
    st.markdown('<div class="main-header">🎯 Football Prediction Engine</div>', unsafe_allow_html=True)
    
    # Initialize engine
    if st.session_state.engine is None:
        with st.spinner("Loading prediction engine..."):
            st.session_state.engine = load_engine()
    
    if st.session_state.engine is None:
        st.error("""
        ❌ Could not load the prediction engine. Please check:
        - All Python files are in the football_predictor folder
        - CSV files are in the data folder
        - Requirements are installed
        """)
        return
    
    st.success("✅ Prediction Engine Loaded Successfully!")
    
    # Show available leagues
    try:
        leagues = st.session_state.engine.get_available_leagues()
        st.write(f"**Available Leagues:** {', '.join(leagues)}")
        
        # Simple team selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 Home Team")
            home_teams = st.session_state.engine.get_teams_by_league(leagues[0], "home")
            home_team = st.selectbox("Select Home Team", home_teams[:10])  # Show first 10
        
        with col2:
            st.subheader("✈️ Away Team")
            away_teams = st.session_state.engine.get_teams_by_league(leagues[0], "away")
            away_team = st.selectbox("Select Away Team", away_teams[:10])  # Show first 10
        
        # Basic match inputs
        st.subheader("📊 Match Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            home_xg = st.number_input("Home Team xG", value=2.0, min_value=0.1, max_value=10.0, step=0.1)
            home_injuries = st.selectbox("Home Injuries", ["None", "Minor", "Moderate", "Significant", "Crisis"])
        
        with col2:
            away_xg = st.number_input("Away Team xG", value=1.5, min_value=0.1, max_value=10.0, step=0.1)
            away_injuries = st.selectbox("Away Injuries", ["None", "Minor", "Moderate", "Significant", "Crisis"])
        
        # Prediction button
        if st.button("🎯 Predict Match", type="primary"):
            with st.spinner("Calculating prediction..."):
                try:
                    # Create simple inputs
                    inputs = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_xg_total': home_xg * 5,  # Convert to total for 5 matches
                        'home_xga_total': 1.5 * 5,     # Default defense
                        'away_xg_total': away_xg * 5,
                        'away_xga_total': 1.5 * 5,
                        'home_injuries': home_injuries,
                        'away_injuries': away_injuries,
                        'home_rest': 7,
                        'away_rest': 7,
                        'home_odds': 2.0,
                        'draw_odds': 3.5,
                        'away_odds': 3.0,
                        'over_odds': 1.8
                    }
                    
                    result = st.session_state.engine.predict_match(inputs)
                    
                    if 'error' in result:
                        st.error(f"Prediction error: {result['error']}")
                    else:
                        st.session_state.prediction_result = result
                        st.session_state.input_data = inputs
                        st.success("✅ Prediction completed!")
                        
                        # Show simple results
                        st.subheader("📈 Prediction Results")
                        
                        expected_home = result['expected_goals']['home']
                        expected_away = result['expected_goals']['away']
                        
                        st.metric("Expected Score", f"{expected_home:.2f} - {expected_away:.2f}")
                        
                        # Show probabilities
                        probs = result['probabilities']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Home Win", f"{probs['home_win']:.1%}")
                        with col2:
                            st.metric("Draw", f"{probs['draw']:.1%}")
                        with col3:
                            st.metric("Away Win", f"{probs['away_win']:.1%}")
                
                except Exception as e:
                    st.error(f"❌ Prediction failed: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error loading team data: {str(e)}")

def main():
    """Main application function"""
    initialize_session_state()
    
    # Show simple working interface
    show_simple_interface()
    
    # Debug information (collapsed by default)
    with st.expander("🔧 Debug Information"):
        st.write("**Session State:**", st.session_state)
        st.write("**Current Directory:**", os.getcwd())
        st.write("**Files in Directory:**", os.listdir('.'))
        if os.path.exists('football_predictor'):
            st.write("**Files in football_predictor:**", os.listdir('football_predictor'))
        if os.path.exists('data'):
            st.write("**Files in data:**", os.listdir('data'))

if __name__ == "__main__":
    main()
