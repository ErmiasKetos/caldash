import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Probe types and their KETOS part numbers
probe_types = {
    "pH Probe": ["400-00260", "400-00292"],
    "ORP Probe": ["400-00261"],
    "DO Probe": ["300-00056"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes
service_life = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}


def registration_calibration_page():
    # Initialize inventory in session state
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.DataFrame(
            columns=[
                "Serial Number",
                "Type",
                "Manufacturer",
                "KETOS P/N",
                "Mfg P/N",
                "Next Calibration",
                "Status",
            ]
        )

    st.title("Probe Registration & Calibration")

    # General Section: Probe Information
    st.subheader("Probe Information")
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", list(probe_types.keys()))
        ketos_part_number = st.selectbox("KETOS Part Number", probe_types.get(probe_type, []))
        calibration_date = st.date_input("Calibration Date", datetime.today())
        calibration_time = st.time_input("Calibration Time", datetime.now().time())

    # Serial Number Generation
    service_years = service_life.get(probe_type, 1)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    expire_yymm = expire_date.strftime("%y%m")
    serial_number = f"{probe_type.split()[0]}_{expire_yymm}_{len(st.session_state['inventory']) + 1:05d}"
    st.text(f"Generated Serial Number: {serial_number}")

    # Calibration Details Section
    st.subheader("Calibration Details")
    if probe_type == "pH Probe":
        render_ph_calibration()
    elif probe_type == "DO Probe":
        render_do_calibration()
    elif probe_type == "ORP Probe":
        render_orp_calibration()
    elif probe_type == "EC Probe":
        render_ec_calibration()

    # Save Button
    if st.button("Save"):
        next_calibration = calibration_date + timedelta(days=service_years * 365)
        new_row = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Next Calibration": next_calibration.strftime("%Y-%m-%d"),
            "Status": "Active",
        }
        st.session_state["inventory"] = st.session_state["inventory"].append(new_row, ignore_index=True)
        st.success("Probe Registered and Saved Successfully!")


def render_ph_calibration():
    st.subheader("pH Calibration")
    for buffer_label in ["pH 4", "pH 7", "pH 10"]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {buffer_label} Buffer")
            st.text_input(f"{buffer_label} Control Number")
            st.date_input(f"{buffer_label} Expiration Date")
        with col2:
            st.date_input(f"{buffer_label} Date Opened")
            st.number_input(f"{buffer_label} Initial Measurement (pH)", value=0.0)
            st.number_input(f"{buffer_label} Calibrated Measurement (pH)", value=0.0)
            st.number_input(f"{buffer_label} mV", value=0.0)


def render_do_calibration():
    st.subheader("DO Calibration")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("0% DO Control Number")
        st.date_input("0% DO Expiration Date")
        st.number_input("0% DO Initial Measurement (%)", value=0.0)
        st.number_input("100% DO Initial Measurement (%)", value=0.0)
    with col2:
        st.date_input("0% DO Date Opened")
        st.number_input("0% DO Calibrated Measurement (%)", value=0.0)
        st.number_input("100% DO Calibrated Measurement (%)", value=0.0)


def render_orp_calibration():
    st.subheader("ORP Calibration")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("240 mV Control Number")
        st.date_input("240 mV Expiration Date")
        st.number_input("240 mV Initial Measurement (mV)", value=0.0)
    with col2:
        st.date_input("240 mV Date Opened")
        st.number_input("240 mV Calibrated Measurement (mV)", value=0.0)


def render_ec_calibration():
    st.subheader("Specific Conductance (EC) Calibration")
    for label in ["84 μS/cm", "1413 μS/cm", "12.88 mS/cm"]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {label} Calibration")
            st.text_input(f"{label} Control Number")
            st.date_input(f"{label} Expiration Date")
        with col2:
            st.number_input(f"{label} Initial Measurement (μS/cm or mS/cm)", value=0.0)
            st.number_input(f"{label} Calibrated Measurement (μS/cm or mS/cm)", value=0.0)
