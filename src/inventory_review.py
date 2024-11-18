import streamlit as st
import pandas as pd

def inventory_review_page():
    st.title("Inventory Review")

    # Mock data (replace with your data source)
    data = pd.DataFrame({
        "Serial Number": ["pH_2211_00001"],
        "Manufacturer": ["Test Manufacturer"],
        "Calibration Date": ["2023-01-01"],
        "Status": ["Active"]
    })

    # Display the inventory table
    st.dataframe(data)

    # Add functionality to download inventory as CSV
    st.download_button(
        "Download Inventory as CSV",
        data=data.to_csv(index=False),
        file_name="inventory.csv",
        mime="text/csv"
    )
