import streamlit as st
import pandas as pd
from services.platform_parsers import get_parser
from database.db_ecom import add_ecom_sales
from config.settings import PLATFORMS

def importer_page():
    st.title("📥 Sales Importer")
    st.write("Upload CSV sales reports from Amazon, Flipkart, or Meesho to sync your sales and inventory.")
    
    platform = st.selectbox("Select Platform", PLATFORMS)
    uploaded_file = st.file_uploader(f"Choose {platform} CSV Report", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Save file temporarily to parse
            temp_path = f"temp_{platform.lower()}_report.csv"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.info("Parsing file...")
            parser = get_parser(platform)
            sales_data = parser.parse(temp_path)
            
            if sales_data:
                df = pd.DataFrame(sales_data)
                st.subheader("Preview Data")
                st.dataframe(df.head(), use_container_width=True)
                
                st.write(f"Found {len(sales_data)} records.")
                
                if st.button("Confirm and Import"):
                    success, msg = add_ecom_sales(sales_data)
                    if success:
                        st.success(msg)
                    else:
                        st.error(f"Import failed: {msg}")
            else:
                st.warning("No valid sales records found in the uploaded file.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
