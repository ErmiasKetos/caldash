import streamlit as st
import pandas as pd
import os
import threading
import time
from datetime import datetime, timedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Initialize Google Drive authentication
def authenticate_google_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Opens a browser window for user authentication
    drive = GoogleDrive(gauth)
    return drive

# Save inventory to Google Drive
def save_to_google_drive(file_name, drive):
    file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
    if file_list:
        file = file_list[0]
        file.SetContentFile(file_name)
        file.Upload()  # Update the file
    else:
        file = drive.CreateFile({'title': file_name})
        file.SetContentFile(file_name)
        file.Upload()  # Create a new file

# Periodic file updater
def periodic_save(file_name, save_location, drive=None):
    while True:
        time.sleep(600)  # 10 minutes
        if save_location == "Local Computer":
            st.session_state["inventory"].to_csv(file_name, index=False)
        elif save_location == "Google Drive":
            st.session_state["inventory"].to_csv(file_name, index=False)
            save_to_google_drive(file_name, drive)

# Streamlit app
def app():
    # Initialize inventory state
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.DataFrame(
            columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"]
        )

    # File save location
    save_location = st.radio("Where do you want to save the inventory file?", ["Local Computer", "Google Drive"])

    # Google Drive authentication
    drive = None
    if save_location == "Google Drive":
        st.write("Authenticating with Google Drive...")
        drive = authenticate_google_drive()
        st.success("Google Drive authenticated successfully!")

    # Inventory File Name
    file_name = "inventory.csv"

    # Run periodic updates in a separate thread
    if "thread_started" not in st.session_state:
        st.session_state["thread_started"] = True
        threading.Thread(
            target=periodic_save,
            args=(file_name, save_location, drive),
            daemon=True
        ).start()

    # App UI
    st.title("Probe Registration & Calibration")

    # Example user input
    manufacturer = st.text_input("Manufacturer")
    probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
    serial_number = f"{probe_type[:2]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Add new probe
    if st.button("Add Probe"):
        new_row = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": "123-456",
            "Mfg P/N": "789-101",
            "Next Calibration": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "Status": "Active",
        }
        st.session_state["inventory"] = st.session_state["inventory"].append(new_row, ignore_index=True)
        st.success(f"Probe {serial_number} added successfully!")

    # Save Button
    if st.button("Save Inventory"):
        if save_location == "Local Computer":
            st.session_state["inventory"].to_csv(file_name, index=False)
            st.success(f"Inventory saved locally as {file_name}")
        elif save_location == "Google Drive":
            st.session_state["inventory"].to_csv(file_name, index=False)
            save_to_google_drive(file_name, drive)
            st.success(f"Inventory saved to Google Drive as {file_name}")

    # Display Inventory Table
    st.write("Current Inventory:")
    st.dataframe(st.session_state["inventory"])
