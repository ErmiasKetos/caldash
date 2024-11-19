import streamlit as st
import pandas as pd
import os
import time
from threading import Thread

# Function to load inventory file
def load_inventory(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"])

# Function to save inventory file
def save_inventory(inventory, file_path):
    inventory.to_csv(file_path, index=False)

# Thread for periodic saving
def periodic_save(file_path):
    while True:
        time.sleep(600)  # 10 minutes
        save_inventory(st.session_state["inventory"], file_path)

def inventory_review_page():
    # Initialize session state inventory
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

    # File path for inventory
    file_path = "inventory.csv"

    # Load inventory from file
    if os.path.exists(file_path):
        st.session_state["inventory"] = load_inventory(file_path)

    # Start periodic saving in a background thread
    if "save_thread" not in st.session_state:
        save_thread = Thread(target=periodic_save, args=(file_path,), daemon=True)
        save_thread.start()
        st.session_state["save_thread"] = save_thread

    # Display inventory
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state["inventory"])

    # Add new probes manually
    st.markdown("<h3 style='color: #0071ba;'>Add New Probe to Inventory</h3>", unsafe_allow_html=True)
    with st.form(key="add_probe"):
        serial_number = st.text_input("Serial Number")
        probe_type = st.text_input("Probe Type")
        manufacturer = st.text_input("Manufacturer")
        ketos_part_number = st.text_input("KETOS Part Number")
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
        next_calibration = st.date_input("Next Calibration Date")
        status = st.selectbox("Status", ["Active", "Inactive", "Calibration Due"])
        submitted = st.form_submit_button("Add Probe")
        if submitted:
            new_row = {
                "Serial Number": serial_number,
                "Type": probe_type,
                "Manufacturer": manufacturer,
                "KETOS P/N": ketos_part_number,
                "Mfg P/N": manufacturer_part_number,
                "Next Calibration": next_calibration,
                "Status": status,
            }
            st.session_state["inventory"] = st.session_state["inventory"].append(new_row, ignore_index=True)
            save_inventory(st.session_state["inventory"], file_path)
            st.success("New probe added successfully!")

    # Allow user to download the inventory
    st.markdown("<h3 style='color: #0071ba;'>Download Inventory</h3>", unsafe_allow_html=True)
    csv = st.session_state["inventory"].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Inventory as CSV",
        data=csv,
        file_name="inventory.csv",
        mime="text/csv",
    )
