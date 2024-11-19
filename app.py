import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Probe Management System", layout="wide")

# Initialize global inventory in session state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = pd.DataFrame(
        columns=[
            "Serial Number",
            "Type",
            "Manufacturer",
            "KETOS P/N",
            "Mfg P/N",
            "Next Calibration",
            "Status",
        ]
    )

# Sidebar for navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Page", ["Registration & Calibration", "Inventory Review"])

if menu == "Registration & Calibration":
    registration_calibration_page()
elif menu == "Inventory Review":
    inventory_review_page()
