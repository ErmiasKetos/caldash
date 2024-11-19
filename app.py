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
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

INVENTORY_FILENAME = "wbpms_inventory_2024.csv"

class DriveManager:
    def __init__(self):
        self.service = None
    
    def authenticate(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)
    
    def save_to_drive(self, file_path, drive_folder_id):
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [drive_folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='text/csv')
        self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

    def load_inventory_from_drive(self, filename):
        try:
            file_id = self.find_file_id(filename)
            if file_id:
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}.")
                fh.seek(0)
                return pd.read_csv(fh)
            else:
                return None
        except Exception as e:
            print(f"Error loading inventory from Drive: {e}")
            return None

    def find_file_id(self, filename):
        results = self.service.files().list(
            q=f"name='{filename}' and trashed=false",
            fields='files(id, name)'
        ).execute()
        items = results.get('files', [])
        if items:
            return items[0]['id']
        else:
            return None


def periodic_save():
    last_backup = datetime.now()
    while True:
        time.sleep(600)  # 10 minutes
        now = datetime.now()
        if all(key in st.session_state for key in ['inventory', 'drive_manager', 'drive_folder_id']):
            folder_id = st.session_state.drive_folder_id
            if folder_id and folder_id != "your_folder_id":
                save_inventory(st.session_state.inventory, INVENTORY_FILENAME, st.session_state.drive_manager, folder_id)
                
                # Create backup every 5 days
                if (now - last_backup).days >= 5:
                    timestamp = now.strftime('%Y%m%d%H%M%S')
                    backup_filename = f"inventory_{timestamp}.csv"
                    save_inventory(st.session_state.inventory, backup_filename, st.session_state.drive_manager, folder_id)
                    last_backup = now

def save_inventory(inventory, file_path, drive_manager, drive_folder_id):
    inventory.to_csv(file_path, index=False)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
    inventory.to_csv(backup_path, index=False)
    if drive_manager and drive_manager.service:
        drive_manager.save_to_drive(file_path, drive_folder_id)

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
        daemon=True
    )
    save_thread.start()
    st.session_state.save_thread = save_thread
    st.session_state['drive_folder_id'] = '19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i'


# Title of the App
st.set_page_config(page_title="Probe Management System", layout="wide")

# Main app
def main():
    try:
        st.sidebar.title("CalMS")
        
        # Handle OAuth 2.0 callback
        if 'code' in st.experimental_get_query_params():
            flow = Flow.from_client_config(
                client_config=CLIENT_CONFIG,
                scopes=SCOPES,
                redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
            )
            flow.fetch_token(code=st.experimental_get_query_params()['code'][0])
            st.session_state['credentials'] = flow.credentials
            st.experimental_rerun()

        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
        user_info = user_info_service.userinfo().get().execute()
        
        if not user_info['email'].endswith('@ketos.co'):
            st.error("Access denied. Please use your @ketos.co email to log in.")
            if st.button("Logout"):
                st.session_state.pop('credentials', None)
                st.experimental_rerun()
            return

        st.sidebar.text(f"Logged in as: {user_info['name']}")
        if st.sidebar.button("Logout"):
            st.session_state.pop('credentials', None)
            st.experimental_rerun()

        # Authenticate DriveManager
        st.session_state.drive_manager.authenticate(st.session_state['credentials'])

        # Load inventory from Google Drive
        if 'inventory' not in st.session_state and 'drive_manager' in st.session_state:
            st.session_state.inventory = st.session_state.drive_manager.load_inventory_from_drive(INVENTORY_FILENAME)
            if st.session_state.inventory is None:
                st.session_state.inventory = pd.DataFrame(columns=[
                    "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                    "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                    "Last Modified", "Status Color"
                ])
        
        # App Navigation
        page = st.sidebar.radio(
            "Navigate",
            ["Probe Registration & Calibration", "Inventory Review"],
        )

        if page == "Probe Registration & Calibration":
            registration_calibration_page()
        elif page == "Inventory Review":
            inventory_review_page()
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    import io
    from googleapiclient.http import MediaIoBaseDownload
    main()
