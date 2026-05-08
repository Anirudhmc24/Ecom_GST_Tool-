import streamlit as st
from config.settings import SHOP_NAME
from database.db_ecom import init_db

# Initialize Database
init_db()

st.set_page_config(page_title=f"{SHOP_NAME} - GST Tool", layout="wide")

def main():
    st.sidebar.title(f"📦 {SHOP_NAME}")
    st.sidebar.markdown("---")
    
    menu = ["Dashboard", "Inventory Management", "Sales Importer", "Return Reconciliation", "Purchase Entry", "Reports"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Dashboard":
        st.title("📊 Business Dashboard")
        st.info("Welcome to the E-Commerce GST and Inventory Tool.")
        
        from database.db_ecom import get_all_inventory, get_all_sales
        inventory = get_all_inventory()
        sales = get_all_sales()
        
        total_sales_amount = sum(s['total_amount'] for s in sales)
        total_skus = len(inventory)
        pending_returns = sum(1 for s in sales if s['return_status'] == 'Returned')

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sales (INR)", f"₹ {total_sales_amount:,.2f}")
        with col2:
            st.metric("Total SKU Count", total_skus)
        with col3:
            st.metric("Pending Returns", pending_returns)

    elif choice == "Inventory Management":
        from ui.inventory import inventory_page
        inventory_page()

    elif choice == "Sales Importer":
        from ui.importer import importer_page
        importer_page()

    elif choice == "Return Reconciliation":
        from ui.reconciliation import reconciliation_page
        reconciliation_page()

    elif choice == "Purchase Entry":
        from ui.purchases import purchases_page
        purchases_page()
        
    elif choice == "Reports":
        from ui.reports import reports_page
        reports_page()

if __name__ == "__main__":
    main()
