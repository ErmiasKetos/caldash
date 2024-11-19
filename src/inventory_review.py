import streamlit as st
import pandas as pd
from datetime import datetime
from .inventory_manager import (
    initialize_inventory,
    get_filtered_inventory,
    style_inventory_dataframe,
    update_probe_status,
    save_inventory,
    STATUS_COLORS
)

def inventory_review_page():
    """Display and manage inventory"""
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    
    # Initialize inventory if needed
    initialize_inventory()
    
    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Instock", "Shipped", "Scraped"]
    )
    
    # Get filtered inventory
    filtered_inventory = get_filtered_inventory(status_filter)
    
    # Display inventory with styling
    if not filtered_inventory.empty:
        st.dataframe(
            style_inventory_dataframe(filtered_inventory),
            height=400,
            use_container_width=True
        )
    else:
        st.info("No records found for the selected filter.")
    
    # Status update section
    if not st.session_state.inventory.empty:
        st.markdown("### Update Probe Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_probe = st.selectbox(
                "Select Probe",
                st.session_state.inventory['Serial Number'].tolist()
            )
            
            if selected_probe:
                probe_info = st.session_state.inventory[
                    st.session_state.inventory['Serial Number'] == selected_probe
                ].iloc[0]
                st.info(f"Current Status: {probe_info['Status']}")
        
        with col2:
            current_status = st.session_state.inventory[
                st.session_state.inventory['Serial Number'] == selected_probe
            ]['Status'].iloc[0]
            
            new_status = st.selectbox(
                "New Status",
                ["Instock", "Shipped", "Scraped"],
                index=["Instock", "Shipped", "Scraped"].index(current_status)
            )
            
            # Preview color for selected status
            st.markdown(
                f'<div style="background-color: {STATUS_COLORS[new_status]}; '
                f'padding: 10px; border-radius: 5px; margin-top: 10px;">'
                f'Selected status color preview</div>',
                unsafe_allow_html=True
            )
        
        # Update button with confirmation
        if st.button("Update Status"):
            if new_status != current_status:
                with st.spinner("Updating status..."):
                    if update_probe_status(selected_probe, new_status):
                        st.success(f"✅ Updated status of {selected_probe} to {new_status}")
                        # Re-save inventory
                        save_inventory(st.session_state.inventory)
                        # Rerun to refresh the page
                        st.experimental_rerun()
                    else:
                        st.error("Failed to update status")
            else:
                st.warning("No status change selected")

    # Download section
    st.markdown("### Download Inventory")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download filtered inventory
        csv = filtered_inventory.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Inventory",
            data=csv,
            file_name=f"inventory_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    
    with col2:
        # Download full inventory
        full_csv = st.session_state.inventory.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Full Inventory",
            data=full_csv,
            file_name=f"inventory_full_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # Debug information
    with st.expander("Debug Info", expanded=False):
        st.write({
            "Total Records": len(st.session_state.inventory),
            "Filtered Records": len(filtered_inventory),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Drive Status": 'drive_manager' in st.session_state
        })
