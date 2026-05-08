import sqlite3
import datetime
from config.settings import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables, auto-migrate old DBs, seed sample data."""
    conn = get_conn()
    c = conn.cursor()

    # ── Inventory ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sku         TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            hsn_code    TEXT    NOT NULL,
            unit        TEXT    DEFAULT 'Pcs',
            quantity    REAL    DEFAULT 0,
            cost_price  REAL    DEFAULT 0,
            mrp         REAL    NOT NULL,
            gst_rate    REAL    DEFAULT 0.18
        )
    """)

    # ── E-Commerce Sales (B2C) ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS ecom_sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        TEXT    NOT NULL,
            platform        TEXT    NOT NULL, -- Amazon, Flipkart, Meesho
            order_date      TEXT    NOT NULL,
            sku             TEXT    NOT NULL,
            quantity        REAL    NOT NULL,
            unit_price      REAL    NOT NULL,
            taxable_value   REAL    NOT NULL,
            igst_amount     REAL    DEFAULT 0,
            cgst_amount     REAL    DEFAULT 0,
            sgst_amount     REAL    DEFAULT 0,
            total_amount    REAL    NOT NULL,
            customer_state  TEXT    NOT NULL,
            return_status   TEXT    DEFAULT 'Delivered', -- Delivered, Returned, Cancelled
            FOREIGN KEY (sku) REFERENCES inventory(sku)
        )
    """)

    # ── Purchases (B2B from Shukaan Mall etc.) ──────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no      TEXT    UNIQUE NOT NULL,
            supplier_name   TEXT    NOT NULL,
            supplier_gstin  TEXT,
            invoice_date    TEXT    NOT NULL,
            taxable_value   REAL    NOT NULL,
            igst_amount     REAL    DEFAULT 0,
            cgst_amount     REAL    DEFAULT 0,
            sgst_amount     REAL    DEFAULT 0,
            total_amount    REAL    NOT NULL
        )
    """)

    # ── Purchase Items ──────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no      TEXT    NOT NULL,
            sku             TEXT    NOT NULL,
            quantity        REAL    NOT NULL,
            unit_price      REAL    NOT NULL,
            gst_rate        REAL    NOT NULL,
            taxable_value   REAL    NOT NULL,
            igst_amount     REAL    DEFAULT 0,
            cgst_amount     REAL    DEFAULT 0,
            sgst_amount     REAL    DEFAULT 0,
            line_total      REAL    NOT NULL,
            FOREIGN KEY (invoice_no) REFERENCES purchases(invoice_no),
            FOREIGN KEY (sku) REFERENCES inventory(sku)
        )
    """)

    # Seed sample inventory data if empty
    c.execute("SELECT COUNT(*) FROM inventory")
    if c.fetchone()[0] == 0:
        samples = [
            ("SKU-AMZ-001", "Wireless Mouse", "84716060", "Pcs", 50, 250, 499, 0.18),
            ("SKU-FLK-002", "Bluetooth Headphones", "85183000", "Pcs", 30, 800, 1499, 0.18),
            ("SKU-MSH-003", "Cotton T-Shirt", "61091000", "Pcs", 100, 150, 399, 0.05),
            ("SKU-GEN-004", "Desk Lamp", "94052010", "Pcs", 20, 350, 899, 0.12),
        ]
        c.executemany("""
            INSERT INTO inventory
                (sku, name, hsn_code, unit, quantity, cost_price, mrp, gst_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, samples)

    conn.commit()
    conn.close()

# ── Inventory Helpers ──────────────────────────────────────────────────
def get_all_inventory():
    conn = get_conn()
    items = conn.execute("SELECT * FROM inventory").fetchall()
    conn.close()
    return [dict(ix) for ix in items]

def add_inventory_item(sku, name, hsn_code, unit, quantity, cost_price, mrp, gst_rate):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO inventory (sku, name, hsn_code, unit, quantity, cost_price, mrp, gst_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sku, name, hsn_code, unit, quantity, cost_price, mrp, gst_rate))
        conn.commit()
        return True, "Item added successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_inventory_stock(sku, quantity_change):
    conn = get_conn()
    conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE sku = ?", (quantity_change, sku))
    conn.commit()
    conn.close()

