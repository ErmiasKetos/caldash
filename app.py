import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page

# Set page configuration
st.set_page_config(page_title="KETOS WB PMS", layout="wide")

# Sidebar navigation
st.sidebar.title("KETOS WB PMS")
menu = st.sidebar.radio(
    "Navigation",
    ["Probe Registration & Calibration", "Inventory Review"]
)

# Route to appropriate pages
if menu == "Probe Registration & Calibration":
    registration_calibration_page()
elif menu == "Inventory Review":
    inventory_review_page()
