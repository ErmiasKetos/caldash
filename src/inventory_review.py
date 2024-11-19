import streamlit as st
import pandas as pd

def inventory_review_page():
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
    
    st.title("Inventory Review")

    # Load inventory data from session state
    inventory_data = st.session_state["inventory"]

    # Display inventory table
    st.dataframe(inventory_data)

    # Option to download inventory as CSV
    st.download_button(
        "Download Inventory as CSV",
        data=inventory_data.to_csv(index=False),
        file_name="inventory.csv",
        mime="text/csv",
    )
