import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from threading import Thread
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Google Drive Authentication
def authenticate_google_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("credentials.json")
    else:
        gauth.Authorize()
    return GoogleDrive(gauth)

# Function to save inventory to Google Drive
def save_to_google_drive(file_path, folder_id):
    drive = authenticate_google_drive()
    file = drive.CreateFile({"parents": [{"id": folder_id}]})
    file.SetContentFile(file_path)
    file.Upload()

# Function to load inventory file
def load_inventory(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"])

# Function to save inventory file locally
def save_inventory(inventory, file_path, version_control=False):
    inventory.to_csv(file_path, index=False)
    if version_control:
        backup_path = file_path.replace(".csv", f"_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        inventory.to_csv(backup_path, index=False)

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
        return "inventory_google_drive.csv"

def inventory_review_page():
    """Display and manage inventory"""
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    
    # Initialize inventory if needed
    initialize_inventory()
    
    # Add status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Instock", "Shipped", "Scraped"]
    )
    
    # Filter inventory based on selection
    filtered_inventory = st.session_state.inventory
    if status_filter != "All":
        filtered_inventory = filtered_inventory[filtered_inventory['Status'] == status_filter]
    
    # Display inventory with status colors
    def color_rows(row):
        return [f"background-color: {row['Status Color']}"] * len(row)
    
    st.dataframe(
        filtered_inventory.style.apply(color_rows, axis=1),
        height=400
    )
    
    # Status update section
    st.markdown("### Update Probe Status")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_probe = st.selectbox(
            "Select Probe",
            st.session_state.inventory['Serial Number'].tolist()
        )
    
    with col2:
        new_status = st.selectbox(
            "New Status",
            ["Instock", "Shipped", "Scraped"],
            index=0
        )
    
    if st.button("Update Status"):
        if st.button("Confirm Status Change"):
            if update_probe_status(selected_probe, new_status):
                st.success(f"Updated status of {selected_probe} to {new_status}")
            else:
                st.error("Failed to update status")

    # Download button
    csv = filtered_inventory.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Inventory as CSV",
        data=csv,
        file_name="inventory.csv",
        mime="text/csv",
    )
