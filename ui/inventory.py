import streamlit as st
import pandas as pd
from database.db_ecom import get_all_inventory, add_inventory_item
from config.settings import GST_RATES

def inventory_page():
    st.title("📦 Inventory Management")
    
    tab1, tab2 = st.tabs(["View Stock", "Add New SKU"])
    
    with tab1:
        st.subheader("Current Inventory")
        items = get_all_inventory()
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No items in inventory. Add some to get started.")
            
    with tab2:
        st.subheader("Register New Product")
        with st.form("add_sku_form"):
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("SKU ID", placeholder="e.g. AMZ-WRLS-MSE")
                name = st.text_input("Product Name")
                hsn = st.text_input("HSN Code")
            with col2:
                unit = st.selectbox("Unit", ["Pcs", "Kg", "Box", "Set"])
                qty = st.number_input("Initial Quantity", min_value=0.0, step=1.0)
                cost = st.number_input("Cost Price (Excl GST)", min_value=0.0)
                mrp = st.number_input("Selling Price / MRP", min_value=0.0)
                gst = st.selectbox("GST Rate", list(GST_RATES.keys()))
            
            submitted = st.form_submit_button("Add SKU")
            if submitted:
                if not sku or not name or not hsn:
                    st.error("Please fill all required fields.")
                else:
                    gst_val = GST_RATES[gst]
                    success, msg = add_inventory_item(sku, name, hsn, unit, qty, cost, mrp, gst_val)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
