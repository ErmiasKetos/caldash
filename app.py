import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page

# Title of the App
st.set_page_config(page_title="Probe Management System", layout="wide")

# Sidebar Navigation
st.sidebar.title("KETOS WB PMS")
page = st.sidebar.radio(
    "Navigate",
    ["Probe Registration & Calibration", "Inventory Review"],
)

# App Navigation
if page == "Probe Registration & Calibration":
    registration_calibration_page()
elif page == "Inventory Review":
    inventory_review_page()
