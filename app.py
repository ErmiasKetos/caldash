import streamlit as st
from src.registration_calibration import registration_calibration_page
from src.inventory_review import inventory_review_page
import streamlit_authenticator as stauth


# User configuration with hashed passwords
users = {
    "ermias@ketos.co": {"name": "Ermias", "password": "$2b$12$abcd1234hash1..."},
    "girma.seifu@ketos.co": {"name": "Girma Seifu", "password": "$2b$12$abcd1234hash2..."},
}

# Authenticator setup
authenticator = stauth.Authenticate(
    users,
    "my_app_secret",  # Replace with a unique secret key
    "my_app_cookie",  # Replace with a unique cookie name
    cookie_expiry_days=30,
)

# Login
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Welcome, {name}!")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Probe Registration & Calibration", "Inventory Review"],
    )

    # Navigation logic (example pages)
    if page == "Probe Registration & Calibration":
        st.write("Probe Registration & Calibration Page")
    elif page == "Inventory Review":
        st.write("Inventory Review Page")

elif authentication_status is False:
    st.error("Username/password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")
