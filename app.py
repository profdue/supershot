import streamlit as st
import pandas as pd
from football_predictor.engine import ProfessionalPredictionEngine

# Page configuration
st.set_page_config(
    page_title="Professional Football Predictor",
    page_icon="⚽",
    layout="wide"
)

# Initialize engine
@st.cache_resource
def load_prediction_engine():
    try:
        engine = ProfessionalPredictionEngine()
        return engine
    except Exception as e:
        st.error(f"Failed to initialize prediction engine: {e}")
        return None

def main():
    st.title("⚽ Professional Football Predictor 2025/26")
    st.markdown("### Advanced match predictions using xG, team quality, and form analysis")
    
    # Load engine
    engine = load_prediction_engine()
    if not engine:
        st.stop()
    
    # Get available teams
    available_teams = engine.get_available_teams()
    
    # Sidebar for match selection
    st.sidebar.header("Match Configuration")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        home_team = st.selectbox(
            "Home Team",
            options=available_teams,
            index=available_teams.index("Arsenal") if "Arsenal" in available_teams else 0
        )
        home_injury = st.selectbox(
            f"{home_team} Injury Status",
            options=["None", "Minor", "Moderate", "Major", "Crisis"],
            help="Impact of injuries on team performance"
        )
    
    with col2:
        away_team = st.selectbox(
            "Away Team", 
            options=available_teams,
            index=available_teams.index("Manchester City") if "Manchester City" in available_teams else 1
        )
        away_injury = st.selectbox(
            f"{away_team} Injury Status",
            options=["None", "Minor", "Moderate", "Major", "Crisis"],
            help="Impact of injuries on team performance"
        )
    
    # Prediction button
    if st.sidebar.button("🎯 Predict Match", type="primary"):
        with st.spinner("Analyzing match data..."):
            try:
                prediction = engine.predict_match(
                    home_team, away_team, home_injury, away_injury
                )
                
                if "error" in prediction:
                    st.error(f"Prediction error: {prediction['error']}")
                else:
                    display_prediction_results(prediction)
                    
            except Exception as e:
                st.error(f"Error during prediction: {e}")
    
    # Display team information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Team Information")
    if home_team and away_team:
        display_team_info(engine, home_team, away_team)

def display_prediction_results(prediction):
    """Display prediction results in an organized layout"""
    st.markdown("---")
    st.header(f"🎯 {prediction['home_team']} vs {prediction['away_team']}")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Expected Goals (Home)",
            prediction['home_expected_goals']
        )
        st.metric(
            "Home Win Probability", 
            f"{prediction['home_win_probability']*100:.1f}%"
        )
    
    with col2:
        st.metric(
            "Expected Goals (Away)", 
            prediction['away_expected_goals']
        )
        st.metric(
            "Draw Probability", 
            f"{prediction['draw_probability']*100:.1f}%"
        )
    
    with col3:
        st.metric(
            "Home Advantage Boost", 
            f"+{prediction['home_advantage_boost']:.3f}"
        )
        st.metric(
            "Away Win Probability", 
            f"{prediction['away_win_probability']*100:.1f}%"
        )
    
    # Scoreline predictions
    st.subheader("📊 Most Likely Scorelines")
    score_cols = st.columns(3)
    for i, scoreline in enumerate(prediction['likely_scorelines']):
        with score_cols[i]:
            st.info(f"**{scoreline}**")
    
    # Additional insights
    st.subheader("🔍 Match Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.write("**Team Factors:**")
        st.write(f"• Home Advantage: {prediction['home_advantage_boost']:.3f} goals")
        st.write(f"• Quality Difference: {prediction['quality_difference']:.3f}")
        st.write(f"• {prediction['home_team']} Injuries: {prediction['home_injury_impact']}")
        st.write(f"• {prediction['away_team']} Injuries: {prediction['away_injury_impact']}")
    
    with insight_col2:
        st.write("**Prediction Confidence:**")
        max_prob = max(
            prediction['home_win_probability'],
            prediction['draw_probability'], 
            prediction['away_win_probability']
        )
        
        if max_prob > 0.65:
            confidence = "High"
            color = "green"
        elif max_prob > 0.55:
            confidence = "Medium" 
            color = "orange"
        else:
            confidence = "Close Match"
            color = "blue"
            
        st.write(f"• **{confidence}** ({(max_prob*100):.1f}% probability)")
        
        # Recommended bet
        if prediction['home_win_probability'] > 0.5:
            recommendation = f"{prediction['home_team']} to win"
        elif prediction['away_win_probability'] > 0.5:
            recommendation = f"{prediction['away_team']} to win" 
        else:
            recommendation = "Draw or close match"
            
        st.write(f"• **Recommendation:** {recommendation}")

def display_team_info(engine, home_team, away_team):
    """Display basic team information in sidebar"""
    try:
        home_qual = engine.team_quality.get_team_quality(home_team)
        away_qual = engine.team_quality.get_team_quality(away_team)
        
        if home_qual and away_qual:
            st.write(f"**{home_team}:**")
            st.write(f"Elo: {home_qual['elo']}")
            st.write(f"Tier: {home_qual['structural_tier']}")
            st.write(f"Value: €{home_qual['squad_value']:,.0f}")
            
            st.write(f"**{away_team}:**") 
            st.write(f"Elo: {away_qual['elo']}")
            st.write(f"Tier: {away_qual['structural_tier']}")
            st.write(f"Value: €{away_qual['squad_value']:,.0f}")
            
    except Exception as e:
        st.sidebar.error("Could not load team information")

if __name__ == "__main__":
    main()
