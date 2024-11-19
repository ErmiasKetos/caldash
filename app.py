import streamlit as st
import streamlit_authenticator as stauth

# User configuration with plaintext passwords
names = ["Ermias", "Girma Seifu"]
usernames = ["ermias@ketos.co", "girma.seifu@ketos.co"]
passwords = ["18221822", "18221822"]

# Plaintext Password Authentication
def validate(username, password):
    if username in usernames and password in passwords:
        user_index = usernames.index(username)
        if passwords[user_index] == password:
            return True, names[user_index]
    return False, None

# Initialize session state for login
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None

# Login Section
if st.session_state["authentication_status"] is None or st.session_state["authentication_status"] is False:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        is_valid, name = validate(username, password)
        if is_valid:
            st.session_state["authentication_status"] = True
            st.session_state["name"] = name
            st.success(f"Welcome, {name}!")
        else:
            st.error("Invalid username or password")

# After Successful Login
if st.session_state["authentication_status"]:
    st.sidebar.title(f"Welcome, {st.session_state['name']}")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Probe Registration & Calibration", "Inventory Review"],
    )

# App Navigation
if page == "Probe Registration & Calibration":
    registration_calibration_page()
elif page == "Inventory Review":
    inventory_review_page()
