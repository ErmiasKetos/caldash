import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.inventory_review import save_inventory, get_file_path

# Autofill options for KETOS Part Number
ketos_part_numbers = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Service life in years for each probe type
service_life = {
    "pH Probe": 2,
    "DO Probe": 2,
    "ORP Probe": 4,
    "EC Probe": 10,  # Example: EC probes have a service life of 2 years
}

# Function to render the registration and calibration page
def registration_calibration_page():
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.DataFrame(
            columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"]
        )

    st.title("Probe Registration & Calibration")
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
        ketos_part_number = st.selectbox("KETOS Part Number", ketos_part_numbers.get(probe_type, []))
        calibration_date = st.date_input("Calibration Date", datetime.today())

    # Serial Number Generation
    service_years = service_life.get(probe_type, 1)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    expire_yymm = expire_date.strftime("%y%m")
    serial_number = f"{probe_type.split()[0]}_{expire_yymm}_{len(st.session_state['inventory']) + 1:05d}"
    st.text(f"Generated Serial Number: {serial_number}")

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
        st.session_state["inventory"] = pd.concat([st.session_state["inventory"], pd.DataFrame([new_row])], ignore_index=True)
        save_inventory(st.session_state["inventory"], get_file_path(), version_control=True)
        st.success("Probe registered successfully!")


# pH Calibration Rendering
def render_ph_calibration():
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">pH Calibration</h3>', unsafe_allow_html=True)
    for idx, (buffer_label, color) in enumerate([("pH 4", "#f8f1f1"), ("pH 7", "#e8f8f2"), ("pH 10", "#e8f0f8")]):
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{buffer_label} Buffer</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(f"{buffer_label} Control Number", key=f"ph_{idx}_control_number")
            st.date_input(f"{buffer_label} Expiration Date", key=f"ph_{idx}_expiration")
        with col2:
            st.date_input(f"{buffer_label} Date Opened", key=f"ph_{idx}_date_opened")
            st.number_input(f"{buffer_label} Initial Measurement (pH)", value=0.0, key=f"ph_{idx}_initial")
            st.number_input(f"{buffer_label} Calibrated Measurement (pH)", value=0.0, key=f"ph_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)

# DO Calibration Rendering
def render_do_calibration():
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #0071ba;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Initial Temperature (°C)", value=0.0, key="do_temp_initial")
    with col2:
        st.number_input("Calibrated Temperature (°C)", value=0.0, key="do_temp_calibrated")

    for idx, label in enumerate(["0% DO Calibration", "100% DO Calibration"]):
        st.markdown(
            f'<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label}</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(f"{label} Control Number", key=f"do_{idx}_control_number")
            st.date_input(f"{label} Expiration Date", key=f"do_{idx}_expiration")
        with col2:
            st.date_input(f"{label} Date Opened", key=f"do_{idx}_date_opened")
            st.number_input(f"{label} Initial Measurement (%)", value=0.0, key=f"do_{idx}_initial")
            st.number_input(f"{label} Calibrated Measurement (%)", value=0.0, key=f"do_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)

# ORP Calibration Rendering
def render_orp_calibration():
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Control Number", key="orp_control_number")
        st.date_input("Expiration Date", key="orp_expiration")
    with col2:
        st.date_input("Date Opened", key="orp_date_opened")
        st.number_input("Initial Measurement (mV)", value=0.0, key="orp_initial")
        st.number_input("Calibrated Measurement (mV)", value=0.0, key="orp_calibrated")

# EC Calibration Rendering
def render_ec_calibration():
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">EC Calibration</h3>', unsafe_allow_html=True)
    for idx, label in enumerate(["84 μS/cm", "1413 μS/cm", "12.88 mS/cm"]):
        st.markdown(
            f'<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label} Calibration</h4>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(f"{label} Control Number", key=f"ec_{idx}_control_number")
            st.date_input(f"{label} Expiration Date", key=f"ec_{idx}_expiration")
        with col2:
            st.date_input(f"{label} Date Opened", key=f"ec_{idx}_date_opened")
            st.number_input(f"{label} Initial Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_initial")
            st.number_input(f"{label} Calibrated Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)
