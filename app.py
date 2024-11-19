import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page
import streamlit_authenticator as stauth

# Authentication Setup
users = {
    "user1@ketos.co": {"name": "User One", "password": "hashed_password1"},
    "user2@ketos.co": {"name": "User Two", "password": "hashed_password2"},
}

authenticator = stauth.Authenticate(
    users,
    "my_app_secret",  # Replace with your unique secret key
    "my_app_cookie",  # Replace with your unique cookie name
    cookie_expiry_days=30,
)

name, authentication_status, username = authenticator.login("Login", "main")

# Authentication Logic
if authentication_status:
    st.sidebar.success(f"Welcome, {name}!")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Probe Registration & Calibration", "Inventory Review"],
    )

    if page == "Probe Registration & Calibration":
        registration_calibration_page()
    elif page == "Inventory Review":
        inventory_review_page()

elif authentication_status is False:
    st.error("Username/password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")