# ── Sales Helpers ──────────────────────────────────────────────────────
def add_ecom_sales(sales_list):
    conn = get_conn()
    try:
        for sale in sales_list:
            conn.execute("""
                INSERT INTO ecom_sales (
                    order_id, platform, order_date, sku, quantity, unit_price, 
                    taxable_value, igst_amount, cgst_amount, sgst_amount, 
                    total_amount, customer_state, return_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sale['order_id'], sale['platform'], sale['order_date'], sale['sku'], 
                sale['quantity'], sale['unit_price'], sale['taxable_value'], 
                sale['igst_amount'], sale['cgst_amount'], sale['sgst_amount'], 
                sale['total_amount'], sale['customer_state'], sale['return_status']
            ))
            # Optional: Auto-deduct stock
            conn.execute("UPDATE inventory SET quantity = quantity - ? WHERE sku = ?", (sale['quantity'], sale['sku']))
        conn.commit()
        return True, f"Imported {len(sales_list)} sales successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_all_sales():
    conn = get_conn()
    sales = conn.execute("SELECT * FROM ecom_sales ORDER BY order_date DESC").fetchall()
    conn.close()
    return [dict(s) for s in sales]

# ── Purchase Helpers ───────────────────────────────────────────────────
def add_purchase_order(purchase, items):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO purchases (
                invoice_no, supplier_name, supplier_gstin, invoice_date, 
                taxable_value, igst_amount, cgst_amount, sgst_amount, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            purchase['invoice_no'], purchase['supplier_name'], purchase['supplier_gstin'], 
            purchase['invoice_date'], purchase['taxable_value'], purchase['igst_amount'], 
            purchase['cgst_amount'], purchase['sgst_amount'], purchase['total_amount']
        ))
        
        for item in items:
            conn.execute("""
                INSERT INTO purchase_items (
                    invoice_no, sku, quantity, unit_price, gst_rate, 
                    taxable_value, igst_amount, cgst_amount, sgst_amount, line_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                purchase['invoice_no'], item['sku'], item['quantity'], item['unit_price'], 
                item['gst_rate'], item['taxable_value'], item['igst_amount'], 
                item['cgst_amount'], item['sgst_amount'], item['line_total']
            ))
            # Auto-add stock
            conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE sku = ?", (item['quantity'], item['sku']))
            
        conn.commit()
        return True, "Purchase recorded and stock updated"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# ── Reconciliation Helpers ─────────────────────────────────────────────
def mark_order_as_returned(order_id, sku=None):
    """
    Marks an order as returned and adds the quantity back to inventory.
    """
    conn = get_conn()
    try:
        # Find the sale record
        if sku:
            sale = conn.execute("SELECT * FROM ecom_sales WHERE order_id = ? AND sku = ?", (order_id, sku)).fetchone()
        else:
            sale = conn.execute("SELECT * FROM ecom_sales WHERE order_id = ?", (order_id,)).fetchone()
        
        if sale:
            if sale['return_status'] != 'Returned':
                # Update status
                conn.execute("UPDATE ecom_sales SET return_status = 'Returned' WHERE id = ?", (sale['id'],))
                # Add back to inventory
                conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE sku = ?", (sale['quantity'], sale['sku']))
                conn.commit()
                return True, f"Order {order_id} marked as returned and stock adjusted."
            else:
                return False, "Order already marked as returned."
        else:
            return False, f"Order {order_id} not found in database."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_unreconciled_returns():
    """
    Returns a list of orders that are marked as 'Returned' in the sales table.
    """
    conn = get_conn()
    # For now, just return all rows with 'Returned' status
    returns = conn.execute("SELECT * FROM ecom_sales WHERE return_status = 'Returned'").fetchall()
    conn.close()
    return [dict(r) for r in returns]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
