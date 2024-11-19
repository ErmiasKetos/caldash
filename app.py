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
from src.drive_manager import DriveManager
from src.inventory_manager import initialize_inventory

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

# Update the init_google_auth function:
def init_google_auth():
    """Initialize Google authentication"""
    try:
        params = st.experimental_get_query_params()
        if 'code' not in params:
            return False

        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            state=st.session_state.get('oauth_state'),
            redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
        )
        
        flow.fetch_token(code=params['code'][0])
        st.session_state['credentials'] = flow.credentials
        
        # Initialize Drive manager with new credentials
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()
        
        st.session_state.drive_manager.authenticate(flow.credentials)
        
        # Set default Drive folder
        st.session_state['drive_folder_id'] = DRIVE_FOLDER_ID
        
        # Verify folder access
        if st.session_state.drive_manager.verify_folder_access(DRIVE_FOLDER_ID):
            logger.info(f"Successfully verified access to folder: {DRIVE_FOLDER_ID}")
            st.success("✅ Drive folder access verified")
        else:
            logger.warning("Could not verify folder access")
            st.warning("⚠️ Could not verify Drive folder access. Please check permissions.")
        
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

# Update the Google Drive Settings section in main():
def main():
    try:
        st.sidebar.title("CalMS")
        
        # Debug information
        logger.info(f"Client ID exists: {bool(os.environ.get('GOOGLE_CLIENT_ID'))}")
        logger.info(f"Client Secret exists: {bool(os.environ.get('GOOGLE_CLIENT_SECRET'))}")
        
        # Add debug information to sidebar
        with st.sidebar.expander("Debug Info", expanded=True):
            st.write({
                "Has Code": bool(st.experimental_get_query_params().get('code')),
                "Has Credentials": 'credentials' in st.session_state,
                "Has Drive Manager": 'drive_manager' in st.session_state,
                "Drive Folder ID": st.session_state.get('drive_folder_id')
            })

        # Check for auth code in URL
        if 'code' in st.experimental_get_query_params():
            if init_google_auth():
                st.rerun()
            return

        # Check if already authenticated
        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # Get user info and verify email domain
        try:
            user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
            user_info = user_info_service.userinfo().get().execute()
            
            if not user_info['email'].endswith('@ketos.co'):
                st.error("Access denied. Please use your @ketos.co email to log in.")
                if st.button("Logout"):
                    st.session_state.clear()
                    st.experimental_set_query_params()
                    st.rerun()
                return

            # Initialize inventory after successful authentication
            initialize_inventory()

            st.sidebar.text(f"Logged in as: {user_info['name']}")
            
         # Google Drive Settings in sidebar
        with st.sidebar.expander("Google Drive Settings"):
            st.info("Google Drive Integration Status")
        
            if 'drive_folder_id' in st.session_state:
                st.success(f"✅ Using folder ID: {st.session_state['drive_folder_id']}")
            
                if st.button("Test Folder Access"):
                    if st.session_state.drive_manager.verify_folder_access(st.session_state['drive_folder_id']):
                        st.success("✅ Folder access verified!")
                    else:
                        st.error("❌ Could not access folder. Please check permissions.")
                        st.info("Make sure the folder is shared with your Google account")
            else:
                st.warning("⚠️ Drive folder not configured")
                st.session_state['drive_folder_id'] = DRIVE_FOLDER_ID
                st.info("Using default folder ID")

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
            logger.error(f"Error getting user info: {str(e)}")
            st.error("Authentication error. Please try logging in again.")
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    try:
        # Set page config first
        st.set_page_config(
            page_title="Probe Management System",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        main()
        
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error(f"Application startup error: {str(e)}")
