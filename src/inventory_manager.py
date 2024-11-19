import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
from src.drive_manager import DriveManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BACKUP_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"
INVENTORY_FILENAME = "wbpms_inventory_2024.csv"

# Service life definitions
service_life = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

# Status color mapping
STATUS_COLORS = {
    'Instock': '#90EE90',  # Green
    'Shipped': '#ADD8E6',  # Light Blue
    'Scraped': '#FFB6C6'   # Red
}

def initialize_inventory():
    """Initialize or load existing inventory"""
    try:
        if 'inventory' not in st.session_state:
            logger.info("Initializing inventory...")
            # Try to load from Drive first
            if 'drive_manager' in st.session_state:
                df = st.session_state.drive_manager.load_inventory_from_drive(BACKUP_FOLDER_ID)
                if df is not None:
                    # Ensure all required columns exist
                    required_columns = [
                        "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                        "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                        "Last Modified", "Status Color"
                    ]
                    for col in required_columns:
                        if col not in df.columns:
                            if col in ['Entry Date', 'Last Modified']:
                                df[col] = datetime.now().strftime('%Y-%m-%d')
                            elif col == 'Status':
                                df[col] = 'Instock'
                            elif col == 'Status Color':
                                df[col] = STATUS_COLORS['Instock']
                            else:
                                df[col] = ''
                    
                    st.session_state.inventory = df
                    logger.info(f"Loaded existing inventory with {len(df)} records")
                else:
                    # Create new inventory if none exists
                    st.session_state.inventory = pd.DataFrame(columns=[
                        "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                        "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                        "Last Modified", "Status Color"
                    ])
                    logger.info("Created new inventory")
    except Exception as e:
        logger.error(f"Error initializing inventory: {str(e)}")
        st.error("Error initializing inventory. Please try refreshing the page.")

def get_next_serial_number(probe_type, manufacturing_date):
    """Generate next serial number based on existing inventory"""
    try:
        inventory = st.session_state.inventory
        
        # Filter existing serial numbers for this probe type
        existing_serials = inventory[inventory['Type'] == probe_type]['Serial Number'].tolist()
        
        if existing_serials:
            # Extract the highest sequence number
            sequence_numbers = [int(serial.split('_')[-1]) for serial in existing_serials]
            next_sequence = max(sequence_numbers) + 1
        else:
            next_sequence = 1
        
        # Generate new serial number
        expire_date = manufacturing_date + timedelta(days=service_life.get(probe_type, 1) * 365)
        expire_yymm = expire_date.strftime("%y%m")
        serial_number = f"{probe_type.split()[0]}_{expire_yymm}_{next_sequence:05d}"
        
        logger.info(f"Generated new serial number: {serial_number}")
        return serial_number
        
    except Exception as e:
        logger.error(f"Error generating serial number: {str(e)}")
        return None

def update_probe_status(serial_number, new_status):
    """Update probe status and last modified date"""
    try:
        if serial_number in st.session_state.inventory['Serial Number'].values:
            # Update the probe
            mask = st.session_state.inventory['Serial Number'] == serial_number
            st.session_state.inventory.loc[mask, 'Status'] = new_status
            st.session_state.inventory.loc[mask, 'Status Color'] = STATUS_COLORS.get(new_status)
            st.session_state.inventory.loc[mask, 'Last Modified'] = datetime.now().strftime('%Y-%m-%d')
            
            # Save changes to Drive
            if st.session_state.get('drive_manager'):
                if st.session_state.drive_manager.save_to_drive(
                    st.session_state.inventory, 
                    BACKUP_FOLDER_ID
                ):
                    logger.info(f"Updated status of {serial_number} to {new_status}")
                    return True
                else:
                    logger.error(f"Failed to save status update to Drive for {serial_number}")
                    return False
            
        return False
    except Exception as e:
        logger.error(f"Error updating probe status: {str(e)}")
        return False

def add_new_probe(probe_data):
    """Add a new probe to the inventory"""
    try:
        # Create new row with current date
        probe_data['Entry Date'] = datetime.now().strftime('%Y-%m-%d')
        probe_data['Last Modified'] = datetime.now().strftime('%Y-%m-%d')
        probe_data['Status'] = 'Instock'
        probe_data['Status Color'] = STATUS_COLORS['Instock']
        
        # Add to inventory
        new_row_df = pd.DataFrame([probe_data])
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_row_df], ignore_index=True)
        
        # Save to Drive
        if st.session_state.get('drive_manager'):
            if st.session_state.drive_manager.save_to_drive(
                st.session_state.inventory, 
                BACKUP_FOLDER_ID
            ):
                logger.info(f"Added new probe: {probe_data['Serial Number']}")
                return True
            else:
                logger.error("Failed to save new probe to Drive")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error adding new probe: {str(e)}")
        return False

def get_filtered_inventory(status_filter="All"):
    """Get filtered inventory based on status"""
    try:
        if status_filter == "All":
            return st.session_state.inventory
        return st.session_state.inventory[st.session_state.inventory['Status'] == status_filter]
    except Exception as e:
        logger.error(f"Error filtering inventory: {str(e)}")
        return pd.DataFrame()

def style_inventory_dataframe(df):
    """Apply color styling to inventory dataframe"""
    try:
        def color_rows(row):
            return [f"background-color: {row['Status Color']}"] * len(row)
        
        return df.style.apply(color_rows, axis=1)
    except Exception as e:
        logger.error(f"Error styling dataframe: {str(e)}")
        return df
