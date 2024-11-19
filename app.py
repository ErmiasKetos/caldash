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
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

# DriveManager class for Google Drive operations
class DriveManager:
    def __init__(self):
        self.service = None

    def authenticate(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def save_to_drive(self, file_path, drive_folder_id):
        file_metadata = {'name': os.path.basename(file_path), 'parents': [drive_folder_id]}
        media = MediaFileUpload(file_path, mimetype='text/csv')
        self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()

# Periodic save function
def periodic_save(inventory, file_path, drive_manager, drive_folder_id):
    while True:
        time.sleep(600)  # Every 10 minutes
        save_inventory(inventory, file_path, drive_manager, drive_folder_id)

# Save inventory to CSV and optionally to Google Drive
def save_inventory(inventory, file_path, drive_manager, drive_folder_id):
    inventory.to_csv(file_path, index=False)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
    inventory.to_csv(backup_path, index=False)
    if drive_manager and drive_manager.service:
        drive_manager.save_to_drive(file_path, drive_folder_id)

# Check if user is authenticated
def check_user_auth():
    if 'credentials' not in st.session_state:
        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
        )
        authorization_url, _ = flow.authorization_url(prompt="consent")
        st.markdown(f"[Login with Google]({authorization_url})")
        return False
    return True

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

if 'save_thread' not in st.session_state:
    save_thread = threading.Thread(
        target=periodic_save,
        args=(st.session_state.inventory, 'inventory.csv', st.session_state.drive_manager, '19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i'),
        daemon=True
    )
    save_thread.start()
    st.session_state.save_thread = save_thread

# Title of the App
st.set_page_config(page_title="Probe Management System", layout="wide")

# Main app
def main():
    st.sidebar.title("CalMS")
    
    # Check user authentication
    if not check_user_auth():
        return

    # Get user info
    user_info_service = build('oauth2', 'v2', credentials=st.session_state.credentials)
    user_info = user_info_service.userinfo().get().execute()
    
    # Restrict access to @ketos.co emails
    if not user_info['email'].endswith('@ketos.co'):
        st.error("Access denied. Please use your @ketos.co email to log in.")
        return

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Probe Registration & Calibration", "Inventory Review"],
    )

    st.sidebar.text(f"Logged in as: {user_info['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.pop('credentials', None)
        st.experimental_rerun()

    # Authenticate DriveManager
    st.session_state.drive_manager.authenticate(st.session_state.credentials)

    # App Navigation
    if page == "Probe Registration & Calibration":
        registration_calibration_page()
    elif page == "Inventory Review":
        inventory_review_page()

if __name__ == "__main__":
    # Handle OAuth 2.0 callback
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
        )
        flow.fetch_token(code=query_params['code'][0])
        st.session_state.credentials = Credentials.from_authorized_user_info(flow.credentials)
        st.experimental_rerun()
    else:
        main()
