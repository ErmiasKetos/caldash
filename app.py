import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import logging
import os
from datetime import datetime
from src.drive_manager import DriveManager
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page
from src.inventory_manager import initialize_inventory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRIVE_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def init_google_auth():
    """Initialize Google authentication."""
    try:
        params = st.experimental_get_query_params()
        if 'code' not in params:
            return False

        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
        )

        flow.fetch_token(code=params['code'][0])
        st.session_state['credentials'] = flow.credentials

        # Initialize Drive manager
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()
        st.session_state.drive_manager.authenticate(flow.credentials)
        
        # Initialize inventory
        if 'inventory' not in st.session_state:
            initialize_inventory()

        # Set authenticated state
        st.session_state['authenticated'] = True
        st.session_state['drive_folder_id'] = DRIVE_FOLDER_ID

        # Clear query parameters
        st.experimental_set_query_params()
        
        logger.info("Authentication successful")
        return True

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
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

def main():
    try:
        st.sidebar.title("CalMS")

        # Handle OAuth flow
        params = st.experimental_get_query_params()
        if 'code' in params and 'authenticated' not in st.session_state:
            if init_google_auth():
                st.experimental_rerun()
            return

        # Check authentication
        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # Validate user email domain
        try:
            user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
            user_info = user_info_service.userinfo().get().execute()

            if user_info['email'].endswith('@ketos.co'):
                st.sidebar.text(f"Logged in as: {user_info['name']}")
            else:
                st.error("Access denied. Please use your @ketos.co email.")
                if st.button("Logout"):
                    st.session_state.clear()
                    st.experimental_rerun()
                return
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            st.error("Authentication error. Please try logging in again.")
            st.session_state.clear()
            st.experimental_rerun()
            return

        # Sidebar navigation
        page = st.sidebar.radio(
            "Navigate to",
            ["Registration & Calibration", "Inventory Review"]
        )

        # Page routing
        if page == "Registration & Calibration":
            registration_calibration_page()
        elif page == "Inventory Review":
            inventory_review_page()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Probe Management System",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
