import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
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
            ph_data[f"{buffer_label}_control"] = st.text_input(
                f"{buffer_label} Control Number",
                key=f"ph_{idx}_control_number"
            )
            ph_data[f"{buffer_label}_exp"] = st.date_input(
                f"{buffer_label} Expiration Date",
                key=f"ph_{idx}_expiration"
            )
        with col2:
            ph_data[f"{buffer_label}_opened"] = st.date_input(
                f"{buffer_label} Date Opened",
                key=f"ph_{idx}_date_opened"
            )
            ph_data[f"{buffer_label}_initial"] = st.number_input(
                f"{buffer_label} Initial Measurement (pH)",
                value=0.0,
                key=f"ph_{idx}_initial"
            )
            ph_data[f"{buffer_label}_calibrated"] = st.number_input(
                f"{buffer_label} Calibrated Measurement (pH)",
                value=0.0,
                key=f"ph_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return ph_data

def render_do_calibration():
    """Render DO probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)
    do_data = {}

    # Temperature section
    st.markdown('<h4 style="font-family: Arial; color: #0071ba;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        do_data['temp_initial'] = st.number_input(
            "Initial Temperature (°C)",
            value=0.0,
            key="do_temp_initial"
        )
    with col2:
        do_data['temp_calibrated'] = st.number_input(
            "Calibrated Temperature (°C)",
            value=0.0,
            key="do_temp_calibrated"
        )

    # DO Calibration sections
    for idx, label in enumerate(["0% DO Calibration", "100% DO Calibration"]):
        st.markdown(
            f'<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label}</h4>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            do_data[f"do_{idx}_control"] = st.text_input(
                f"{label} Control Number",
                key=f"do_{idx}_control_number"
            )
            do_data[f"do_{idx}_exp"] = st.date_input(
                f"{label} Expiration Date",
                key=f"do_{idx}_expiration"
            )
        with col2:
            do_data[f"do_{idx}_opened"] = st.date_input(
                f"{label} Date Opened",
                key=f"do_{idx}_date_opened"
            )
            do_data[f"do_{idx}_initial"] = st.number_input(
                f"{label} Initial Measurement (%)",
                value=0.0,
                key=f"do_{idx}_initial"
            )
            do_data[f"do_{idx}_calibrated"] = st.number_input(
                f"{label} Calibrated Measurement (%)",
                value=0.0,
                key=f"do_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return do_data

def render_orp_calibration():
    """Render ORP probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)
    orp_data = {}

    col1, col2 = st.columns(2)
    with col1:
        orp_data['control_number'] = st.text_input("Control Number", key="orp_control_number")
        orp_data['expiration'] = st.date_input("Expiration Date", key="orp_expiration")
    with col2:
        orp_data['date_opened'] = st.date_input("Date Opened", key="orp_date_opened")
        orp_data['initial'] = st.number_input("Initial Measurement (mV)", value=0.0, key="orp_initial")
        orp_data['calibrated'] = st.number_input("Calibrated Measurement (mV)", value=0.0, key="orp_calibrated")
    return orp_data

