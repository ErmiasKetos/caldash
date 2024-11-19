import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import logging
from datetime import datetime
from src.registration_calibration import registration_calibration_page
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

        # Initialize Drive manager with new credentials
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()

        st.session_state.drive_manager.authenticate(flow.credentials)

        # Verify folder access (optional for Drive integration)
        if 'drive_folder_id' not in st.session_state:
            st.session_state['drive_folder_id'] = DRIVE_FOLDER_ID

        if st.session_state.drive_manager.verify_folder_access(DRIVE_FOLDER_ID):
            logger.info(f"Drive folder access verified for folder ID: {DRIVE_FOLDER_ID}")
        else:
            st.warning("⚠️ Drive folder access verification failed. Check permissions.")

        # Clear query params to prevent re-execution
        st.experimental_set_query_params()

        # Set the user as authenticated
        st.session_state['authenticated'] = True

        logger.info("Google authentication successfully initialized.")
        return True

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        st.error(f"Authentication failed: {str(e)}")
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
        return False

def main():
    try:
        st.sidebar.title("CalMS")
        if 'code' in st.experimental_get_query_params():
            if init_google_auth():
                st.rerun()
            return

        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # User info
        try:
            user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
            user_info = user_info_service.userinfo().get().execute()
            if not user_info['email'].endswith('@ketos.co'):
                st.error("Access denied. Please use your @ketos.co email.")
                if st.button("Logout"):
                    st.session_state.clear()
                    st.experimental_set_query_params()
                    st.rerun()
                return

            st.sidebar.text(f"Logged in as: {user_info['name']}")
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            st.error("Authentication error. Please try logging in again.")
            st.session_state.clear()
            st.rerun()

        # Sidebar options
        with st.sidebar.expander("Google Drive Settings"):
            if 'drive_folder_id' in st.session_state:
                st.success(f"✅ Using folder ID: {st.session_state['drive_folder_id']}")
                if st.button("Test Folder Access"):
                    drive_manager = st.session_state.get('drive_manager')
                    if drive_manager and drive_manager.verify_folder_access(st.session_state['drive_folder_id']):
                        st.success("✅ Folder access verified!")
                    else:
                        st.error("❌ Could not access folder. Check permissions.")
            else:
                st.warning("⚠️ Drive folder not configured.")

        # Page navigation
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
        st.set_page_config(
            page_title="Probe Management System",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        main()
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error(f"Application startup error: {str(e)}")
