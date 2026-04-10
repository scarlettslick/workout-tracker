import streamlit as st
import psycopg2
from datetime import date

st.set_page_config(page_title="My Goals", page_icon="🎯")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("🎯 My Goals")

# ── ADD GOAL FORM ──────────────────────────────────────────
st.subheader("Add a New Goal")

with st.form("add_goal_form"):
    title = st.text_input("Goal Title *", placeholder="e.g. Bench Press 225 lbs")
    description = st.text_area("Description (optional)", placeholder="e.g. Hit a 2 plate bench by summer")
    
    col1, col2 = st.columns(2)
    with col1:
        goal_type = st.selectbox("Goal Type", ["Strength", "Weight", "Endurance", "Consistency", "Other"])
    with col2:
        status
