import streamlit as st
import pandas as pd
import os
from services.platform_parsers import get_parser
from database.db_ecom import add_ecom_sales
from config.settings import PLATFORMS

def importer_page():
    st.title("📥 Sales & Returns Importer")
    st.write("Upload sales and returns reports from Amazon, Flipkart, or Meesho to sync your sales database and inventory.")
    
    platform = st.selectbox("Select Platform", PLATFORMS)
    
    col1, col2 = st.columns(2)
    with col1:
        sales_file = st.file_uploader(f"Choose {platform} Sales Report", type=["csv", "xlsx"], key="sales_uploader")
    with col2:
        returns_file = st.file_uploader(f"Choose {platform} Returns Report (Optional)", type=["csv", "xlsx"], key="returns_uploader")
    
    combined_records = []
    sales_count = 0
    returns_count = 0
    
    try:
        # Parse Sales
        if sales_file is not None:
            suffix = ".xlsx" if sales_file.name.endswith(".xlsx") else ".csv"
            temp_path = f"temp_{platform.lower()}_sales{suffix}"
            with open(temp_path, "wb") as f:
                f.write(sales_file.getbuffer())
            
            parser = get_parser(platform)
            sales_data = parser.parse(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            for r in sales_data:
                if r.get('return_status') != 'Returned':
                    r['return_status'] = 'Delivered'
            
            combined_records.extend(sales_data)
            sales_count = len(sales_data)
            
        # Parse Returns
        if returns_file is not None:
            suffix = ".xlsx" if returns_file.name.endswith(".xlsx") else ".csv"
            temp_path = f"temp_{platform.lower()}_returns{suffix}"
            with open(temp_path, "wb") as f:
                f.write(returns_file.getbuffer())
            
            parser = get_parser(platform)
            returns_data = parser.parse(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            for r in returns_data:
                r['return_status'] = 'Returned'
                
            combined_records.extend(returns_data)
            returns_count = len(returns_data)
            
        if combined_records:
            df = pd.DataFrame(combined_records)
            
            st.markdown("### 📊 Import Summary Preview")
            m1, m2, m3 = st.columns(3)
            m1.metric("Sales Records", sales_count)
            m2.metric("Return Records", returns_count)
            m3.metric("Total Records to Import", len(combined_records))
            
            st.subheader("Preview Consolidated Data")
            st.dataframe(df, use_container_width=True)
            
            if st.button("Confirm and Import", type="primary"):
                success, msg = add_ecom_sales(combined_records)
                if success:
                    st.success(msg)
                else:
                    st.error(f"Import failed: {msg}")
        elif sales_file is not None or returns_file is not None:
            st.warning("No valid records found in the uploaded files.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")

    # Database Maintenance Section
    st.markdown("---")
    st.subheader("🧹 Database Maintenance")
    st.write("Need to start fresh or remove imported data? Use the option below.")
    
    confirm_clear = st.checkbox("I understand that clearing the database will delete all sales, returns, purchases, and reset inventory stock.", key="confirm_clear_db")
    if confirm_clear:
        if st.button("Clear and Reset Database", type="secondary"):
            from database.db_ecom import clear_db
            try:
                clear_db()
                st.success("Database has been successfully cleared and reset!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear database: {e}")

