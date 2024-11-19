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

# Login Page
st.title("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button("Login"):
    is_valid, name = validate(username, password)
    if is_valid:
        st.success(f"Welcome, {name}!")
        # Example navigation logic
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Select Page",
            ["Probe Registration & Calibration", "Inventory Review"],
        )
        if page == "Probe Registration & Calibration":
            st.write("Probe Registration & Calibration Page")
        elif page == "Inventory Review":
            st.write("Inventory Review Page")
    else:
        st.error("Invalid username or password")
