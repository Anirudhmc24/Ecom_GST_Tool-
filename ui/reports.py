import streamlit as st
import pandas as pd
import datetime
from services.report_generator import get_gstr1_b2cs, get_hsn_summary, get_sales_by_platform, get_final_hsn_data
from services.gstr1_json import generate_gstr1_json
from database.db_ecom import get_conn

def reports_page():
    st.title("📄 GST & Sales Reports")
    
    # Month/Year selection
    col1, col2 = st.columns([1, 2])
    with col1:
        current_date = datetime.date.today()
        month_options = []
        for i in range(12):
            # Safe way to subtract months
            d = (current_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1) if i > 0 else current_date.replace(day=1)
            if i > 0:
                for _ in range(i-1):
                    d = (d - datetime.timedelta(days=1)).replace(day=1)
            month_options.append(d.strftime('%Y-%m'))
        
        # Ensure current month is always first option
        if current_date.strftime('%Y-%m') not in month_options:
            month_options.insert(0, current_date.strftime('%Y-%m'))
            
        selected_month = st.selectbox("Select Month for GST Return", month_options)
    
    tab1, tab2, tab3, tab4 = st.tabs(["GSTR-1 B2CS", "HSN Summary", "Platform Analytics", "GSTR-1 JSON Export"])
    
    with tab1:
        st.subheader("B2C Small (B2CS) Summary")
        st.caption(f"Aggregated by State (Place of Supply) and Tax Rate for {selected_month}.")
        b2cs_df = get_gstr1_b2cs(selected_month)
        if not b2cs_df.empty:
            st.dataframe(b2cs_df, use_container_width=True)
            csv = b2cs_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download B2CS CSV", csv, "gstr1_b2cs.csv", "text/csv")
        else:
            st.info("No B2C sales data found.")
            
    with tab2:
        st.subheader("HSN Wise Summary")
        st.caption(f"Aggregated HSN Data for {selected_month}. Showing Final Data (Overrides applied if any).")
        hsn_df = get_final_hsn_data(selected_month)
        if not hsn_df.empty:
            st.dataframe(hsn_df, use_container_width=True)
            csv = hsn_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download HSN Summary CSV", csv, "gstr1_hsn.csv", "text/csv")
        else:
            st.info("No HSN data found.")
            
        with st.expander("🛠️ Manual HSN Override"):
            st.warning("Adding an override will APPEND to the override table for this month. If override exists, auto-calculated HSN data is ignored.")
            with st.form("hsn_override_form"):
                col1, col2, col3 = st.columns(3)
                hsn_sc = col1.text_input("HSN Code")
                uqc = col2.selectbox("UQC", ["Pcs", "PAC", "KGS", "LTR", "NOS", "BAG", "BOX", "MTR"])
                qty = col3.number_input("Total Quantity", min_value=0.0)
                
                col4, col5 = st.columns(2)
                rt = col4.number_input("GST Rate (%)", min_value=0.0)
                txval = col5.number_input("Total Taxable Value", min_value=0.0)
                
                col6, col7, col8 = st.columns(3)
                iamt = col6.number_input("IGST Amount", min_value=0.0)
                camt = col7.number_input("CGST Amount", min_value=0.0)
                samt = col8.number_input("SGST Amount", min_value=0.0)
                
                if st.form_submit_button("Save HSN Override"):
                    conn = get_conn()
                    conn.execute("""
                        INSERT INTO hsn_overrides (month_year, hsn_sc, uqc, qty, rt, txval, iamt, camt, samt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (selected_month, hsn_sc, uqc, qty, rt, txval, iamt, camt, samt))
                    conn.commit()
                    conn.close()
                    st.success("Override saved. Please refresh the page.")
            
    with tab3:
        st.subheader("Sales by Platform")
        platform_df = get_sales_by_platform()
        if not platform_df.empty:
            st.bar_chart(platform_df.set_index('platform')['Total Sales'])
            st.dataframe(platform_df, use_container_width=True)
        else:
            st.info("No sales data available for analytics.")

    with tab4:
        st.subheader("Generate Final GSTR-1 JSON")
        st.write("This JSON file is ready to be directly uploaded to the GST Portal Offline Utility.")
        
        gstin = st.text_input("Your GSTIN", value="29XXXXX0000X1Z5")
        
        # Check for missing HSNs
        conn = get_conn()
        missing_hsn = conn.execute(f"SELECT COUNT(*) FROM ecom_sales WHERE strftime('%Y-%m', order_date) = '{selected_month}' AND (hsn_code IS NULL OR hsn_code = 'UNKNOWN' OR hsn_code = '')").fetchone()[0]
        conn.close()
        
        if missing_hsn > 0:
            st.warning(f"⚠️ Warning: Found {missing_hsn} sales records in {selected_month} with missing HSN codes. Your JSON may be rejected by the portal. Please update inventory or apply overrides.")
            
        if st.button("Generate JSON"):
            try:
                # Calculate financial period, e.g., '042026'
                fp = selected_month.split('-')[1] + selected_month.split('-')[0]
                json_data = generate_gstr1_json(selected_month, gstin, fp)
                st.download_button(
                    label="Download GSTR-1 JSON",
                    data=json_data,
                    file_name=f"GSTR1_{gstin}_{selected_month}.json",
                    mime="application/json"
                )
                st.success("JSON Generated Successfully! Click download below.")
            except Exception as e:
                st.error(f"Error generating JSON: {e}")
