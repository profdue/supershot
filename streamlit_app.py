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
    page_title="SuperShot Football Predictor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🎯 SuperShot Football Predictor</div>', unsafe_allow_html=True)
    
    st.success("🚀 Welcome to SuperShot Football Prediction Engine!")
    
    # Try to load the engine
    try:
        from football_predictor.engine import ProfessionalPredictionEngine
        
        if 'engine' not in st.session_state:
            st.session_state.engine = ProfessionalPredictionEngine()
            st.success("✅ Prediction engine loaded successfully!")
        
        # Show available leagues
        engine = st.session_state.engine
        leagues = engine.get_available_leagues()
        
        st.write(f"**Available Leagues:** {len(leagues)} leagues loaded")
        
        # Simple team selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 Home Team")
            if leagues:
                home_teams = engine.get_teams_by_league(leagues[0], "home")
                home_team = st.selectbox("Select Home Team", home_teams[:20])
        
        with col2:
            st.subheader("✈️ Away Team")
            if leagues:
                away_teams = engine.get_teams_by_league(leagues[0], "away")
                away_team = st.selectbox("Select Away Team", away_teams[:20])
        
        # Show team info
        if st.button("🎯 Analyze Match"):
            try:
                home_data = engine.get_team_data(home_team)
                away_data = engine.get_team_data(away_team)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{home_team}**")
                    st.write(f"League: {home_data['league']}")
                    st.write(f"xG: {home_data['last_5_xg_per_match']:.2f} per match")
                    st.write(f"xGA: {home_data['last_5_xga_per_match']:.2f} per match")
                
                with col2:
                    st.write(f"**{away_team}**")
                    st.write(f"League: {away_data['league']}")
                    st.write(f"xG: {away_data['last_5_xg_per_match']:.2f} per match")
                    st.write(f"xGA: {away_data['last_5_xga_per_match']:.2f} per match")
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Error analyzing match: {str(e)}")
    
    except ImportError as e:
        st.error(f"❌ Could not import prediction engine: {e}")
        st.info("Please check that all files are in the correct locations.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
