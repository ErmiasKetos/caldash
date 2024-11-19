import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import time  # Added for delay functionality
from .drive_manager import DriveManager
from .inventory_manager import (
    add_new_probe,
    get_next_serial_number,
    save_inventory,
    STATUS_COLORS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Autofill options for KETOS Part Number
KETOS_PART_NUMBERS = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes (in years)
SERVICE_LIFE = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

# Add Status Colors definition
STATUS_COLORS = {
    'Instock': '#90EE90',  # Green
    'Shipped': '#ADD8E6',  # Light Blue
    'Scraped': '#FFB6C6'   # Red
}

# Function to render calibration forms
def render_ph_calibration():
    """Render pH probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">pH Calibration</h3>', unsafe_allow_html=True)
    ph_data = {}

    for idx, (buffer_label, color) in enumerate([("pH 4", "#f8f1f1"), ("pH 7", "#e8f8f2"), ("pH 10", "#e8f0f8")]):
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{buffer_label} Buffer</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            ph_data[f"{buffer_label}_control"] = st.text_input(f"{buffer_label} Control Number", key=f"ph_{idx}_control_number")
            ph_data[f"{buffer_label}_exp"] = st.date_input(f"{buffer_label} Expiration Date", key=f"ph_{idx}_expiration")
        with col2:
            ph_data[f"{buffer_label}_opened"] = st.date_input(f"{buffer_label} Date Opened", key=f"ph_{idx}_date_opened")
            ph_data[f"{buffer_label}_initial"] = st.number_input(f"{buffer_label} Initial Measurement (pH)", value=0.0, key=f"ph_{idx}_initial")
            ph_data[f"{buffer_label}_calibrated"] = st.number_input(f"{buffer_label} Calibrated Measurement (pH)", value=0.0, key=f"ph_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)
    return ph_data


def render_do_calibration():
    """Render DO probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)
    do_data = {}

    st.markdown('<h4 style="font-family: Arial; color: #0071ba;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        do_data['temp_initial'] = st.number_input("Initial Temperature (°C)", value=0.0, key="do_temp_initial")
    with col2:
        do_data['temp_calibrated'] = st.number_input("Calibrated Temperature (°C)", value=0.0, key="do_temp_calibrated")

    for idx, label in enumerate(["0% DO Calibration", "100% DO Calibration"]):
        st.markdown(
            f'<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label}</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            do_data[f"do_{idx}_control"] = st.text_input(f"{label} Control Number", key=f"do_{idx}_control_number")
            do_data[f"do_{idx}_exp"] = st.date_input(f"{label} Expiration Date", key=f"do_{idx}_expiration")
        with col2:
            do_data[f"do_{idx}_opened"] = st.date_input(f"{label} Date Opened", key=f"do_{idx}_date_opened")
            do_data[f"do_{idx}_initial"] = st.number_input(f"{label} Initial Measurement (%)", value=0.0, key=f"do_{idx}_initial")
            do_data[f"do_{idx}_calibrated"] = st.number_input(f"{label} Calibrated Measurement (%)", value=0.0, key=f"do_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)
    return do_data


def render_calibration_form(probe_type):
    """Render appropriate calibration form based on the probe type"""
    if probe_type == "pH Probe":
        return render_ph_calibration()
    elif probe_type == "DO Probe":
        return render_do_calibration()
    elif probe_type == "ORP Probe":
        return render_orp_calibration()
    elif probe_type == "EC Probe":
        return render_ec_calibration()
    return {}


def load_inventory_from_drive():
    """Load the inventory CSV from Google Drive into the app's session state."""
    try:
        drive_manager = st.session_state.get("drive_manager")
        folder_id = st.session_state.get("drive_folder_id")

        if drive_manager and folder_id:
            file_content = drive_manager.download_inventory_csv(folder_id)
            inventory_df = pd.read_csv(file_content)
            st.session_state.inventory = inventory_df
            return True
        else:
            st.warning("⚠️ Google Drive is not configured. Cannot fetch the inventory.")
            return False
    except Exception as e:
        logger.error(f"Error loading inventory from Google Drive: {e}")
        st.error("❌ Failed to load inventory. Please check your Google Drive settings.")
        return False


def registration_calibration_page():
    """Main page for probe registration and calibration"""
    # Initialize inventory
    if 'inventory' not in st.session_state:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Status Color", "Change Date"
        ])

    # Sidebar for Drive settings
    with st.sidebar:
        st.markdown("### Google Drive Settings")
        if 'drive_folder_id' in st.session_state:
            st.success(f"✅ Using folder ID: {st.session_state['drive_folder_id']}")
            if st.button("Test Folder Access"):
                drive_manager = st.session_state.get('drive_manager')
                if drive_manager and drive_manager.verify_folder_access(st.session_state['drive_folder_id']):
                    st.success("✅ Folder access verified!")
                else:
                    st.error("❌ Could not access folder. Check permissions.")

            if st.button("Upload or Update Inventory"):
                if load_inventory_from_drive():
                    st.success("✅ Inventory updated successfully from Google Drive!")
                else:
                    st.error("❌ Failed to update inventory. Please check your settings.")
        else:
            st.warning("⚠️ Google Drive is not configured.")

    # Title
    st.markdown('<h1 style="font-family: Arial; color: #0071ba;">📋 Probe Registration & Calibration</h1>', unsafe_allow_html=True)

    # Automatic inventory update on login
    if not st.session_state.get("inventory_loaded"):
        if load_inventory_from_drive():
            st.success("✅ Inventory loaded successfully from Google Drive!")
            st.session_state["inventory_loaded"] = True
        else:
            st.warning("⚠️ Inventory could not be loaded automatically. Please use the 'Upload or Update Inventory' button.")

    # Input Fields
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
        ketos_part_number = st.selectbox("KETOS Part Number", KETOS_PART_NUMBERS.get(probe_type, []))
        calibration_date = st.date_input("Calibration Date", datetime.today())

    # Generate Serial Number
    service_years = SERVICE_LIFE.get(probe_type, 2)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    serial_number = get_next_serial_number(probe_type, manufacturing_date)
    st.text(f"Generated Serial Number: {serial_number}")

    # Render Calibration Form
    calibration_data = render_calibration_form(probe_type)

    # Save Button
    if st.button("Save Probe"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("Please fill in all required fields.")
            return

        # Prepare and save probe data
        probe_data = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Next Calibration": (calibration_date + timedelta(days=365)).strftime("%Y-%m-%d"),
            "Status": "Instock",
            "Entry Date": datetime.now().strftime("%Y-%m-%d"),
            "Last Modified": datetime.now().strftime("%Y-%m-%d"),
            "Change Date": datetime.now().strftime("%Y-%m-%d"),
            "Calibration Data": calibration_data
        }

        success = add_new_probe(probe_data)
        if success:
            st.success(f"✅ Probe {serial_number} saved successfully!")
            if 'drive_manager' in st.session_state and 'drive_folder_id' in st.session_state:
                if st.session_state.drive_manager.save_to_drive(st.session_state.inventory, st.session_state.drive_folder_id):
                    st.success("✅ Inventory saved to Google Drive.")
                    st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    st.warning("⚠️ Failed to save to Google Drive. Data saved locally.")
            else:
                st.warning("⚠️ Google Drive not configured. Data saved locally.")
            time.sleep(1)  # Delay for user feedback
            st.rerun()
        else:
            st.error("❌ Failed to save probe.")

if __name__ == "__main__":
    registration_calibration_page()
