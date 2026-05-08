import streamlit as st
import pandas as pd
from database.db_ecom import get_unreconciled_returns, mark_order_as_returned

def reconciliation_page():
    st.title("🔄 Return Reconciliation")
    st.write("Match returned orders with original sales to adjust inventory and GST liability.")
    
    tab1, tab2 = st.tabs(["Manual Recon", "Recent Returns"])
    
    with tab1:
        st.subheader("Mark Order as Returned")
        with st.form("manual_recon_form"):
            order_id = st.text_input("Order ID", placeholder="Enter the Order ID from Platform")
            sku = st.text_input("SKU (Optional)", placeholder="Enter SKU if specific item was returned")
            
            submitted = st.form_submit_button("Reconcile and Adjust Stock")
            if submitted:
                if not order_id:
                    st.error("Please provide an Order ID.")
                else:
                    success, msg = mark_order_as_returned(order_id, sku if sku else None)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                        
    with tab2:
        st.subheader("Automatically Detected Returns")
        st.caption("These returns were identified during CSV imports.")
        returns = get_unreconciled_returns()
        if returns:
            df = pd.DataFrame(returns)
            st.dataframe(df[['order_id', 'platform', 'order_date', 'sku', 'quantity', 'total_amount', 'customer_state']], use_container_width=True)
        else:
            st.info("No returns detected in the current data.")
