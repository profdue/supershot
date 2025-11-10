import streamlit as st
import os
import sys

st.set_page_config(page_title="Debug", page_icon="🔧")

st.title("🔧 Debug Information")

# Show current environment
st.subheader("📁 File System Info")
st.write("**Current Directory:**", os.getcwd())
st.write("**Python Path:**", sys.path)

# List all files
st.write("**All Files in Root:**")
try:
    files = os.listdir('.')
    for file in files:
        st.write(f"- {file}")
        if os.path.isdir(file):
            st.write(f"  📁 Folder contents: {os.listdir(file)}")
except Exception as e:
    st.error(f"Error listing files: {e}")

# Test imports
st.subheader("🔧 Import Tests")

try:
    from football_predictor.engine import ProfessionalPredictionEngine
    st.success("✅ SUCCESS: Imported ProfessionalPredictionEngine")
except ImportError as e:
    st.error(f"❌ FAILED: Import ProfessionalPredictionEngine - {e}")

try:
    from football_predictor import config
    st.success("✅ SUCCESS: Imported config")
except ImportError as e:
    st.error(f"❌ FAILED: Import config - {e}")

# Check if files exist
st.subheader("📋 File Existence Check")
files_to_check = [
    'football_predictor/__init__.py',
    'football_predictor/engine.py', 
    'football_predictor/config.py',
    'data/teams.csv'
]

for file in files_to_check:
    if os.path.exists(file):
        st.success(f"✅ {file} - EXISTS")
    else:
        st.error(f"❌ {file} - MISSING")

st.info("Share this debug output so I can see exactly what's wrong!")
