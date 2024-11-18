import streamlit as st

def registration_calibration_page():
    st.title("Probe Registration & Calibration")

    # General Section: Probe Information
    st.subheader("Probe Information")
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date")
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
        ketos_part_number = st.text_input("KETOS Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH", "DO", "ORP", "EC"])
        assigned_to = st.text_input("Assigned To")
        calibration_date = st.date_input("Calibration Date")
        calibration_time = st.time_input("Calibration Time")

    # Serial Number Generation
    st.text("Generated Serial Number: AUTO_GENERATED")

    # Dynamic Sections Based on Probe Type
    if probe_type == "pH":
        render_ph_calibration()
    elif probe_type == "DO":
        render_do_calibration()
    elif probe_type == "ORP":
        render_orp_calibration()
    elif probe_type == "EC":
        render_ec_calibration()

    # Save Button
    if st.button("Save"):
        st.success("Data saved successfully!")


def render_ph_calibration():
    st.subheader("pH Calibration")
    for buffer_label, tag_color in [("pH 4", "red"), ("pH 7", "green"), ("pH 10", "blue")]:
        with st.container():
            st.markdown(f"### {buffer_label} Buffer")
            control_number = st.text_input(f"{buffer_label} Control Number")
            expiration_date = st.date_input(f"{buffer_label} Expiration Date")
            date_opened = st.date_input(f"{buffer_label} Date Opened")
            initial = st.number_input(f"{buffer_label} Initial Measurement (pH)")
            calibrated = st.number_input(f"{buffer_label} Calibrated Measurement (pH)")
            mv = st.number_input(f"{buffer_label} mV")


def render_do_calibration():
    st.subheader("DO Calibration")
    st.markdown("### Temperature")
    initial_temp = st.number_input("Initial Temperature (°C)")
    calibrated_temp = st.number_input("Calibrated Temperature (°C)")

    st.markdown("### 0% DO Calibration")
    zero_control_number = st.text_input("0% DO Control Number")
    zero_expiration_date = st.date_input("0% DO Expiration Date")
    zero_date_opened = st.date_input("0% DO Date Opened")
    zero_initial = st.number_input("0% DO Initial Measurement (%)")
    zero_calibrated = st.number_input("0% DO Calibrated Measurement (%)")

    st.markdown("### 100% DO Calibration")
    hundred_initial = st.number_input("100% DO Initial Measurement (%)")
    hundred_calibrated = st.number_input("100% DO Calibrated Measurement (%)")


def render_orp_calibration():
    st.subheader("ORP Calibration")
    st.markdown("### Temperature")
    initial_temp = st.number_input("Initial Temperature (°C)")
    calibrated_temp = st.number_input("Calibrated Temperature (°C)")

    st.markdown("### 240 mV Calibration")
    control_number = st.text_input("240 mV Control Number")
    expiration_date = st.date_input("240 mV Expiration Date")
    date_opened = st.date_input("240 mV Date Opened")
    initial_orp = st.number_input("240 mV Initial Measurement (mV)")
    calibrated_orp = st.number_input("240 mV Calibrated Measurement (mV)")


def render_ec_calibration():
    st.subheader("Specific Conductance (EC) Calibration")
    st.markdown("### Temperature")
    initial_temp = st.number_input("Initial Temperature (°C)")
    calibrated_temp = st.number_input("Calibrated Temperature (°C)")

    for label, unit in [("84 μS/cm", "Low Point"), ("1413 μS/cm", "Mid Point"), ("12.88 mS/cm", "High Point")]:
        with st.container():
            st.markdown(f"### {label} Calibration")
            control_number = st.text_input(f"{label} Control Number")
            expiration_date = st.date_input(f"{label} Expiration Date")
            date_opened = st.date_input(f"{label} Date Opened")
            initial_value = st.number_input(f"{label} Initial Measurement ({unit})")
            calibrated_value = st.number_input(f"{label} Calibrated Measurement ({unit})")
