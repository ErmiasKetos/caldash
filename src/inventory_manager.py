import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time
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
        if 'inventory' not in st.session_state or st.session_state.inventory.empty:
            if 'drive_manager' in st.session_state:
                # Try to load from Drive
                try:
                    file_list = st.session_state.drive_manager.service.files().list(
                        q=f"name='{INVENTORY_FILENAME}' and '{BACKUP_FOLDER_ID}' in parents",
                        spaces='drive'
                    ).execute()
                    
                    if file_list.get('files'):
                        file_id = file_list['files'][0]['id']
                        df = st.session_state.drive_manager.load_file_from_drive(file_id)
                        if df is not None:
                            st.session_state.inventory = df
                            logger.info(f"Loaded inventory from Drive: {len(df)} records")
                            return
                except Exception as e:
                    logger.error(f"Error loading from Drive: {str(e)}")
            
            # Create new inventory if loading failed
            st.session_state.inventory = pd.DataFrame(columns=[
                "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                "Last Modified", "Status Color", "Change Date"
            ])
            logger.info("Created new inventory")
    except Exception as e:
        logger.error(f"Error initializing inventory: {str(e)}")
        st.error("Error initializing inventory. Please try refreshing the page.")

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
            return ['background-color: {}'.format(row['Status Color']) for _ in row]
        return df.style.apply(color_rows, axis=1)
    except Exception as e:
        logger.error(f"Error styling dataframe: {str(e)}")
        return df

def save_inventory(inventory_df, version_control=True):
    """Save inventory with versioning"""
    try:
        # Save main file
        inventory_df.to_csv(INVENTORY_FILENAME, index=False)
        
        # Version control backup every 5 days
        if version_control and datetime.now().day % 5 == 0:
            backup_filename = f"inventory_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            inventory_df.to_csv(backup_filename, index=False)
            
            # Save backup to Drive if available
            if 'drive_manager' in st.session_state:
                st.session_state.drive_manager.save_to_drive(
                    backup_filename,
                    BACKUP_FOLDER_ID
                )
        
        # Save to Drive
        if 'drive_manager' in st.session_state:
            st.session_state.drive_manager.save_to_drive(
                INVENTORY_FILENAME,
                BACKUP_FOLDER_ID
            )
        
        return True
    except Exception as e:
        logger.error(f"Error saving inventory: {str(e)}")
        return False

def update_probe_status(serial_number, new_status):
    """Update probe status and metadata"""
    try:
        if serial_number in st.session_state.inventory['Serial Number'].values:
            mask = st.session_state.inventory['Serial Number'] == serial_number
            st.session_state.inventory.loc[mask, 'Status'] = new_status
            st.session_state.inventory.loc[mask, 'Status Color'] = STATUS_COLORS[new_status]
            st.session_state.inventory.loc[mask, 'Change Date'] = datetime.now().strftime('%Y-%m-%d')
            st.session_state.inventory.loc[mask, 'Last Modified'] = datetime.now().strftime('%Y-%m-%d')
            
            # Save changes
            return save_inventory(st.session_state.inventory)
        return False
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return False

def get_next_serial_number(probe_type, manufacturing_date):
    """Generate sequential serial number"""
    try:
        existing_serials = st.session_state.inventory[
            st.session_state.inventory['Type'] == probe_type
        ]['Serial Number'].tolist()
        
        if existing_serials:
            sequence_numbers = [
                int(serial.split('_')[-1])
                for serial in existing_serials
            ]
            next_sequence = max(sequence_numbers) + 1
        else:
            next_sequence = 1
        
        expire_date = manufacturing_date + timedelta(days=365 * 2)  # 2-year default
        expire_yymm = expire_date.strftime("%y%m")
        return f"{probe_type.split()[0]}_{expire_yymm}_{next_sequence:05d}"
        
    except Exception as e:
        logger.error(f"Error generating serial number: {str(e)}")
        return None

def add_new_probe(probe_data):
    """Add a new probe to the inventory"""
    try:
        # Add metadata
        probe_data['Entry Date'] = datetime.now().strftime('%Y-%m-%d')
        probe_data['Last Modified'] = datetime.now().strftime('%Y-%m-%d')
        probe_data['Change Date'] = datetime.now().strftime('%Y-%m-%d')
        probe_data['Status'] = 'Instock'
        probe_data['Status Color'] = STATUS_COLORS['Instock']
        
        # Create new row
        new_row_df = pd.DataFrame([probe_data])
        
        # Append to inventory
        st.session_state.inventory = pd.concat(
            [st.session_state.inventory, new_row_df],
            ignore_index=True
        )
        
        # Save changes
        return save_inventory(st.session_state.inventory)
    except Exception as e:
        logger.error(f"Error adding new probe: {str(e)}")
        return False

# Start periodic save thread
def start_periodic_save():
    def periodic_save_task():
        while True:
            time.sleep(600)  # 10 minutes
            if 'inventory' in st.session_state:
                save_inventory(st.session_state.inventory)
    
    import threading
    save_thread = threading.Thread(target=periodic_save_task, daemon=True)
    save_thread.start()
