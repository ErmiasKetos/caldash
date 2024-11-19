import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from threading import Thread

# Function to load inventory file
def load_inventory(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"])

# Function to save inventory file
def save_inventory(inventory, file_path, version_control=False):
    # Save the inventory file
    inventory.to_csv(file_path, index=False)
    if version_control:
        # Create a version-controlled backup
        backup_path = file_path.replace(".csv", f"_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        inventory.to_csv(backup_path, index=False)

# Function to save inventory to Google Drive (placeholder for integration)
def save_to_google_drive(inventory, file_path):
    # TODO: Implement Google Drive API for saving files
    pass

# Periodic save thread function
def periodic_save():
    while True:
        time.sleep(600)  # Every 10 minutes
        file_path = get_file_path()
        save_inventory(st.session_state["inventory"], file_path, version_control=True)

# Helper function to determine save location
def get_file_path():
    if st.session_state["save_location"] == "Local Computer":
        return "inventory.csv"
    elif st.session_state["save_location"] == "Google Drive":
        # Placeholder for Google Drive path
        return "inventory_google_drive.csv"

# Inventory review page
def inventory_review_page():
    # Initialize session state inventory
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = load_inventory(get_file_path())

    # Start periodic saving in a background thread
    if "save_thread" not in st.session_state:
        save_thread = Thread(target=periodic_save, daemon=True)
        save_thread.start()
        st.session_state["save_thread"] = save_thread

    # Display inventory
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state["inventory"])

    # Allow user to download the inventory
    st.markdown("<h3 style='color: #0071ba;'>Download Inventory</h3>", unsafe_allow_html=True)
    csv = st.session_state["inventory"].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Inventory as CSV",
        data=csv,
        file_name="inventory.csv",
        mime="text/csv",
    )
