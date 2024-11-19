import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import logging
from datetime import datetime, timedelta
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVENTORY_FILENAME = "wbpms_inventory_2024.csv"
BACKUP_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"  # Your Google Drive folder ID

class DriveManager:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.last_backup_date = None

    def load_inventory_from_drive(self, folder_id):
        """Load inventory from Google Drive"""
        try:
            if not self.service:
                return None

            # Search for the inventory file
            results = self.service.files().list(
                q=f"name='{INVENTORY_FILENAME}' and '{folder_id}' in parents",
                fields="files(id, name, modifiedTime)"
            ).execute()
            files = results.get('files', [])

            if files:
                # Get the file ID of the most recent version
                file_id = files[0]['id']
                request = self.service.files().get_media(fileId=file_id)
                
                # Download and read the file
                from io import StringIO
                content = request.execute().decode('utf-8')
                df = pd.read_csv(StringIO(content))
                logger.info(f"Loaded inventory from Drive: {len(df)} records")
                return df
            else:
                logger.info("No existing inventory file found in Drive")
                return None

        except Exception as e:
            logger.error(f"Failed to load inventory from Drive: {str(e)}")
            return None

    def check_and_create_backup(self, inventory):
        """Create backup if 5 days have passed"""
        try:
            current_date = datetime.now()
            if (not self.last_backup_date or 
                (current_date - self.last_backup_date).days >= 5):
                
                # Create backup filename with timestamp
                timestamp = current_date.strftime('%Y%m%d%H%M%S')
                backup_filename = f"inventory_{timestamp}.csv"
                
                # Save backup locally first
                inventory.to_csv(backup_filename, index=False)
                
                # Upload to Drive
                file_metadata = {
                    'name': backup_filename,
                    'parents': [BACKUP_FOLDER_ID],
                    'mimeType': 'text/csv'
                }
                
                media = MediaFileUpload(
                    backup_filename,
                    mimetype='text/csv',
                    resumable=True
                )
                
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                self.last_backup_date = current_date
                logger.info(f"Created backup: {backup_filename}")
                
                # Clean up local backup file
                os.remove(backup_filename)
                
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")

    def save_to_drive(self, inventory_df, folder_id):
        """Save/Update inventory in Google Drive"""
        try:
            if not self.service:
                return False

            # Save to temporary file first
            inventory_df.to_csv(INVENTORY_FILENAME, index=False)
            
            # Check if file already exists
            results = self.service.files().list(
                q=f"name='{INVENTORY_FILENAME}' and '{folder_id}' in parents",
                fields="files(id)"
            ).execute()
            files = results.get('files', [])

            if files:
                # Update existing file
                file_id = files[0]['id']
                media = MediaFileUpload(
                    INVENTORY_FILENAME,
                    mimetype='text/csv',
                    resumable=True
                )
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
            else:
                # Create new file
                file_metadata = {
                    'name': INVENTORY_FILENAME,
                    'parents': [folder_id],
                    'mimeType': 'text/csv'
                }
                media = MediaFileUpload(
                    INVENTORY_FILENAME,
                    mimetype='text/csv',
                    resumable=True
                )
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            # Clean up temporary file
            os.remove(INVENTORY_FILENAME)
            
            # Check if backup is needed
            self.check_and_create_backup(inventory_df)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to Drive: {str(e)}")
            return False
