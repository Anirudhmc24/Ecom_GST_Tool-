import streamlit as st
import pandas as pd
from database.db_ecom import get_all_inventory, add_purchase_order
from config.settings import GST_RATES

def purchases_page():
    st.title("🛒 Purchase Entry")
    st.write("Record B2B purchases to update stock and track GST inputs.")
    
    with st.form("purchase_form"):
        col1, col2 = st.columns(2)
        with col1:
            invoice_no = st.text_input("Invoice Number")
            supplier = st.text_input("Supplier Name (e.g. Shukaan Mall)")
            gstin = st.text_input("Supplier GSTIN")
        with col2:
            date = st.date_input("Invoice Date")
            total_taxable = st.number_input("Total Taxable Value", min_value=0.0)
            total_gst = st.number_input("Total GST Amount", min_value=0.0)
            total_amount = st.number_input("Grand Total (Incl GST)", min_value=0.0)
            
        st.subheader("Items in Purchase")
        inventory = get_all_inventory()
        skus = [item['sku'] for item in inventory]
        
        # Simple dynamic item list (for MVP, we use one item at a time or a simple list)
        # In a real app, this would be a dynamic table
        selected_sku = st.selectbox("Select Item SKU", skus if skus else ["Add items in Inventory first"])
        qty = st.number_input("Quantity Purchased", min_value=1.0)
        unit_price = st.number_input("Unit Cost Price (Excl GST)", min_value=0.0)
        gst_rate = st.selectbox("GST Rate for Item", list(GST_RATES.keys()))
        
        submitted = st.form_submit_button("Record Purchase")
        
        if submitted:
            if not invoice_no or not supplier or not skus:
                st.error("Missing required fields or inventory items.")
            else:
                purchase = {
                    'invoice_no': invoice_no,
                    'supplier_name': supplier,
                    'supplier_gstin': gstin,
                    'invoice_date': str(date),
                    'taxable_value': total_taxable,
                    'igst_amount': total_gst if gstin[:2] != "29" else 0, # Simple logic for KA
                    'cgst_amount': total_gst/2 if gstin[:2] == "29" else 0,
                    'sgst_amount': total_gst/2 if gstin[:2] == "29" else 0,
                    'total_amount': total_amount
                }
                
                # Mocking items list for now based on form input
                # Real implementation would allow multiple items
                gst_val = GST_RATES[gst_rate]
                item_taxable = qty * unit_price
                item_gst = item_taxable * gst_val
                
                items = [{
                    'sku': selected_sku,
                    'quantity': qty,
                    'unit_price': unit_price,
                    'gst_rate': gst_val,
                    'taxable_value': item_taxable,
                    'igst_amount': item_gst if gstin[:2] != "29" else 0,
                    'cgst_amount': item_gst/2 if gstin[:2] == "29" else 0,
                    'sgst_amount': item_gst/2 if gstin[:2] == "29" else 0,
                    'line_total': item_taxable + item_gst
                }]
                
                success, msg = add_purchase_order(purchase, items)
                if success:
                    st.success(msg)
                else:
                    st.error(f"Error: {msg}")
