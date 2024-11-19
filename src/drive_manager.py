import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import pandas as pd
import io
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVENTORY_FILENAME = "wbpms_inventory_2024.csv"
BACKUP_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

class DriveManager:
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

    def load_file_from_drive(self, file_id):
        """Load and parse CSV file from Drive"""
        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return None

            # Get the file metadata and content
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            # Parse CSV content
            df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            logger.info(f"Successfully loaded file from Drive: {file_id}")
            return df

        except Exception as e:
            logger.error(f"Failed to load file from Drive: {str(e)}")
            return None

    def save_to_drive(self, file_path, drive_folder_id, update_existing=True):
        """Save or update file in Google Drive"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            if not self.service:
                logger.error("Drive service not initialized")
                return False

            filename = os.path.basename(file_path)

            # Check if file already exists
            existing_files = self.service.files().list(
                q=f"name='{filename}' and '{drive_folder_id}' in parents",
                spaces='drive',
                fields="files(id, name)"
            ).execute()

            media = MediaFileUpload(
                file_path,
                mimetype='text/csv',
                resumable=True
            )

            if existing_files.get('files') and update_existing:
                # Update existing file
                file_id = existing_files['files'][0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                logger.info(f"Updated existing file in Drive: {filename}")
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'parents': [drive_folder_id],
                    'mimeType': 'text/csv'
                }
                
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"Created new file in Drive: {filename}")

            return True

        except Exception as e:
            logger.error(f"Failed to save to Drive: {str(e)}")
            return False
