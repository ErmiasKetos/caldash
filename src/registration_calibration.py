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

    # Title
    st.markdown(
        f'<h1 style="font-family: Arial, sans-serif; font-size: 32px; color: #0071ba;">📋 Probe Registration & Calibration</h1>',
        unsafe_allow_html=True,
    )

    # General Section: Probe Information
    st.markdown('<h2 style="font-family: Arial; color: #333;">Probe Information</h2>', unsafe_allow_html=True)
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
    st.markdown(
        f'<p style="font-family: Arial; font-size: 16px; color: #0071ba;"><b>Generated Serial Number:</b> {serial_number}</p>',
        unsafe_allow_html=True,
    )

    # Calibration Details - Big Card
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

    # Closing Big Card
    st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown('<div style="border: 1px solid #0071ba; padding: 20px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">pH Calibration</h3>', unsafe_allow_html=True)

    for idx, (buffer_label, color) in enumerate([("pH 4", "#f8f1f1"), ("pH 7", "#e8f8f2"), ("pH 10", "#e8f0f8")]):
        with st.container():
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
                st.number_input(f"{buffer_label} mV", value=0.0, key=f"ph_{idx}_mv")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_ec_calibration():
    st.markdown('<div style="border: 1px solid #0071ba; padding: 20px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">EC Calibration</h3>', unsafe_allow_html=True)

    # Temperature Section
    st.markdown('<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Initial Temperature (°C)", value=0.0, key="ec_temp_initial")
    with col2:
        st.number_input("Calibrated Temperature (°C)", value=0.0, key="ec_temp_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)  # Closing Temperature section

    # Calibration Points
    for idx, (label, color) in enumerate(
        [("84 μS/cm", "#f8f1f1"), ("1413 μS/cm", "#e8f8f2"), ("12.88 mS/cm", "#e8f0f8")]
    ):
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">',
            unsafe_allow_html=True,
        )
        st.markdown(f'<h4 style="font-family: Arial; color: #333;">{label} Calibration</h4>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Control Number", key=f"ec_{idx}_control_number")
            st.date_input("Expiration Date", key=f"ec_{idx}_expiration")
        with col2:
            st.date_input("Date Opened", key=f"ec_{idx}_date_opened")
            st.number_input("Initial Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_initial")
            st.number_input("Calibrated Measurement (μS/cm or mS/cm)", value=0.0, key=f"ec_{idx}_calibrated")
        st.markdown('</div>', unsafe_allow_html=True)  # Closing Calibration point section

    st.markdown('</div>', unsafe_allow_html=True)  # Closing EC Calibration container



def render_do_calibration():
    st.markdown('<div style="border: 1px solid #0071ba; padding: 20px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)

    # Temperature Section
    st.markdown('<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Initial Temperature (°C)", value=0.0, key="do_temp_initial")
    with col2:
        st.number_input("Calibrated Temperature (°C)", value=0.0, key="do_temp_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)

    # 0% DO Calibration
    st.markdown('<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">0% DO Calibration</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Control Number", key="do_0_control_number")
        st.date_input("Expiration Date", key="do_0_expiration")
    with col2:
        st.date_input("Date Opened", key="do_0_date_opened")
        st.number_input("Initial DO (%)", value=0.0, key="do_0_initial")
        st.number_input("Calibrated DO (%)", value=0.0, key="do_0_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)

    # 100% DO Calibration
    st.markdown('<div style="background-color: #e8f0f8; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">100% DO Calibration</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Initial DO (%)", value=0.0, key="do_100_initial")
    with col2:
        st.number_input("Calibrated DO (%)", value=0.0, key="do_100_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)



def render_orp_calibration():
    st.markdown('<div style="border: 1px solid #0071ba; padding: 20px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-family: Arial; color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)

    # Temperature Section
    st.markdown('<div style="background-color: #f8f1f1; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">Temperature</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Initial Temperature (°C)", value=0.0, key="orp_temp_initial")
    with col2:
        st.number_input("Calibrated Temperature (°C)", value=0.0, key="orp_temp_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)

    # 240 mV Calibration
    st.markdown('<div style="background-color: #e8f8f2; border: 1px solid #ccc; padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="font-family: Arial; color: #333;">240 mV Calibration</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Control Number", key="orp_240_control_number")
        st.date_input("Expiration Date", key="orp_240_expiration")
    with col2:
        st.date_input("Date Opened", key="orp_240_date_opened")
        st.number_input("Initial Measurement (mV)", value=0.0, key="orp_240_initial")
        st.number_input("Calibrated Measurement (mV)", value=0.0, key="orp_240_calibrated")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


