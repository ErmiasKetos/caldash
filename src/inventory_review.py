import streamlit as st
import pandas as pd

def inventory_review_page():
    st.title("Inventory Review")

    # Load inventory data from session state
    inventory_data = st.session_state.get("inventory", pd.DataFrame())

    # Display inventory table
    st.dataframe(inventory_data)

    # Option to download inventory as CSV
    st.download_button(
        "Download Inventory as CSV",
        data=inventory_data.to_csv(index=False),
        file_name="inventory.csv",
        mime="text/csv",
    )
