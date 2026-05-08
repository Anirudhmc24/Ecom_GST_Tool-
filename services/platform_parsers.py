import csv
import datetime
import re

class SalesParser:
    def parse(self, file_path: str):
        raise NotImplementedError("Subclasses must implement parse method")

    def _safe_float(self, val):
        try:
            if not val: return 0.0
            # Remove currency symbols and commas
            clean_val = re.sub(r'[^\d.]', '', str(val))
            return float(clean_val) if clean_val else 0.0
        except:
            return 0.0

class AmazonParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        # Amazon MTR reports often use tab or comma
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            # Try to detect delimiter
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample) if ',' in sample or '\t' in sample else 'excel'
            reader = csv.DictReader(f, dialect=dialect)
            
            for row in reader:
                order_id = row.get('Order ID') or row.get('order-id')
                if not order_id: continue
                
                total = self._safe_float(row.get('Total Amount') or row.get('total-amount') or 0)
                taxable = self._safe_float(row.get('Taxable Value') or row.get('taxable-value') or total)
                
                results.append({
                    'order_id': order_id,
                    'platform': 'Amazon',
                    'order_date': row.get('Order Date') or row.get('order-date') or datetime.date.today().isoformat(),
                    'sku': row.get('SKU') or row.get('sku') or 'UNKNOWN',
                    'quantity': self._safe_float(row.get('Quantity') or row.get('quantity') or 1),
                    'unit_price': self._safe_float(row.get('Item Price') or row.get('unit-price') or 0),
                    'taxable_value': taxable,
                    'igst_amount': self._safe_float(row.get('IGST') or row.get('igst-amount') or 0),
                    'cgst_amount': self._safe_float(row.get('CGST') or row.get('cgst-amount') or 0),
                    'sgst_amount': self._safe_float(row.get('SGST') or row.get('sgst-amount') or 0),
                    'total_amount': total,
                    'customer_state': row.get('Ship To State') or row.get('ship-state') or 'Unknown',
                    'return_status': 'Returned' if 'Refund' in str(row.get('Transaction Type', '')) else 'Delivered'
                })
        return results

class FlipkartParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get('Order_Item_Id') or row.get('Order Item Id')
                if not order_id: continue
                
                results.append({
                    'order_id': order_id,
                    'platform': 'Flipkart',
                    'order_date': row.get('Order_Date') or row.get('Order Date') or datetime.date.today().isoformat(),
                    'sku': row.get('Seller_SKU') or row.get('SKU') or 'UNKNOWN',
                    'quantity': self._safe_float(row.get('Quantity') or 1),
                    'unit_price': self._safe_float(row.get('Selling_Price') or 0),
                    'taxable_value': self._safe_float(row.get('Taxable_Value') or 0),
                    'igst_amount': self._safe_float(row.get('IGST') or 0),
                    'cgst_amount': self._safe_float(row.get('CGST') or 0),
                    'sgst_amount': self._safe_float(row.get('SGST') or 0),
                    'total_amount': self._safe_float(row.get('Total_Amount') or 0),
                    'customer_state': row.get('Customer_State') or 'Unknown',
                    'return_status': 'Delivered'
                })
        return results

class MeeshoParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get('Sub Order No') or row.get('Order ID')
                if not order_id: continue
                
                results.append({
                    'order_id': order_id,
                    'platform': 'Meesho',
                    'order_date': row.get('Order Date') or datetime.date.today().isoformat(),
                    'sku': row.get('SKU') or 'UNKNOWN',
                    'quantity': self._safe_float(row.get('Quantity') or 1),
                    'unit_price': self._safe_float(row.get('Product Price') or 0),
                    'taxable_value': self._safe_float(row.get('Taxable Value') or 0),
                    'igst_amount': self._safe_float(row.get('IGST') or 0),
                    'cgst_amount': self._safe_float(row.get('CGST') or 0),
                    'sgst_amount': self._safe_float(row.get('SGST') or 0),
                    'total_amount': self._safe_float(row.get('Total Order Value') or 0),
                    'customer_state': row.get('State') or 'Unknown',
                    'return_status': 'Returned' if row.get('Order Status') == 'Returned' else 'Delivered'
                })
        return results

def get_parser(platform: str) -> SalesParser:
    if platform.lower() == 'amazon':
        return AmazonParser()
    elif platform.lower() == 'flipkart':
        return FlipkartParser()
    elif platform.lower() == 'meesho':
        return MeeshoParser()
    else:
        raise ValueError(f"No parser available for platform: {platform}")
