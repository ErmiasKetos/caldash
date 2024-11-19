import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'inventory'
if 'probes' not in st.session_state:
    st.session_state.probes = pd.DataFrame(columns=['Serial Number', 'Type', 'Manufacturer', 'Part Number', 'Location', 'Calibration Status'])

def save_data():
    st.session_state.probes.to_csv('inventory.csv', index=False)
    st.success('Data saved successfully!')

def inventory_review_page():
    st.title('Inventory Review')
    
    # Search and filter
    search = st.text_input('Search probes')
    filtered_probes = st.session_state.probes[st.session_state.probes.apply(lambda row: search.lower() in ' '.join(row.astype(str)).lower(), axis=1)]
    
    # Display probes
    for _, probe in filtered_probes.iterrows():
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            if st.button(f"{probe['Serial Number']} - {probe['Type']}"):
                st.session_state.page = 'calibration'
                st.session_state.current_probe = probe
        with col2:
            st.write(f"Manufacturer: {probe['Manufacturer']}")
            st.write(f"Location: {probe['Location']}")
        with col3:
            status_color = 'green' if probe['Calibration Status'] == 'Active' else 'red'
            st.markdown(f"<p style='color:{status_color};'>{probe['Calibration Status']}</p>", unsafe_allow_html=True)
    
    if st.button('Add New Probe'):
        st.session_state.page = 'calibration'
        st.session_state.current_probe = None

def registration_calibration_page():
    st.title('Probe Registration and Calibration')
    
    # Probe Registration
    serial_number = st.text_input('Serial Number', value=st.session_state.current_probe['Serial Number'] if st.session_state.current_probe is not None else '')
    probe_type = st.selectbox('Probe Type', ['Specific Conductance', 'pH', 'DO', 'ORP', 'Temperature'])
    manufacturer = st.text_input('Manufacturer')
    manufacturing_date = st.date_input('Manufacturing Date')
    model = st.text_input('Model (Manufacturer Part Number)')
    ketos_part_number = st.text_input('KETOS Part Number')
    location = st.text_input('Assignment/Location')
    
    # Calibration
    st.subheader('Calibration')
    calibration_date = st.date_input('Calibration Date')
    
    if probe_type == 'pH':
        ph4 = st.number_input('pH 4 Buffer Reading')
        ph7 = st.number_input('pH 7 Buffer Reading')
        ph10 = st.number_input('pH 10 Buffer Reading')
        slope = st.number_input('Slope')
    elif probe_type == 'DO':
        barometric_pressure = st.number_input('Barometric Pressure')
        temperature = st.number_input('Temperature')
        theoretical_value = st.number_input('Theoretical Value')
        qa_data = st.text_input('QA Data')
    elif probe_type == 'Specific Conductance':
        standard_value = st.number_input('Standard Value')
        temperature = st.number_input('Temperature')
        qa_check = st.text_input('QA Check')
    
    if st.button('Save'):
        new_probe = {
            'Serial Number': serial_number,
            'Type': probe_type,
            'Manufacturer': manufacturer,
            'Part Number': model,
            'Location': location,
            'Calibration Status': 'Active',
            'Last Calibration': calibration_date
        }
        st.session_state.probes = st.session_state.probes.append(new_probe, ignore_index=True)
        save_data()
        st.session_state.page = 'inventory'
    
    if st.button('Back to Inventory'):
        st.session_state.page = 'inventory'

# Main app logic
if st.session_state.page == 'inventory':
    inventory_review_page()
elif st.session_state.page == 'calibration':
    registration_calibration_page()
