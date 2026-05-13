import pandas as pd
from database.db_ecom import get_conn

def get_gstr1_b2cs(month_year=None):
    """
    Returns B2CS (Business to Consumer Small) data grouped by State and Tax Rate.
    month_year should be in 'YYYY-MM' format.
    """
    conn = get_conn()
    
    where_clause = "WHERE return_status != 'Cancelled'"
    params = ()
    if month_year:
        where_clause += " AND strftime('%Y-%m', order_date) = ?"
        params = (month_year,)
        
    query = f"""
        SELECT 
            customer_state as "Place of Supply",
            CAST(( (igst_amount + cgst_amount + sgst_amount) / taxable_value ) * 100 as INTEGER) || '%' as "Tax Rate",
            SUM(taxable_value) as "Total Taxable Value",
            SUM(igst_amount) as "Total IGST",
            SUM(cgst_amount) as "Total CGST",
            SUM(sgst_amount) as "Total SGST"
        FROM ecom_sales
        {where_clause}
        GROUP BY customer_state, "Tax Rate"
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_hsn_summary(month_year=None):
    """
    Returns HSN summary as required for GSTR-1.
    Groups by HSN, UQC, and GST Rate.
    """
    conn = get_conn()
    
    where_clause = "WHERE return_status != 'Cancelled'"
    params = ()
    if month_year:
        where_clause += " AND strftime('%Y-%m', order_date) = ?"
        params = (month_year,)
        
    query = f"""
        SELECT 
            hsn_code as "HSN",
            uqc as "UQC",
            gst_rate * 100 as "GST Rate",
            SUM(quantity) as "Total Quantity",
            SUM(taxable_value) as "Total Taxable Value",
            SUM(igst_amount) as "IGST",
            SUM(cgst_amount) as "CGST",
            SUM(sgst_amount) as "SGST",
            SUM(total_amount) as "Total Value"
        FROM ecom_sales
        {where_clause}
        GROUP BY hsn_code, uqc, gst_rate
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_final_hsn_data(month_year):
    """
    Returns HSN summary with a multi-tier fallback hierarchy:
    1. HSN Overrides (Manual from DB)
    2. Sales Aggregation (Auto from bills)
    """
    conn = get_conn()
    overrides = conn.execute("SELECT * FROM hsn_overrides WHERE month_year = ?", (month_year,)).fetchall()
    conn.close()
    
    if overrides:
        df = pd.DataFrame([dict(row) for row in overrides])
        df = df.rename(columns={
            'hsn_sc': 'HSN', 'uqc': 'UQC', 'qty': 'Total Quantity', 
            'rt': 'GST Rate', 'txval': 'Total Taxable Value',
            'iamt': 'IGST', 'camt': 'CGST', 'samt': 'SGST'
        })
        return df

    # Fallback to aggregation
    return get_hsn_summary(month_year)

def get_sales_by_platform():
    conn = get_conn()
    query = """
        SELECT platform, SUM(total_amount) as "Total Sales", COUNT(order_id) as "Order Count"
        FROM ecom_sales
        GROUP BY platform
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
