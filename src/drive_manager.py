import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVENTORY_FILENAME = "wbpms_inventory_2024.csv"
BACKUP_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

class DriveManager:
    """Manages Google Drive operations"""
    def __init__(self):
        self.service = None
        self.credentials = None

    def authenticate(self, credentials):
        """Set up Google Drive service with provided credentials"""
        try:
            self.credentials = credentials
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Drive service authenticated successfully")
            return True
        except Exception as e:
            logger.error(f"Drive authentication failed: {str(e)}")
            st.error(f"Drive authentication failed: {str(e)}")
            return False

    def verify_folder_access(self, folder_id):
        """Verify if the folder exists and is accessible"""
        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return False

            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, permissions"
            ).execute()

            logger.info(f"Successfully verified access to folder: {folder.get('name', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify folder access: {str(e)}")
            return False

    def save_to_drive(self, file_path, drive_folder_id):
        """Save file to Google Drive in specified folder"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            if not self.service:
                logger.error("Drive service not initialized")
                return False

            # Verify folder access first
            if not self.verify_folder_access(drive_folder_id):
                logger.error(f"Cannot access folder: {drive_folder_id}")
                return False

            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [drive_folder_id],
                'mimeType': 'text/csv'
            }

            media = MediaFileUpload(
                file_path,
                mimetype='text/csv',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name'
            ).execute()

            logger.info(f"File saved to Drive successfully: {file.get('name')} ({file.get('id')})")
            return True

        except Exception as e:
            logger.error(f"Failed to save to Drive: {str(e)}")
            return False

def save_inventory(inventory_df, file_path, drive_manager=None):
    """Save inventory to local file and Google Drive"""
    try:
        # Save locally
        inventory_df.to_csv(file_path, index=False)
        logger.info(f"Inventory saved locally: {file_path}")
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
        inventory_df.to_csv(backup_path, index=False)
        logger.info(f"Backup created: {backup_path}")
        
        # Save to Drive if available
        if drive_manager and drive_manager.service and 'drive_folder_id' in st.session_state:
            folder_id = st.session_state.drive_folder_id
            if folder_id:
                logger.info(f"Attempting to save to Drive folder: {folder_id}")
                if drive_manager.save_to_drive(file_path, folder_id):
                    st.success("✅ File saved to Google Drive successfully")
                    return True
                else:
                    st.error("❌ Failed to save to Google Drive")
                    return False
            else:
                st.warning("⚠️ No Google Drive folder configured")
                return False
        else:
            st.info("ℹ️ Google Drive integration not available")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save inventory: {str(e)}")
        st.error(f"Failed to save inventory: {str(e)}")
        return False
