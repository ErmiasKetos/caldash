import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from src.inventory_review import save_inventory, get_file_path

def registration_calibration_page():
    # Initialize inventory in session state
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

    # Title
    st.markdown(
        f'<h1 style="font-family: Arial, sans-serif; font-size: 32px; color: #0071ba;">📋 Probe Registration & Calibration</h1>',
        unsafe_allow_html=True,
    )

    # General Section: Probe Information
    st.markdown('<h2 style="font-family: Arial; color: #333;">Probe Information</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
        ketos_part_number = st.text_input("KETOS Part Number")
        calibration_date = st.date_input("Calibration Date", datetime.today())

    # Serial Number Generation
    serial_number = f"{probe_type.split()[0]}_{datetime.today().strftime('%y%m%d%H%M%S')}"
    st.markdown(f"<b>Generated Serial Number:</b> {serial_number}", unsafe_allow_html=True)

    # Save Button
    if st.button("Save"):
        next_calibration = calibration_date + timedelta(days=365)  # Default 1 year
        new_row = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Next Calibration": next_calibration.strftime("%Y-%m-%d"),
            "Status": "Active",
        }
        # Append to session state and save
        st.session_state["inventory"] = st.session_state["inventory"].append(new_row, ignore_index=True)
        save_inventory(st.session_state["inventory"], get_file_path(), version_control=True)
        st.success("New probe registered successfully!")
