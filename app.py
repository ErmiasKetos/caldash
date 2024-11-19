import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
import threading
import time
import os
from datetime import datetime
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page

# OAuth 2.0 configuration
SCOPES = ['openid', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']



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
            return True
        except Exception as e:
            st.error(f"Drive authentication failed: {str(e)}")
            return False

    def save_to_drive(self, file_path, drive_folder_id):
        """Save file to Google Drive in specified folder"""
        try:
            if not self.service:
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
            
            return True
        except Exception as e:
            st.error(f"Failed to save to Drive: {str(e)}")
            return False

def check_user_auth():
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
            st.error(f"Auth setup error: {str(e)}")
            return False
    return True

def init_google_auth():
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
            st.experimental_set_query_params()
            return True
        except Exception as e:
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
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
        inventory.to_csv(backup_path, index=False)
        
        # Save to Drive if available
        if drive_manager and drive_manager.service:
            drive_manager.save_to_drive(file_path, drive_folder_id)
            
    except Exception as e:
        st.error(f"Failed to save inventory: {str(e)}")

def periodic_save(inventory, file_path, drive_manager, drive_folder_id):
    """Periodically save inventory"""
    while True:
        time.sleep(600)  # 10 minutes
        save_inventory(inventory, file_path, drive_manager, drive_folder_id)

def main():
    st.sidebar.title("CalMS")
    
    # Check for auth code in URL
    if 'code' in st.experimental_get_query_params():
        if init_google_auth():
            st.experimental_rerun()
        return

    # Check if already authenticated
    if not check_user_auth():
        st.write("Please log in to access the application.")
        return

    try:
        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
        user_info = user_info_service.userinfo().get().execute()
        
        if not user_info['email'].endswith('@ketos.co'):
            st.error("Access denied. Please use your @ketos.co email to log in.")
            if st.button("Logout"):
                st.session_state.clear()
                st.experimental_set_query_params()
                st.experimental_rerun()
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
        st.error(f"Session error: {str(e)}")
        st.session_state.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    # Initialize session state
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory.csv'):
            st.session_state.inventory = pd.read_csv('inventory.csv')
        else:
            st.session_state.inventory = pd.DataFrame(columns=[
                "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                "Mfg P/N", "Next Calibration", "Status"
            ])

    if 'drive_manager' not in st.session_state:
        st.session_state.drive_manager = DriveManager()

    # Set page config
    st.set_page_config(page_title="Probe Management System", layout="wide")
    
    main()
