import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import json
from .inventory_manager import BACKUP_FOLDER_ID
from .drive_manager import DriveManager
from .inventory_manager import save_inventory, STATUS_COLORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_searchable_probes():
    """Get list of searchable probes with their details for autocomplete"""
    if 'inventory' not in st.session_state:
        return []
    
    inventory_df = st.session_state.inventory
    searchable_probes = []
    
    for _, row in inventory_df.iterrows():
        probe_info = {
            'serial': row['Serial Number'],
            'type': row['Type'],
            'manufacturer': row['Manufacturer'],
            'status': row['Status'],
            'display': f"{row['Serial Number']} - {row['Type']} ({row['Status']})",
            'search_text': f"{row['Serial Number']} {row['Type']} {row['Manufacturer']} {row['Status']}"
        }
        searchable_probes.append(probe_info)
    
    return searchable_probes

def render_autocomplete_search():
    """Render autocomplete search bar for probes with real-time suggestions"""
    probes = get_searchable_probes()
    
    # Create a container for the search section
    search_container = st.container()
    
    with search_container:
        st.markdown("""
            <style>
                .search-container {
                    margin-bottom: 1rem;
                }
                .search-input {
                    padding: 0.5rem;
                    border-radius: 4px;
                    border: 1px solid #ddd;
                    width: 100%;
                }
                .suggestion-box {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-top: 4px;
                    max-height: 200px;
                    overflow-y: auto;
                }
                .suggestion-item {
                    padding: 8px 12px;
                    cursor: pointer;
                    border-bottom: 1px solid #eee;
                }
                .suggestion-item:hover {
                    background-color: #f0f2f6;
                }
                .status-badge {
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.8em;
                    margin-left: 8px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Initialize session state for search
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'selected_probe' not in st.session_state:
            st.session_state.selected_probe = None
        if 'show_suggestions' not in st.session_state:
            st.session_state.show_suggestions = False

        # Search input with autocomplete
        col1, col2 = st.columns([5, 1])
        with col1:
            search_query = st.text_input(
                "🔍 Search Probe",
                value=st.session_state.search_query,
                key="probe_search",
                placeholder="Type to search by Serial Number, Type, or Manufacturer...",
            ).strip()
        with col2:
            if st.button("Clear", key="clear_search"):
                st.session_state.search_query = ""
                st.session_state.selected_probe = None
                st.session_state.show_suggestions = False
                st.rerun()

        # Update session state
        st.session_state.search_query = search_query
        
        # Filter probes based on search query
        if search_query:
            filtered_probes = [
                probe for probe in probes
                if search_query.lower() in probe['search_text'].lower()
            ]
            
            # Show suggestions
            if filtered_probes:
                st.markdown("#### Matching Probes")
                for probe in filtered_probes[:5]:  # Limit to 5 suggestions
                    status_color = {
                        'Instock': '#90EE90',
                        'Calibrated': '#98FB98',
                        'Shipped': '#ADD8E6',
                        'Scraped': '#FFB6C6'
                    }.get(probe['status'], '#FFFFFF')
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f"""
                            <div style="
                                padding: 8px;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                margin-bottom: 4px;
                                background-color: white;
                            ">
                                <span style="font-weight: bold;">{probe['serial']}</span><br/>
                                <span style="color: #666;">{probe['type']} - {probe['manufacturer']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with col2:
                        if st.button("Select", key=f"select_{probe['serial']}"):
                            st.session_state.selected_probe = probe['serial']
                            st.session_state.search_query = probe['display']
                            st.rerun()
            else:
                st.info("No matching probes found.")

        return st.session_state.get('selected_probe')

def render_ph_calibration():
    """Render pH probe calibration form."""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">pH Calibration</h3>', unsafe_allow_html=True)
    ph_data = {}
    for idx, (buffer_label, color) in enumerate([("pH 7", "#f8f1f1"), ("pH 4", "#e8f8f2"), ("pH 10", "#e8f0f8")]):
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{buffer_label} Buffer</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            ph_data[f"{buffer_label}_control"] = st.text_input(f"{buffer_label} Control Number", key=f"ph_{idx}_control_number")
            ph_data[f"{buffer_label}_exp"] = st.date_input(f"{buffer_label} Expiration Date", key=f"ph_{idx}_expiration")
            ph_data[f"{buffer_label}_opened"] = st.date_input(f"{buffer_label} Date Opened", key=f"ph_{idx}_date_opened")
        with col2:
            
            ph_data[f"{buffer_label}_initial"] = st.number_input(f"{buffer_label} Initial Measurement (pH)", value=0.0, key=f"ph_{idx}_initial")
            ph_data[f"{buffer_label}_calibrated"] = st.number_input(f"{buffer_label} Calibrated Measurement (pH)", value=0.0, key=f"ph_{idx}_calibrated")
            ph_data[f"{buffer_label}_initial_mv"] = st.number_input(f"{buffer_label} Initial mV", value=0.0, key=f"ph_{idx}_initial_mv")
        st.markdown('</div>', unsafe_allow_html=True)
    return ph_data

def render_do_calibration():
    """Render DO probe calibration form."""
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

def render_orp_calibration():
    """Render ORP probe calibration form."""
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
    """Render EC probe calibration form."""
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
            ec_data[f"ec_{idx}_control"] = st.text_input(f"{label} Control Number", key=f"ec_{idx}_control_number")
            ec_data[f"ec_{idx}_exp"] = st.date_input(f"{label} Expiration Date", key=f"ec_{idx}_expiration")
        with col2:
            ec_data[f"ec_{idx}_opened"] = st.date_input(f"{label} Date Opened", key=f"ec_{idx}_date_opened")
            ec_data[f"ec_{idx}_initial"] = st.number_input(f"{label} Initial Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_initial")
            ec_data[f"ec_{idx}_calibrated"] = st.number_input(f"{label} Calibrated Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)
    return ec_data

def render_calibration_form(probe_type):
    """Render appropriate calibration form based on the probe type."""
    if probe_type == "pH Probe":
        return render_ph_calibration()
    elif probe_type == "DO Probe":
        return render_do_calibration()
    elif probe_type == "ORP Probe":
        return render_orp_calibration()
    elif probe_type == "EC Probe":
        return render_ec_calibration()
    return {}

def find_probe(serial_number):
    """Find a probe in the inventory by serial number."""
    if 'inventory' not in st.session_state:
        return None
    
    inventory_df = st.session_state.inventory
    probe = inventory_df[inventory_df['Serial Number'] == serial_number]
    return probe.iloc[0] if not probe.empty else None

def update_probe_calibration(serial_number, calibration_data):
    """Update probe calibration data in the inventory."""
    try:
        # Debug print statements
        st.write("Debug: Starting calibration save...")
        st.write(f"Debug: Serial Number: {serial_number}")
        
        inventory_df = st.session_state.inventory
        st.write(f"Debug: Found inventory with {len(inventory_df)} records")
        
        # Check if serial number exists
        if serial_number not in inventory_df['Serial Number'].values:
            st.error(f"Serial number {serial_number} not found in inventory")
            return False
            
        probe_idx = inventory_df[inventory_df['Serial Number'] == serial_number].index[0]
        st.write(f"Debug: Found probe at index {probe_idx}")
        
        # Try to convert calibration data to JSON
        try:
            json_data = json.dumps(calibration_data)
            st.write("Debug: Successfully converted calibration data to JSON")
        except Exception as json_error:
            st.error(f"Failed to convert calibration data to JSON: {str(json_error)}")
            return False
        
        # Update all fields
        try:
            inventory_df.at[probe_idx, 'Calibration Data'] = json_data
            inventory_df.at[probe_idx, 'Last Modified'] = datetime.now().strftime("%Y-%m-%d")
            inventory_df.at[probe_idx, 'Next Calibration'] = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
            inventory_df.at[probe_idx, 'Status'] = "Calibrated"
            st.write("Debug: Successfully updated DataFrame")
        except Exception as df_error:
            st.error(f"Failed to update DataFrame: {str(df_error)}")
            return False
        
        # Update session state
        try:
            st.session_state.inventory = inventory_df
            st.write("Debug: Updated session state inventory")
        except Exception as session_error:
            st.error(f"Failed to update session state: {str(session_error)}")
            return False
        
        # Try to save locally
        try:
            save_success = save_inventory(st.session_state.inventory)
            st.write(f"Debug: Local save result: {save_success}")
            if not save_success:
                st.error("Failed to save to local inventory")
                return False
        except Exception as save_error:
            st.error(f"Error during local save: {str(save_error)}")
            return False
        
        # Try to save to Google Drive
        if 'drive_manager' in st.session_state and 'drive_folder_id' in st.session_state:
            try:
                st.write("Debug: Attempting Google Drive save")
                drive_success = st.session_state.drive_manager.save_to_drive(
                    st.session_state.inventory,
                    st.session_state.get('drive_folder_id', BACKUP_FOLDER_ID)
                )
                st.write(f"Debug: Google Drive save result: {drive_success}")
                
                if drive_success:
                    st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.write("Debug: Successfully completed all save operations")
                    return True
                else:
                    st.error("Failed to save to Google Drive")
                    return False
            except Exception as drive_error:
                st.error(f"Error during Google Drive save: {str(drive_error)}")
                return False
        
        return save_success

    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False


def calibration_page():
    """Main page for probe calibration"""
    st.markdown('<h1 style="font-family: Arial; color: #0071ba;">🔍 Probe Calibration</h1>', unsafe_allow_html=True)

    # Autocomplete search
    selected_serial = render_autocomplete_search()
    
    if selected_serial:
        probe = find_probe(selected_serial)
        
        if probe is None:
            st.error("❌ Probe not found in inventory. Please check the serial number.")
            return
        
        # Display probe information
        st.markdown("### Probe Details")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Type:** {probe['Type']}")
            st.write(f"**Manufacturer:** {probe['Manufacturer']}")
            st.write(f"**KETOS P/N:** {probe['KETOS P/N']}")
        with col2:
            st.write(f"**Mfg P/N:** {probe['Mfg P/N']}")
            st.write(f"**Status:** {probe['Status']}")
            st.write(f"**Entry Date:** {probe['Entry Date']}")
        
        # Check probe status
        if probe['Status'] in ['Calibrated', 'Shipped']:
            st.warning(f"⚠️ This probe was already calibrated on {probe['Last Modified']} " +
                      f"and is currently {probe['Status']}. No further calibration is allowed.")
            
            # Display existing calibration data in read-only mode
            if 'Calibration Data' in probe and probe['Calibration Data']:
                st.markdown("### Previous Calibration Data")
                populate_calibration_form(probe['Type'], probe['Calibration Data'])
                
        elif probe['Status'] != 'Instock':
            st.error("❌ Only probes with 'Instock' status can be calibrated.")
            
        else:
            # Calibration Date
            calibration_date = st.date_input("Calibration Date", datetime.today())
            
            # Render calibration form based on probe type
            calibration_data = render_calibration_form(probe['Type'])
        
            # Save calibration data
            if st.button("Save Calibration"):
                with st.spinner("Saving calibration data..."):
                    calibration_data['calibration_date'] = calibration_date.strftime("%Y-%m-%d")
                    success = update_probe_calibration(selected_serial, calibration_data)
                    
                    if success:
                        st.success(f"✅ Calibration data saved successfully for probe {selected_serial}!")
                        
                        # Show save status
                        if 'drive_manager' in st.session_state:
                            st.success("✅ Inventory updated in Google Drive")
                            st.success(f"Last saved: {st.session_state.get('last_save_time', 'Unknown')}")
                        else:
                            st.warning("⚠️ Google Drive not configured. Data saved locally only.")
                        
                        time.sleep(1)  # Delay for user feedback
                        st.rerun()
                    else:
                        st.error("❌ Failed to save calibration data. Please try again.")

    # Add Drive settings in sidebar
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

if __name__ == "__main__":
    calibration_page()
