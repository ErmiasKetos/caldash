import streamlit as st
import pandas as pd

def inventory_review():
    st.title("Inventory Review")

    # Load inventory
    file_name = "inventory.csv"
    if "inventory" not in st.session_state:
        if os.path.exists(file_name):
            st.session_state["inventory"] = pd.read_csv(file_name)
        else:
            st.session_state["inventory"] = pd.DataFrame(
                columns=["Serial Number", "Type", "Manufacturer", "KETOS P/N", "Mfg P/N", "Next Calibration", "Status"]
            )

    # Display Inventory
    st.write("Current Inventory:")
    st.dataframe(st.session_state["inventory"])

    # Export as CSV
    if st.button("Export to CSV"):
        st.session_state["inventory"].to_csv(file_name, index=False)
        st.success(f"Inventory exported as {file_name}")
