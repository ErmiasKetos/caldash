import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
import threading
import time
import os
import logging
from datetime import datetime
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth 2.0 configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Verify environment variables
if not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET"):
    raise EnvironmentError("Missing required environment variables: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"],
        "javascript_origins": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app"]
    }
}

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

    def save_to_drive(self, file_path, drive_folder_id):
        """Save file to Google Drive in specified folder"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return False
                
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [drive_folder_id]
            }
            
            media = MediaFileUpload(
                file_path, 
                mimetype='text/csv',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"File saved to Drive successfully: {file.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save to Drive: {str(e)}")
            st.error(f"Failed to save to Drive: {str(e)}")
            return False

def handle_session_error():
    """Handle session errors by clearing state and rerunning"""
    st.session_state.clear()
    st.experimental_set_query_params()
    st.rerun()  # Updated from experimental_rerun

def check_user_auth():
    """Check and handle user authentication"""
    if 'credentials' not in st.session_state:
        try:
            flow = Flow.from_client_config(
                client_config=CLIENT_CONFIG,
                scopes=SCOPES,
                redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
            )
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            st.session_state['oauth_state'] = state
            st.markdown(f"[Login with Google]({authorization_url})")
            return False
        except Exception as e:
            logger.error(f"Auth setup error: {str(e)}")
            st.error(f"Auth setup error: {str(e)}")
            return False
    return True

def init_google_auth():
    """Initialize Google authentication"""
    params = st.experimental_get_query_params()
    if 'code' in params:
        try:
            flow = Flow.from_client_config(
                client_config=CLIENT_CONFIG,
                scopes=SCOPES,
                state=st.session_state.get('oauth_state'),
                redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
            )
            flow.fetch_token(code=params['code'][0])
            st.session_state['credentials'] = flow.credentials
            
            # Initialize Drive manager with new credentials
            if 'drive_manager' in st.session_state:
                st.session_state.drive_manager.authenticate(flow.credentials)
            
            # Clear URL parameters
            st.experimental_set_query_params()
            logger.info("Google authentication initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            st.error(f"Authentication failed: {str(e)}")
            if 'credentials' in st.session_state:
                del st.session_state['credentials']
            return False
    return False

def save_inventory(inventory, file_path, drive_manager, drive_folder_id):
    """Save inventory to local file and Google Drive"""
    try:
        # Save locally
        inventory.to_csv(file_path, index=False)
        logger.info(f"Inventory saved locally: {file_path}")
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
        inventory.to_csv(backup_path, index=False)
        logger.info(f"Backup created: {backup_path}")
        
        # Save to Drive if available
        if drive_manager and drive_manager.service:
            success = drive_manager.save_to_drive(file_path, drive_folder_id)
            if success:
                st.success("Inventory saved to Google Drive")
            
    except Exception as e:
        logger.error(f"Failed to save inventory: {str(e)}")
        st.error(f"Failed to save inventory: {str(e)}")

def periodic_save(inventory, file_path, drive_manager, drive_folder_id):
    """Periodically save inventory"""
    while True:
        try:
            time.sleep(600)  # 10 minutes
            save_inventory(inventory, file_path, drive_manager, drive_folder_id)
        except Exception as e:
            logger.error(f"Periodic save failed: {str(e)}")

def main():
    try:
        st.sidebar.title("CalMS")
        
        # Debug information
        logger.info(f"Client ID exists: {bool(os.environ.get('GOOGLE_CLIENT_ID'))}")
        logger.info(f"Client Secret exists: {bool(os.environ.get('GOOGLE_CLIENT_SECRET'))}")
        
        # Check for auth code in URL
        if 'code' in st.experimental_get_query_params():
            if init_google_auth():
                st.rerun()  # Updated from experimental_rerun
            return

        # Check if already authenticated
        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
        user_info = user_info_service.userinfo().get().execute()
        
        if not user_info['email'].endswith('@ketos.co'):
            st.error("Access denied. Please use your @ketos.co email to log in.")
            if st.button("Logout"):
                handle_session_error()
            return

        st.sidebar.text(f"Logged in as: {user_info['name']}")
        
        # Navigation
        page = st.sidebar.radio(
            "Navigate to",
            ["Registration & Calibration", "Inventory Review"]
        )
        
        if page == "Registration & Calibration":
            registration_calibration_page()
        elif page == "Inventory Review":
            inventory_review_page()
            
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        handle_session_error()

if __name__ == "__main__":
    try:
        # Set page config first
        st.set_page_config(
            page_title="Probe Management System",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if 'inventory' not in st.session_state:
            if os.path.exists('inventory.csv'):
                st.session_state.inventory = pd.read_csv('inventory.csv')
                logger.info("Loaded existing inventory")
            else:
                st.session_state.inventory = pd.DataFrame(columns=[
                    "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                    "Mfg P/N", "Next Calibration", "Status"
                ])
                logger.info("Created new inventory")

        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()
            logger.info("Drive manager initialized")
        
        main()
        
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error(f"Application startup error: {str(e)}")
