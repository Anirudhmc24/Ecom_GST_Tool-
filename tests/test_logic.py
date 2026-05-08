import unittest
import os
import sqlite3
import database.db_ecom as db
from services.report_generator import get_gstr1_b2cs, get_hsn_summary

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
        # Ensure reports can be generated without error
        b2cs = get_gstr1_b2cs()
        hsn = get_hsn_summary()
        self.assertIsNotNone(b2cs)
        self.assertIsNotNone(hsn)

if __name__ == "__main__":
    unittest.main()
