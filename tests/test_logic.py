import unittest
import os
import sqlite3
import pandas as pd
import tempfile
import database.db_ecom as db
from services.report_generator import get_gstr1_b2cs, get_hsn_summary
from services.gstr1_json import generate_gstr1_json

class TestEcomTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override DB_PATH for testing
        cls.test_db = "test_ecom_data.db"
        db.DB_PATH = os.path.abspath(cls.test_db)
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_inventory_and_stock_flow(self):
        # 1. Add Item
        sku = "TEST-SKU-001"
        db.add_inventory_item(sku, "Test Product", "123456", "Pcs", 10, 100, 200, 0.18)
        
        inv = db.get_all_inventory()
        item = next(i for i in inv if i['sku'] == sku)
        self.assertEqual(item['quantity'], 10)

        # 2. Add Sale (Should deduct stock)
        sale = {
            'order_id': 'ORD-001', 'platform': 'Amazon', 'order_date': '2023-01-01',
            'sku': sku, 'quantity': 2, 'unit_price': 200, 'taxable_value': 169.49,
            'igst_amount': 30.51, 'cgst_amount': 0, 'sgst_amount': 0,
            'total_amount': 200, 'customer_state': 'Maharashtra', 'return_status': 'Delivered'
        }
        db.add_ecom_sales([sale])
        
        inv = db.get_all_inventory()
        item = next(i for i in inv if i['sku'] == sku)
        self.assertEqual(item['quantity'], 8)

        # 3. Mark as Returned (Should add stock back)
        db.mark_order_as_returned('ORD-001', sku)
        inv = db.get_all_inventory()
        item = next(i for i in inv if i['sku'] == sku)
        self.assertEqual(item['quantity'], 10)

    def test_reporting_aggregation(self):
        # Clear database first
        conn = db.get_conn()
        conn.execute("DELETE FROM ecom_sales")
        conn.commit()
        conn.close()

        sku = "TEST-SKU-NET"
        # Seed 2 sales: one Delivered, one Returned
        sale1 = {
            'order_id': 'ORD-DEL', 'platform': 'Meesho', 'order_date': '2026-04-01',
            'sku': sku, 'quantity': 2, 'unit_price': 100, 'taxable_value': 200.0,
            'igst_amount': 10.0, 'cgst_amount': 0.0, 'sgst_amount': 0.0,
            'total_amount': 210.0, 'customer_state': 'Tamil Nadu', 'return_status': 'Delivered',
            'hsn_code': '392410', 'uqc': 'Pcs', 'gst_rate': 0.05
        }
        sale2 = {
            'order_id': 'ORD-RET', 'platform': 'Meesho', 'order_date': '2026-04-09',
            'sku': sku, 'quantity': 1, 'unit_price': 100, 'taxable_value': 100.0,
            'igst_amount': 5.0, 'cgst_amount': 0.0, 'sgst_amount': 0.0,
            'total_amount': 105.0, 'customer_state': 'Tamil Nadu', 'return_status': 'Returned',
            'hsn_code': '392410', 'uqc': 'Pcs', 'gst_rate': 0.05
        }
        db.add_ecom_sales([sale1, sale2])

        # Verify B2CS nets off: Taxable value should be 200 - 100 = 100
        b2cs = get_gstr1_b2cs('2026-04')
        self.assertEqual(len(b2cs), 1)
        self.assertEqual(b2cs.iloc[0]['Total Taxable Value'], 100.0)
        self.assertEqual(b2cs.iloc[0]['Total IGST'], 5.0)

        # Verify HSN nets off: Quantity should be 2 - 1 = 1, Taxable value = 100
        hsn = get_hsn_summary('2026-04')
        self.assertEqual(len(hsn), 1)
        self.assertEqual(hsn.iloc[0]['Total Quantity'], 1.0)
        self.assertEqual(hsn.iloc[0]['Total Taxable Value'], 100.0)

    def test_xlsx_parsing_sales(self):
        from services.platform_parsers import AmazonParser, FlipkartParser, MeeshoParser

        # 1. Test Amazon Parser XLSX
        amazon_data = [{
            'Order ID': 'AMZ-XLS-001',
            'Order Date': '2026-05-01',
            'SKU': 'SKU-AMZ-001',
            'Quantity': '2',
            'Total Amount': '1000',
            'Taxable Value': '847.46',
            'IGST': '152.54',
            'CGST': '0',
            'SGST': '0',
            'Ship To State': 'Karnataka',
            'Transaction Type': 'Order',
            'HSN': '84716060',
            'UQC': 'Pcs',
            'GST Rate': '18'
        }]
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
        
        try:
            pd.DataFrame(amazon_data).to_excel(temp_path, index=False)
            parser = AmazonParser()
            parsed = parser.parse(temp_path)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]['order_id'], 'AMZ-XLS-001')
            self.assertEqual(parsed[0]['platform'], 'Amazon')
            self.assertEqual(parsed[0]['quantity'], 2.0)
            self.assertEqual(parsed[0]['total_amount'], 1000.0)
            self.assertEqual(parsed[0]['hsn_code'], '84716060')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # 2. Test Flipkart Parser XLSX
        flipkart_data = [{
            'Order Item Id': 'FLK-XLS-001',
            'Order Date': '2026-05-02',
            'SKU': 'SKU-FLK-002',
            'Quantity': '1',
            'Selling_Price': '1500',
            'Taxable_Value': '1271.19',
            'IGST': '228.81',
            'CGST': '0',
            'SGST': '0',
            'Total_Amount': '1500',
            'Customer_State': 'Delhi',
            'HSN_Code': '85183000',
            'GST_Rate': '18'
        }]
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
            
        try:
            pd.DataFrame(flipkart_data).to_excel(temp_path, index=False)
            parser = FlipkartParser()
            parsed = parser.parse(temp_path)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]['order_id'], 'FLK-XLS-001')
            self.assertEqual(parsed[0]['platform'], 'Flipkart')
            self.assertEqual(parsed[0]['quantity'], 1.0)
            self.assertEqual(parsed[0]['total_amount'], 1500.0)
            self.assertEqual(parsed[0]['hsn_code'], '85183000')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_xlsx_parsing_purchases(self):
        from services.purchase_parser import PurchaseParser

        purchase_data = [{
            'Invoice No': 'INV-XLS-001',
            'Supplier Name': 'Supplier A',
            'Supplier GSTIN': '29ABCDE1234F1Z5',
            'Invoice Date': '2026-05-03',
            'SKU': 'SKU-AMZ-001',
            'Quantity': '10',
            'Unit Price': '200',
            'GST Rate': '18',
            'Taxable Value': '2000',
            'IGST': '0',
            'CGST': '180',
            'SGST': '180',
            'HSN': '84716060',
            'UQC': 'Pcs'
        }]

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
            
        try:
            pd.DataFrame(purchase_data).to_excel(temp_path, index=False)
            parser = PurchaseParser()
            parsed = parser.parse(temp_path)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]['purchase']['invoice_no'], 'INV-XLS-001')
            self.assertEqual(parsed[0]['purchase']['total_amount'], 2360.0)
            self.assertEqual(len(parsed[0]['items']), 1)
            self.assertEqual(parsed[0]['items'][0]['sku'], 'SKU-AMZ-001')
            self.assertEqual(parsed[0]['items'][0]['quantity'], 10.0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_gstr1_json_generation(self):
        import json

        # Seed data for reporting
        sku = "SKU-AMZ-001"
        # Make sure inventory item exists
        try:
            db.add_inventory_item(sku, "Wireless Mouse", "84716060", "Pcs", 50, 250, 499, 0.18)
        except Exception:
            pass # ignore unique constraint if already seeded

        # Clear existing sales first to avoid interference
        conn = db.get_conn()
        conn.execute("DELETE FROM ecom_sales")
        conn.commit()
        conn.close()

        sale = {
            'order_id': 'ORD-JSON-001', 'platform': 'Amazon', 'order_date': '2026-05-01',
            'sku': sku, 'quantity': 1, 'unit_price': 100, 'taxable_value': 84.75,
            'igst_amount': 15.25, 'cgst_amount': 0, 'sgst_amount': 0,
            'total_amount': 100, 'customer_state': 'MH-Maharashtra', 'return_status': 'Delivered',
            'hsn_code': '84716060', 'uqc': 'Pcs', 'gst_rate': 0.18
        }
        db.add_ecom_sales([sale])

        # Generate JSON
        gstin = "29XXXXX0000X1Z5"
        fp = "052026"
        month_year = "2026-05"
        
        json_str = generate_gstr1_json(month_year, gstin, fp)
        payload = json.loads(json_str)

        self.assertEqual(payload['gstin'], gstin)
        self.assertEqual(payload['fp'], fp)
        self.assertEqual(payload['version'], 'GST3.0.0')
        self.assertTrue('b2cs' in payload)
        self.assertTrue('hsn' in payload)
        
        # Verify B2CS data
        b2cs_item = payload['b2cs'][0]
        self.assertEqual(b2cs_item['pos'], '27')
        self.assertEqual(b2cs_item['rt'], 18.0)
        self.assertEqual(b2cs_item['txval'], 84.75)
        self.assertEqual(b2cs_item['iamt'], 15.26)
        
        # Verify HSN data
        hsn_item = payload['hsn']['data'][0]
        self.assertEqual(hsn_item['hsn_sc'], '84716060')
        self.assertEqual(hsn_item['qty'], 1.0)
        self.assertEqual(hsn_item['rt'], 18.0)

if __name__ == "__main__":
    unittest.main()
