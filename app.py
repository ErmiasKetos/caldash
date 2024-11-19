import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
import threading
import time
import os
from datetime import datetime, timedelta
import jwt

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'

class AuthManager:
    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    
    def verify_ketos_email(self, email):
        return email.endswith('@ketos.co')
    
    def create_session_token(self, email):
        return jwt.encode(
            {'email': email, 'exp': datetime.utcnow() + timedelta(days=1)},
            self.secret_key,
            algorithm='HS256'
        )
    
    def verify_session_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['email']
        except:
            return None

class DriveManager:
    def __init__(self):
        self.credentials = None
        self.service = None
    
    def authenticate(self):
        if os.path.exists('token.json'):
            self.credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not self.credentials or not self.credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            self.credentials = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.credentials.to_json())
        
        self.service = build('drive', 'v3', credentials=self.credentials)
    
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

def periodic_save(inventory, file_path, drive_manager, drive_folder_id):
    while True:
        time.sleep(600)  # 10 minutes
        inventory.to_csv(file_path, index=False)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{os.path.splitext(file_path)[0]}_{timestamp}.csv"
        inventory.to_csv(backup_path, index=False)
        if drive_manager:
            drive_manager.save_to_drive(file_path, drive_folder_id)

# Initialize session state
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = AuthManager()

if 'drive_manager' not in st.session_state:
    st.session_state.drive_manager = DriveManager()
    st.session_state.drive_manager.authenticate()

if 'inventory' not in st.session_state:
    if os.path.exists('inventory.csv'):
        st.session_state.inventory = pd.read_csv('inventory.csv')
    else:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status"
        ])

if 'save_thread' not in st.session_state:
    save_thread = threading.Thread(
        target=periodic_save,
        args=(st.session_state.inventory, 'inventory.csv', st.session_state.drive_manager, 'your_folder_id'),
        daemon=True
    )
    save_thread.start()
    st.session_state.save_thread = save_thread

# Title of the App
st.set_page_config(page_title="Probe Management System", layout="wide")

# Login page
def login_page():
    st.title("Login")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if st.session_state.auth_manager.verify_ketos_email(email):
            # In production, verify password against secure backend
            token = st.session_state.auth_manager.create_session_token(email)
            st.session_state.token = token
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Please use your @ketos.co email address")

# Main app
def main():
    # Check authentication
    if 'token' not in st.session_state:
        login_page()
        return
    
    email = st.session_state.auth_manager.verify_session_token(st.session_state.token)
    if not email:
        st.session_state.pop('token', None)
        st.experimental_rerun()
        return

    # Sidebar Navigation
    st.sidebar.title("CalMS")
    page = st.sidebar.radio(
        "Navigate",
        ["Probe Registration & Calibration", "Inventory Review"],
    )

    st.sidebar.text(f"Logged in as: {email}")
    if st.sidebar.button("Logout"):
        st.session_state.pop('token', None)
        st.experimental_rerun()

    # Shared Save Location Setting
    if "save_location" not in st.session_state:
        st.session_state["save_location"] = st.radio(
            "Select where to save the inventory file:",
            ["Local Computer", "Google Drive"],
        )

    # App Navigation
    if page == "Probe Registration & Calibration":
        registration_calibration_page()
    elif page == "Inventory Review":
        inventory_review_page()

if __name__ == "__main__":
    main()
