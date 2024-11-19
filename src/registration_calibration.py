from src.inventory_manager import add_new_probe, get_next_serial_number

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
