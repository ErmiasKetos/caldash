import streamlit as st
from datetime import timedelta

def registration_calibration_page():
    st.title("Probe Registration & Calibration")

    # CSS for styling
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Section 1: Probe Information
    st.markdown('<div class="section-title">Probe Information</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        mfg_date = st.date_input("Mfg Date")
        mfg_pn = st.text_input("Mfg P/N")
        ketos_pn = st.text_input("KETOS P/N")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH", "DO", "ORP", "EC", "Temperature"])
        assigned_to = st.text_input("Assigned To")
        calibration_date = st.date_input("Calibration Date")
        calibration_time = st.time_input("Calibration Time")

    # Serial Number Generation
    expected_service_life = 2  # Example default value
    expire_date = mfg_date + timedelta(days=expected_service_life * 365)
    expire_yymm = expire_date.strftime("%y%m")
    serial_number = f"{probe_type}_{expire_yymm}_00001"
    st.text(f"Generated Serial Number: {serial_number}")

    # Section 2: Calibration Details
    st.markdown('<div class="section-title">Calibration Details</div>', unsafe_allow_html=True)
    if probe_type == "pH":
        st.markdown('<div class="sub-section-title">pH Calibration</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            ph4_control = st.text_input("pH Buffer 4 Control Number")
            ph4_expiration = st.date_input("pH Buffer 4 Expiration")
            ph4_opened = st.date_input("pH Buffer 4 Date Opened")
            ph7_control = st.text_input("pH Buffer 7 Control Number")
            ph7_expiration = st.date_input("pH Buffer 7 Expiration")
            ph7_opened = st.date_input("pH Buffer 7 Date Opened")
        with col2:
            ph10_control = st.text_input("pH Buffer 10 Control Number")
            ph10_expiration = st.date_input("pH Buffer 10 Expiration")
            ph10_opened = st.date_input("pH Buffer 10 Date Opened")
            ph4_initial = st.number_input("pH 4 Initial Measurement", value=0.0)
            ph4_calibrated = st.number_input("pH 4 Calibrated Measurement", value=0.0)

    elif probe_type == "DO":
        st.markdown('<div class="sub-section-title">DO Calibration</div>', unsafe_allow_html=True)
        barometric_pressure = st.number_input("Barometric Pressure", value=0.0)
        temperature = st.number_input("Temperature", value=0.0)
        initial_measurement = st.number_input("Initial Measurement", value=0.0)
        calibrated_measurement = st.number_input("Calibrated Measurement", value=0.0)
        membrane_date = st.date_input("Membrane Replacement Date")
        next_change_date = st.date_input("Next Membrane Change")

    elif probe_type == "ORP":
        st.markdown('<div class="sub-section-title">ORP Calibration</div>', unsafe_allow_html=True)
        orp_buffer = st.text_input("Buffer Solution")
        orp_temp = st.number_input("Temperature", value=0.0)
        orp_initial = st.number_input("Initial Measurement", value=0.0)
        orp_calibrated = st.number_input("Calibrated Measurement", value=0.0)
        orp_qa = st.text_input("QA Details")

    elif probe_type == "EC":
        st.markdown('<div class="sub-section-title">Specific Conductance Calibration</div>', unsafe_allow_html=True)
        sc_standard = st.text_input("Standard Solution")
        sc_temp = st.number_input("Temperature", value=0.0)
        sc_initial = st.number_input("Initial Measurement", value=0.0)
        sc_calibrated = st.number_input("Calibrated Measurement", value=0.0)
        sc_qa = st.text_input("QA Details")

    # Save Button
    if st.button("Save"):
        # Here you can save data to a local CSV or database
        st.success("Probe Registered and Calibrated Successfully!")

    st.markdown('</div>', unsafe_allow_html=True)
