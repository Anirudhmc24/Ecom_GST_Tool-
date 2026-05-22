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

    def _read_rows(self, file_path: str):
        if file_path.lower().endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file_path, dtype=str)
            df = df.fillna('')
            # Clean column names (strip whitespace)
            df.columns = [str(col).strip() for col in df.columns]
            # Clean values (strip whitespace)
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
            return df.to_dict(orient='records')
        else:
            import csv
            results = []
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                sample = f.read(2048)
                if not sample.strip():
                    return []
                f.seek(0)
                # Try to detect delimiter
                dialect = csv.Sniffer().sniff(sample) if ',' in sample or '\t' in sample else 'excel'
                reader = csv.DictReader(f, dialect=dialect)
                for row in reader:
                    cleaned_row = {str(k).strip(): str(v).strip() if v is not None else '' for k, v in row.items() if k is not None}
                    results.append(cleaned_row)
            return results

class AmazonParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        rows = self._read_rows(file_path)
        
        for row in rows:
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
                'return_status': 'Returned' if 'Refund' in str(row.get('Transaction Type', '')) else 'Delivered',
                'hsn_code': row.get('HSN') or row.get('hsn-code') or row.get('HSN/SAC'),
                'uqc': row.get('UQC') or 'Pcs',
                'gst_rate': self._safe_float(row.get('Tax Rate') or row.get('tax-rate') or row.get('GST Rate')) / 100 if row.get('Tax Rate') or row.get('tax-rate') or row.get('GST Rate') else None
            })
        return results

class FlipkartParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        rows = self._read_rows(file_path)
        for row in rows:
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
                'return_status': 'Delivered',
                'hsn_code': row.get('HSN') or row.get('HSN_Code') or row.get('HSN/SAC'),
                'uqc': row.get('UQC') or 'Pcs',
                'gst_rate': self._safe_float(row.get('GST_Rate') or row.get('Tax_Rate')) / 100 if row.get('GST_Rate') or row.get('Tax_Rate') else None
            })
        return results

class MeeshoParser(SalesParser):
    def parse(self, file_path: str):
        results = []
        rows = self._read_rows(file_path)
        for row in rows:
            order_id = row.get('Sub Order No') or row.get('Order ID') or row.get('sub_order_num') or row.get('sub_order_no')
            if not order_id: continue
            
            customer_state = row.get('State') or row.get('end_customer_state_new') or 'Unknown'
            
            # GST Rate
            raw_rate = row.get('GST Rate') or row.get('Tax Rate') or row.get('gst_rate')
            gst_rate = 0.0
            if raw_rate:
                clean_rate = re.sub(r'[^\d.]', '', str(raw_rate))
                gst_rate = float(clean_rate) if clean_rate else 0.0
                if gst_rate > 1.0:
                    gst_rate = gst_rate / 100.0
            
            quantity = self._safe_float(row.get('Quantity') or row.get('quantity') or 1)
            taxable_value = self._safe_float(row.get('Taxable Value') or row.get('taxable_value') or row.get('total_taxable_sale_value') or 0)
            
            # Tax amount
            tax_amount = self._safe_float(row.get('tax_amount') or row.get('Tax Amount') or (taxable_value * gst_rate))
            total_amount = self._safe_float(row.get('Total Order Value') or row.get('total_invoice_value') or (taxable_value + tax_amount))
            
            unit_price = self._safe_float(row.get('Product Price') or row.get('unit_price') or 0)
            if unit_price == 0 and quantity > 0:
                unit_price = total_amount / quantity
            
            # State split calculation
            is_karnataka = "karnataka" in customer_state.lower() or customer_state.strip().startswith("29")
            if is_karnataka:
                igst_amount = 0.0
                cgst_amount = tax_amount / 2.0
                sgst_amount = tax_amount / 2.0
            else:
                igst_amount = tax_amount
                cgst_amount = 0.0
                sgst_amount = 0.0
                
            order_status = str(row.get('Order Status', '')).lower() or str(row.get('transaction_type', '')).lower()
            is_return = 'return' in file_path.lower() or 'return' in order_status or 'return' in str(row.get('cancel_return_date', '')).lower()
            
            results.append({
                'order_id': order_id,
                'platform': 'Meesho',
                'order_date': row.get('cancel_return_date') or row.get('Order Date') or row.get('order_date') or row.get('manifest_date') or datetime.date.today().isoformat(),
                'sku': row.get('SKU') or row.get('sku') or 'UNKNOWN',
                'quantity': quantity,
                'unit_price': unit_price,
                'taxable_value': taxable_value,
                'igst_amount': igst_amount,
                'cgst_amount': cgst_amount,
                'sgst_amount': sgst_amount,
                'total_amount': total_amount,
                'customer_state': customer_state,
                'return_status': 'Returned' if is_return else 'Delivered',
                'hsn_code': row.get('HSN') or row.get('HSN Code') or row.get('hsn_code') or row.get('HSN/SAC'),
                'uqc': row.get('UQC') or 'Pcs',
                'gst_rate': gst_rate
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
