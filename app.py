import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page

# Title of the App
st.set_page_config(page_title="Probe Management System", layout="wide")

# Sidebar Navigation
st.sidebar.title("CalMS")
page = st.sidebar.radio(
    "Navigate",
    ["Probe Registration & Calibration", "Inventory Review"],
)

# Shared Save Location Setting
if "save_location" not in st.session_state:
    st.session_state["save_location"] = st.radio(
        "Select where to save the inventory file:",
        ["Local Computer", "Google Drive"],
    )

# App Navigation
if page == "Probe Registration & Calibration":
    registration_calibration_page()
elif page == "Inventory Review":
    inventory_review_page()
