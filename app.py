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
        "redirect_uris": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"],
        "javascript_origins": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app"]
    }
}

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
            # Store the state in session for verification
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
            # Clear the URL parameters
            st.experimental_set_query_params()
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            if 'credentials' in st.session_state:
                del st.session_state['credentials']
            return False
    return False

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
