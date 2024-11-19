import streamlit as st
import pandas as pd
import os
import threading
import time
from datetime import datetime, timedelta

# Periodic file updater
def periodic_save(file_name):
    while True:
        time.sleep(600)  # 10 minutes
        if "inventory" in st.session_state:
            st.session_state["inventory"].to_csv(file_name, index=False)

# Streamlit app
def app():
    # Initialize inventory state
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.DataFrame(
            columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"]
        )

    # Inventory File Name
    file_name = "inventory.csv"

    # Run periodic updates in a separate thread
    if "thread_started" not in st.session_state:
        st.session_state["thread_started"] = True
        threading.Thread(
            target=periodic_save,
            args=(file_name,),
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
        st.session_state["inventory"].to_csv(file_name, index=False)
        st.success(f"Inventory saved locally as {file_name}")

    # Display Inventory Table
    st.write("Current Inventory:")
    st.dataframe(st.session_state["inventory"])
