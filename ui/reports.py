import streamlit as st
import pandas as pd
from services.report_generator import get_gstr1_b2cs, get_hsn_summary, get_sales_by_platform

def reports_page():
    st.title("📄 GST & Sales Reports")
    
    tab1, tab2, tab3 = st.tabs(["GSTR-1 B2CS", "HSN Summary", "Platform Analytics"])
    
    with tab1:
        st.subheader("B2C Small (B2CS) Summary")
        st.caption("Aggregated by State (Place of Supply) and Tax Rate.")
        b2cs_df = get_gstr1_b2cs()
        if not b2cs_df.empty:
            st.dataframe(b2cs_df, use_container_width=True)
            csv = b2cs_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download B2CS CSV", csv, "gstr1_b2cs.csv", "text/csv")
        else:
            st.info("No B2C sales data found.")
            
    with tab2:
        st.subheader("HSN Wise Summary")
        hsn_df = get_hsn_summary()
        if not hsn_df.empty:
            st.dataframe(hsn_df, use_container_width=True)
            csv = hsn_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download HSN Summary CSV", csv, "gstr1_hsn.csv", "text/csv")
        else:
            st.info("No HSN data found. Ensure sales are mapped to SKUs in inventory.")
            
    with tab3:
        st.subheader("Sales by Platform")
        platform_df = get_sales_by_platform()
        if not platform_df.empty:
            st.bar_chart(platform_df.set_index('platform')['Total Sales'])
            st.dataframe(platform_df, use_container_width=True)
        else:
            st.info("No sales data available for analytics.")