def render_ec_calibration():
    """Render EC probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">EC Calibration</h3>', unsafe_allow_html=True)
    ec_data = {}

    for idx, label in enumerate(["84 μS/cm", "1413 μS/cm", "12.88 mS/cm"]):
        st.markdown(
            f'<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label} Calibration</h4>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            ec_data[f"ec_{idx}_control"] = st.text_input(
                f"{label} Control Number",
                key=f"ec_{idx}_control_number"
            )
            ec_data[f"ec_{idx}_exp"] = st.date_input(
                f"{label} Expiration Date",
                key=f"ec_{idx}_expiration"
            )
        with col2:
            ec_data[f"ec_{idx}_opened"] = st.date_input(
                f"{label} Date Opened",
                key=f"ec_{idx}_date_opened"
            )
            ec_data[f"ec_{idx}_initial"] = st.number_input(
                f"{label} Initial Measurement (μS/cm or mS/cm)",
                value=0.0,
                key=f"ec_{idx}_initial"
            )
            ec_data[f"ec_{idx}_calibrated"] = st.number_input(
                f"{label} Calibrated Measurement (μS/cm or mS/cm)",
                value=0.0,
                key=f"ec_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return ec_data

def registration_calibration_page():
    """Main page for probe registration and calibration"""
def registration_calibration_page():
    """Main page for probe registration and calibration"""
    # Initialize session state for inventory if not exists
    if 'inventory' not in st.session_state:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Status Color", "Change Date"
        ])

    # Title
    st.markdown(
        '<h1 style="font-family: Arial, sans-serif; font-size: 32px; color: #0071ba;">📋 Probe Registration & Calibration</h1>',
        unsafe_allow_html=True,
    )
    
    # Initialize form clearing mechanism
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

    # Reset form if previously submitted
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
        for key in ['manufacturer', 'manufacturer_part_number']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
        
    # Sidebar Drive Settings
    with st.sidebar:
        with st.expander("Google Drive Settings"):
            if 'drive_folder_id' in st.session_state:
                st.success(f"✅ Using folder ID: {st.session_state['drive_folder_id']}")
                if st.button("Test Folder Access"):
                    drive_manager = st.session_state.get('drive_manager')
                    if drive_manager and drive_manager.verify_folder_access(st.session_state['drive_folder_id']):
                        st.success("✅ Folder access verified!")
                        st.session_state['last_drive_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        st.error("❌ Could not access folder. Check permissions.")
            else:
                st.warning("⚠️ Drive folder not configured")

        # Debug information
        with st.expander("Debug Info"):
            st.write({
                "Drive Connected": 'drive_manager' in st.session_state,
                "Drive Folder": st.session_state.get('drive_folder_id', 'Not set'),
                "Records Count": len(st.session_state.inventory),
                "Last Save": st.session_state.get('last_save_time', 'Never'),
                "Last Drive Check": st.session_state.get('last_drive_check', 'Never')
            })

    # Probe Information Section
    st.markdown('<h2 style="font-family: Arial; color: #333;">Probe Information</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer", key="manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today(), key="manufacturing_date")
        manufacturer_part_number = st.text_input("Manufacturer Part Number", key="manufacturer_part_number")
    
    with col2:
        probe_type = st.selectbox(
            "Probe Type",
            ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"],
            key="probe_type"
        )
        ketos_part_number = st.selectbox(
            "KETOS Part Number",
            KETOS_PART_NUMBERS.get(probe_type, []),
            key="ketos_part_number"
        )
        calibration_date = st.date_input("Calibration Date", datetime.today(), key="calibration_date")

    # Generate Serial Number
    service_years = SERVICE_LIFE.get(probe_type, 2)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    serial_number = get_next_serial_number(probe_type, manufacturing_date)
    st.text(f"Generated Serial Number: {serial_number}")

    # Calibration Details Section
    st.markdown(
        """
        <div style="border: 2px solid #0071ba; padding: 20px; border-radius: 12px; margin-top: 20px;">
            <h2 style="font-family: Arial; color: #0071ba; text-align: center;">Calibration Details</h2>
        """,
        unsafe_allow_html=True,
    )

    # Render appropriate calibration form
    calibration_data = None
    if probe_type == "pH Probe":
        calibration_data = render_ph_calibration()
    elif probe_type == "DO Probe":
        calibration_data = render_do_calibration()
    elif probe_type == "ORP Probe":
        calibration_data = render_orp_calibration()
    elif probe_type == "EC Probe":
        calibration_data = render_ec_calibration()

    st.markdown('</div>', unsafe_allow_html=True)

# Save Button
    if st.button("Save Probe"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("Please fill in all required fields.")
            return

    try:
        with st.spinner("Saving probe data..."):
            # Verify Drive access before saving
            drive_status = False
            if 'drive_manager' in st.session_state and 'drive_folder_id' in st.session_state:
                drive_status = st.session_state.drive_manager.verify_folder_access(
                    st.session_state['drive_folder_id']
                )

            # Prepare probe data
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
                "Calibration Data": str(calibration_data)
            }

            # Add probe to inventory and save
            success = add_new_probe(probe_data)
            
            if success:
                st.success(f"✅ New probe {serial_number} registered successfully!")
                
                if drive_status:
                    save_success = st.session_state.drive_manager.save_to_drive(
                        st.session_state.inventory,
                        st.session_state.drive_folder_id
                    )
                    if save_success:
                        st.success("✅ Inventory updated and saved to Google Drive")
                        st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        st.warning("⚠️ Failed to save to Google Drive, but data is saved locally")
                else:
                    st.warning("⚠️ Inventory updated locally only. Google Drive not accessible.")

                # Mark form as submitted for clearing
                st.session_state.form_submitted = True
                # Wait a moment to show success messages
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to register probe")

    except Exception as e:
        logger.error(f"Error saving probe: {str(e)}")
        st.error(f"Error saving probe: {str(e)}")

if __name__ == "__main__":
    registration_calibration_page()
