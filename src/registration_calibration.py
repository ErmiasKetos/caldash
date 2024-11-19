import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from .drive_manager import save_inventory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Autofill options for KETOS Part Number
ketos_part_numbers = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes
service_life = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

def registration_calibration_page():
    """Main page for probe registration and calibration"""
    if 'inventory' not in st.session_state:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status"
        ])

    # Title
    st.markdown(
        f'<h1 style="font-family: Arial; font-size: 32px; color: #0071ba;">📋 Probe Registration & Calibration</h1>',
        unsafe_allow_html=True,
    )

    # General Section: Probe Information
    st.markdown('<h2 style="font-family: Arial; color: #333;">Probe Information</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer", key="manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today(), key="manufacturing_date")
        manufacturer_part_number = st.text_input("Manufacturer Part Number", key="manufacturer_part_number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"], key="probe_type")
        ketos_part_number = st.selectbox(
            "KETOS Part Number",
            ketos_part_numbers.get(probe_type, []),
            key="ketos_part_number"
        )
        calibration_date = st.date_input("Calibration Date", datetime.today(), key="calibration_date")

    # Serial Number Generation
    service_years = service_life.get(probe_type, 1)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    expire_yymm = expire_date.strftime("%y%m")
    serial_number = f"{probe_type.split()[0]}_{expire_yymm}_{len(st.session_state.inventory) + 1:05d}"
    st.text(f"Generated Serial Number: {serial_number}")

    # Save Button
    if st.button("Save"):
        if not manufacturer or not manufacturer_part_number or not ketos_part_number:
            st.error("Please fill in all required fields.")
        else:
            try:
                # Create new row
                next_calibration = calibration_date + timedelta(days=365)
                new_row = {
                    "Serial Number": serial_number,
                    "Type": probe_type,
                    "Manufacturer": manufacturer,
                    "KETOS P/N": ketos_part_number,
                    "Mfg P/N": manufacturer_part_number,
                    "Next Calibration": next_calibration.strftime("%Y-%m-%d"),
                    "Status": "Active",
                }
                
                # Create a single-row DataFrame for the new entry
                new_row_df = pd.DataFrame([new_row])

                # Append the new row to the inventory
                st.session_state["inventory"] = pd.concat([st.session_state["inventory"], new_row_df], ignore_index=True)

                # Save inventory with the specified file name
                inventory_file_name = "wbpms_inventory_2024.csv"
                save_inventory(st.session_state["inventory"], inventory_file_name, version_control=True)

                st.success("New probe registered successfully!")
                
                # File paths
                local_file_path = "wbpms_inventory_2024.csv"
                drive_folder_id = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

                # Try saving to Google Drive and locally
                try:
                    if save_inventory(
                        inventory=st.session_state["inventory"],
                        file_path=local_file_path,
                        drive_manager=st.session_state.get("drive_manager"),  # Ensure DriveManager is initialized
                    ):
                        st.success("✅ New probe registered and saved to Google Drive successfully!")
                    else:
                        st.warning("⚠️ Probe registered and saved locally, but Google Drive save failed.")
                        st.info("Please check Google Drive settings in the sidebar.")
                except Exception as e:
                    # Fallback to local save only
                    try:
                        st.session_state["inventory"].to_csv(local_file_path, index=False)
                        st.warning(f"⚠️ Probe registered and saved locally, but Google Drive save failed: {str(e)}")
                        st.info("Please check Google Drive settings in the sidebar.")
                    except Exception as local_error:
                        st.error(f"❌ Failed to save locally as well: {local_error}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
