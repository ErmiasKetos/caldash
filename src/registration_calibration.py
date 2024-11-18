import streamlit as st
from datetime import timedelta

def registration_calibration_page():
    st.title("Probe Registration & Calibration")
    
    # Create a layout for the page
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Probe Information</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            manufacturer = st.text_input("Manufacturer")
            mfg_date = st.date_input("Mfg Date")
            mfg_pn = st.text_input("Mfg P/N")
        with col2:
            probe_type = st.selectbox("Probe Type", ["pH", "DO", "ORP", "EC"])
            assigned_to = st.text_input("Assigned To")
            calibration_date = st.date_input("Date")
        
        # Generate Serial Number
        expected_service_life = 2  # Example value
        expire_date = mfg_date + timedelta(days=expected_service_life * 365)
        expire_yymm = expire_date.strftime("%y%m")
        serial_number = f"{probe_type}_{expire_yymm}_00001"
        st.text(f"Generated Serial Number: {serial_number}")
        
        st.markdown('<div class="section-title">Calibration Details</div>', unsafe_allow_html=True)
        if probe_type == "pH":
            st.text_input("pH Buffer 4 Control Number")
            st.date_input("pH Buffer 4 Expiration")
            st.text_input("pH Buffer 7 Control Number")
            st.date_input("pH Buffer 7 Expiration")
        elif probe_type == "DO":
            st.text_input("DO Control Number")
            st.date_input("DO Expiration")
            st.number_input("Initial DO Value (%)")
        # Add other calibration fields dynamically based on probe_type

        # Save Button
        if st.button("Save"):
            # Save data to a .csv file or Google Sheet
            st.success("Probe Registered Successfully!")

        st.markdown('</div>', unsafe_allow_html=True)

