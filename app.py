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
from src.drive_manager import DriveManager
from src.inventory_review import inventory_review_page
from src.inventory_manager import initialize_inventory


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth 2.0 configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
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
            
            self.service.files().get(fileId=folder_id).execute()
            logger.info(f"Folder access verified for ID: {folder_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify folder access: {str(e)}")
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

def save_inventory(inventory, file_path, drive_manager=None):
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
        if drive_manager and drive_manager.service and 'drive_folder_id' in st.session_state:
            folder_id = st.session_state.drive_folder_id
            if folder_id and folder_id != "your_folder_id":
                success = drive_manager.save_to_drive(file_path, folder_id)
                if success:
                    st.success("Inventory saved to Google Drive")
                else:
                    st.error("Failed to save to Google Drive")
            else:
                st.warning("Please configure Google Drive folder in settings")
            
    except Exception as e:
        logger.error(f"Failed to save inventory: {str(e)}")
        st.error(f"Failed to save inventory: {str(e)}")

def periodic_save():
    """Periodically save inventory"""
    while True:
        try:
            time.sleep(600)  # 10 minutes
            if all(key in st.session_state for key in ['inventory', 'drive_manager', 'drive_folder_id']):
                folder_id = st.session_state.drive_folder_id
                if folder_id and folder_id != "your_folder_id":
                    save_inventory(st.session_state.inventory, 'inventory.csv', st.session_state.drive_manager)
        except Exception as e:
            logger.error(f"Periodic save failed: {str(e)}")

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

def main():
    try:
        st.sidebar.title("CalMS")
        
        # Debug information
        logger.info(f"Client ID exists: {bool(os.environ.get('GOOGLE_CLIENT_ID'))}")
        logger.info(f"Client Secret exists: {bool(os.environ.get('GOOGLE_CLIENT_SECRET'))}")
        
        # Check for auth code in URL
        if 'code' in st.experimental_get_query_params():
           with st.spinner('Authenticating...'):
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
                st.session_state.clear()
                st.experimental_set_query_params()
                st.rerun()
            return
            
        initialize_inventory()
        st.sidebar.text(f"Logged in as: {user_info['name']}")
        
        # Google Drive Settings in sidebar
        with st.sidebar.expander("Google Drive Settings"):
            st.info("Configure Google Drive folder for automatic saving")
            
            current_folder = st.session_state.get('drive_folder_id', "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i")
            new_folder_id = st.text_input(
                "Google Drive Folder ID",
                value=current_folder,
                help="Enter the folder ID from your Google Drive URL"
            )
            
            if st.button("Verify Folder Access"):
                if st.session_state.drive_manager.verify_folder_access(new_folder_id):
                    st.session_state.drive_folder_id = new_folder_id
                    st.success("✅ Folder access verified successfully!")
                    # Test save to verify everything works
                    save_inventory(st.session_state.inventory, 'inventory.csv', st.session_state.drive_manager)
                else:
                    st.error("❌ Cannot access this folder. Please check the ID and permissions.")
                    st.info("Make sure the folder is shared with your Google account")

            if 'drive_folder_id' in st.session_state:
                st.info(f"Current folder ID: {st.session_state.drive_folder_id}")
                
                # Add a test save button
                if st.button("Test Save to Drive"):
                    save_inventory(st.session_state.inventory, 'inventory.csv', st.session_state.drive_manager)

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

        # Initialize drive_folder_id if not set
        if 'drive_folder_id' not in st.session_state:
            st.session_state.drive_folder_id = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"
            logger.info("Set default drive folder ID")

        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()
            logger.info("Drive manager initialized")

        # Start periodic save thread
        if 'save_thread' not in st.session_state:
            save_thread = threading.Thread(target=periodic_save, daemon=True)
            save_thread.start()
            st.session_state.save_thread = save_thread
            logger.info("Periodic save thread started")
        
        main()
        
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error(f"Application startup error: {str(e)}")
