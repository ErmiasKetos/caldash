# inventory_manager.py
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
                        "Last Modified", "Status Color", "Change Date"
                    ]
                    for col in required_columns:
                        if col not in df.columns:
                            if col in ['Entry Date', 'Last Modified', 'Change Date']:
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
                        "Last Modified", "Status Color", "Change Date"
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
