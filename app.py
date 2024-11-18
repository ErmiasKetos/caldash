import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Set the page layout
st.set_page_config(page_title="KETOS WB PMS", layout="wide")

# Add custom CSS for styling
def apply_custom_css():
    st.markdown("""
    <style>
    /* Sidebar styling */
    .css-1v3fvcr {
        background-color: #0071ba;
        color: white;
    }
    /* Section styling */
    .section-title {
        font-size: 18px;
        font-weight: bold;
        margin-top: 20px;
        border-bottom: 2px solid #0071ba;
        padding-bottom: 5px;
    }
    /* Input fields */
    .stTextInput, .stDateInput, .stSelectbox {
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    /* Page container */
    .main-container {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# Sidebar
st.sidebar.title("KETOS WB PMS")
menu = st.sidebar.radio(
    "Navigation",
    ["Probe Registration & Calibration", "Inventory Review", "QA/QC", "Audit Log", "Data Export"]
)

