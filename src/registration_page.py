import streamlit as st
from datetime import datetime, timedelta
from .inventory_manager import get_next_serial_number, add_new_probe

def registration_page():
    """Probe Registration Page"""
    st.markdown('<h1 style="font-family: Arial; color: #0071ba;">📋 Probe Registration</h1>', unsafe_allow_html=True)

    # Input Fields
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
        ketos_part_number = st.text_input("KETOS Part Number")

    # Generate Serial Number
    serial_number = get_next_serial_number(probe_type, manufacturing_date)
    st.markdown(f"Generated Serial Number: **{serial_number}**")

    # Save Button
    if st.button("Register Probe"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("Please fill in all required fields.")
            return

        # Save basic probe data
        probe_data = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Next Calibration": None,
            "Status": None,
            "Entry Date": datetime.now().strftime("%Y-%m-%d"),
            "Last Modified": datetime.now().strftime("%Y-%m-%d"),
            "Change Date": None,
        }

        if add_new_probe(probe_data):
            st.success(f"✅ Probe {serial_number} registered successfully!")
        else:
            st.error("❌ Failed to register probe.")
