import pandas as pd
from database.db_ecom import get_conn

def get_gstr1_b2cs():
    """
    Returns B2CS (Business to Consumer Small) data grouped by State and Tax Rate.
    """
    conn = get_conn()
    query = """
        SELECT 
            customer_state as "Place of Supply",
            CAST(( (igst_amount + cgst_amount + sgst_amount) / taxable_value ) * 100 as INTEGER) || '%' as "Tax Rate",
            SUM(taxable_value) as "Total Taxable Value",
            SUM(igst_amount) as "Total IGST",
            SUM(cgst_amount) as "Total CGST",
            SUM(sgst_amount) as "Total SGST"
        FROM ecom_sales
        WHERE return_status != 'Cancelled'
        GROUP BY customer_state, "Tax Rate"
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_hsn_summary():
    """
    Returns HSN summary as required for GSTR-1.
    """
    conn = get_conn()
    # Join sales with inventory to get HSN codes
    query = """
        SELECT 
            i.hsn_code as "HSN",
            i.name as "Description",
            i.unit as "UQC",
            SUM(s.quantity) as "Total Quantity",
            SUM(s.taxable_value) as "Total Taxable Value",
            SUM(s.igst_amount) as "IGST",
            SUM(s.cgst_amount) as "CGST",
            SUM(s.sgst_amount) as "SGST",
            SUM(s.total_amount) as "Total Value"
        FROM ecom_sales s
        JOIN inventory i ON s.sku = i.sku
        WHERE s.return_status != 'Cancelled'
        GROUP BY i.hsn_code, i.unit
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

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
