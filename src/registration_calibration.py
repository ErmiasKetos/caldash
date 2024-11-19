import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import time
import threading
import logging
from src.drive_manager import DriveManager, save_inventory
from src.inventory_manager import add_new_probe, get_next_serial_number

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Autofill options for KETOS Part Number
ketos_part_numbers = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes
service_life = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

def render_ph_calibration():
    """Render pH probe calibration form"""
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

def render_do_calibration():
    """Render DO probe calibration form"""
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

def render_orp_calibration():
    """Render ORP probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Control Number", key="orp_control_number")
        st.date_input("Expiration Date", key="orp_expiration")
    with col2:
        st.date_input("Date Opened", key="orp_date_opened")
        st.number_input("Initial Measurement (mV)", value=0.0, key="orp_initial")
        st.number_input("Calibrated Measurement (mV)", value=0.0, key="orp_calibrated")

def render_ec_calibration():
    """Render EC probe calibration form"""
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

def registration_calibration_page():
    """Main page for probe registration and calibration"""
    if 'inventory' not in st.session_state:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status"
        ])

    # Debug information
    with st.sidebar.expander("Debug Info", expanded=False):
        st.write({
            "Drive Folder ID": st.session_state.get('drive_folder_id'),
            "Drive Manager Present": 'drive_manager' in st.session_state,
            "Has Credentials": 'credentials' in st.session_state
        })

    # Title
    st.markdown(
        f'<h1 style="font-family: Arial, sans-serif; font-size: 32px; color: #0071ba;">📋 Probe Registration & Calibration</h1>',
        unsafe_allow_html=True,
    )

    # General Section: Probe Information
    st.markdown('<h2 style="font-family: Arial; color: #333;">Probe Information</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer", key="manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today(), key="manufacturing_date")
        manufacturer_part_number = st.text_input("Manufacturer Part Number", key="manufacturer_part_number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"], key="probe_type")
        ketos_part_number = st.selectbox(
            "KETOS Part Number",
            ketos_part_numbers.get(probe_type, []),
            key="ketos_part_number"
        )
        calibration_date = st.date_input("Calibration Date", datetime.today(), key="calibration_date")

    # Serial Number Generation
    service_years = service_life.get(probe_type, 1)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    expire_yymm = expire_date.strftime("%y%m")
    serial_number = f"{probe_type.split()[0]}_{expire_yymm}_{len(st.session_state.inventory) + 1:05d}"
    st.text(f"Generated Serial Number: {serial_number}")

    # Calibration Details Section
    st.markdown(
        """
        <div style="border: 2px solid #0071ba; padding: 20px; border-radius: 12px; margin-top: 20px;">
            <h2 style="font-family: Arial; color: #0071ba; text-align: center;">Calibration Details</h2>
        """,
        unsafe_allow_html=True,
    )

    # Render Calibration Details Based on Probe Type
    if probe_type == "pH Probe":
        render_ph_calibration()
    elif probe_type == "DO Probe":
        render_do_calibration()
    elif probe_type == "ORP Probe":
        render_orp_calibration()
    elif probe_type == "EC Probe":
        render_ec_calibration()

    # Close Calibration Details Card
    st.markdown('</div>', unsafe_allow_html=True)

# In the save button logic:
if st.button("Save"):
    if not manufacturer or not manufacturer_part_number or not ketos_part_number:
        st.error("Please fill in all required fields.")
    else:
        try:
            serial_number = get_next_serial_number(probe_type, manufacturing_date)
            if not serial_number:
                st.error("Error generating serial number")
              return

            new_probe = {
                "Serial Number": serial_number,
                "Type": probe_type,
                "Manufacturer": manufacturer,
                "KETOS P/N": ketos_part_number,
                "Mfg P/N": manufacturer_part_number,
                "Next Calibration": (calibration_date + timedelta(days=365)).strftime("%Y-%m-%d"),
            }

            if add_new_probe(new_probe):
                st.success("✅ New probe registered successfully!")
            else:
                st.error("❌ Error saving probe")
                
        except Exception as e:
            st.error(f"Error saving probe: {str(e)}")
