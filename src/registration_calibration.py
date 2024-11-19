import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
from .drive_manager import DriveManager
from .inventory_manager import (
    add_new_probe,
    get_next_serial_number,
    save_inventory,
    STATUS_COLORS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Autofill options for KETOS Part Number
KETOS_PART_NUMBERS = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes (in years)
SERVICE_LIFE = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

# Add Status Colors definition
STATUS_COLORS = {
    'Instock': '#90EE90',  # Green
    'Shipped': '#ADD8E6',  # Light Blue
    'Scraped': '#FFB6C6'   # Red
}

def render_ph_calibration():
    """Render pH probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">pH Calibration</h3>', unsafe_allow_html=True)
    ph_data = {}

    for idx, (buffer_label, color) in enumerate([("pH 4", "#f8f1f1"), ("pH 7", "#e8f8f2"), ("pH 10", "#e8f0f8")]):
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{buffer_label} Buffer</h4>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            ph_data[f"{buffer_label}_control"] = st.text_input(
                f"{buffer_label} Control Number",
                key=f"ph_{idx}_control_number"
            )
            ph_data[f"{buffer_label}_exp"] = st.date_input(
                f"{buffer_label} Expiration Date",
                key=f"ph_{idx}_expiration"
            )
        with col2:
            ph_data[f"{buffer_label}_opened"] = st.date_input(
                f"{buffer_label} Date Opened",
                key=f"ph_{idx}_date_opened"
            )
            ph_data[f"{buffer_label}_initial"] = st.number_input(
                f"{buffer_label} Initial Measurement (pH)",
                value=0.0,
                key=f"ph_{idx}_initial"
            )
            ph_data[f"{buffer_label}_calibrated"] = st.number_input(
                f"{buffer_label} Calibrated Measurement (pH)",
                value=0.0,
                key=f"ph_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return ph_data

def render_do_calibration():
    """Render DO probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)
    do_data = {}

    # Temperature section
    st.markdown('<h4 style="font-family: Arial; color: #0071ba;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        do_data['temp_initial'] = st.number_input(
            "Initial Temperature (°C)",
            value=0.0,
            key="do_temp_initial"
        )
    with col2:
        do_data['temp_calibrated'] = st.number_input(
            "Calibrated Temperature (°C)",
            value=0.0,
            key="do_temp_calibrated"
        )

    # DO Calibration sections
    for idx, label in enumerate(["0% DO Calibration", "100% DO Calibration"]):
        st.markdown(
            f'<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label}</h4>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            do_data[f"do_{idx}_control"] = st.text_input(
                f"{label} Control Number",
                key=f"do_{idx}_control_number"
            )
            do_data[f"do_{idx}_exp"] = st.date_input(
                f"{label} Expiration Date",
                key=f"do_{idx}_expiration"
            )
        with col2:
            do_data[f"do_{idx}_opened"] = st.date_input(
                f"{label} Date Opened",
                key=f"do_{idx}_date_opened"
            )
            do_data[f"do_{idx}_initial"] = st.number_input(
                f"{label} Initial Measurement (%)",
                value=0.0,
                key=f"do_{idx}_initial"
            )
            do_data[f"do_{idx}_calibrated"] = st.number_input(
                f"{label} Calibrated Measurement (%)",
                value=0.0,
                key=f"do_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return do_data

def render_orp_calibration():
    """Render ORP probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)
    orp_data = {}

    col1, col2 = st.columns(2)
    with col1:
        orp_data['control_number'] = st.text_input("Control Number", key="orp_control_number")
        orp_data['expiration'] = st.date_input("Expiration Date", key="orp_expiration")
    with col2:
        orp_data['date_opened'] = st.date_input("Date Opened", key="orp_date_opened")
        orp_data['initial'] = st.number_input("Initial Measurement (mV)", value=0.0, key="orp_initial")
        orp_data['calibrated'] = st.number_input("Calibrated Measurement (mV)", value=0.0, key="orp_calibrated")
    return orp_data

def render_ec_calibration():
    """Render EC probe calibration form"""
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">EC Calibration</h3>', unsafe_allow_html=True)
    ec_data = {}

    for idx, label in enumerate(["84 μS/cm", "1413 μS/cm", "12.88 mS/cm"]):
        st.markdown(
            f'<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            f'<h4 style="font-family: Arial; color: #333;">{label} Calibration</h4>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            ec_data[f"ec_{idx}_control"] = st.text_input(
                f"{label} Control Number",
                key=f"ec_{idx}_control_number"
            )
            ec_data[f"ec_{idx}_exp"] = st.date_input(
                f"{label} Expiration Date",
                key=f"ec_{idx}_expiration"
            )
        with col2:
            ec_data[f"ec_{idx}_opened"] = st.date_input(
                f"{label} Date Opened",
                key=f"ec_{idx}_date_opened"
            )
            ec_data[f"ec_{idx}_initial"] = st.number_input(
                f"{label} Initial Measurement (μS/cm or mS/cm)",
                value=0.0,
                key=f"ec_{idx}_initial"
            )
            ec_data[f"ec_{idx}_calibrated"] = st.number_input(
                f"{label} Calibrated Measurement (μS/cm or mS/cm)",
                value=0.0,
                key=f"ec_{idx}_calibrated"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    return ec_data

def registration_calibration_page():
    """Main page for probe registration and calibration"""
    # Code continues here with no indentation errors...
    pass

if __name__ == "__main__":
    registration_calibration_page()
