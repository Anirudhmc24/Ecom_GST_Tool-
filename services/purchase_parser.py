import csv
import datetime
import re

class PurchaseParser:
    def _safe_float(self, val):
        try:
            if not val: return 0.0
            clean_val = re.sub(r'[^\d.]', '', str(val))
            return float(clean_val) if clean_val else 0.0
        except:
            return 0.0

    def parse(self, file_path: str):
        purchases = {}
        
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample) if ',' in sample or '\t' in sample else 'excel'
            reader = csv.DictReader(f, dialect=dialect)
            
            for row in reader:
                invoice_no = row.get('Invoice No') or row.get('invoice_no')
                if not invoice_no: continue
                
                supplier = row.get('Supplier Name') or row.get('supplier_name') or 'Unknown'
                gstin = row.get('Supplier GSTIN') or row.get('supplier_gstin') or ''
                date = row.get('Invoice Date') or row.get('invoice_date') or datetime.date.today().isoformat()
                
                sku = row.get('SKU') or row.get('sku') or 'UNKNOWN'
                qty = self._safe_float(row.get('Quantity') or row.get('quantity') or 1)
                unit_price = self._safe_float(row.get('Unit Price') or row.get('unit_price') or 0)
                gst_rate = self._safe_float(row.get('GST Rate') or row.get('gst_rate') or 0)
                if gst_rate > 1:
                    gst_rate = gst_rate / 100 # normalize to decimal
                    
                taxable = self._safe_float(row.get('Taxable Value') or row.get('taxable_value') or (qty * unit_price))
                igst = self._safe_float(row.get('IGST') or row.get('igst_amount') or 0)
                cgst = self._safe_float(row.get('CGST') or row.get('cgst_amount') or 0)
                sgst = self._safe_float(row.get('SGST') or row.get('sgst_amount') or 0)
                line_total = taxable + igst + cgst + sgst
                
                hsn_code = row.get('HSN') or row.get('hsn_code') or row.get('HSN/SAC')
                uqc = row.get('UQC') or row.get('uqc') or 'Pcs'
                
                if invoice_no not in purchases:
                    purchases[invoice_no] = {
                        'purchase': {
                            'invoice_no': invoice_no,
                            'supplier_name': supplier,
                            'supplier_gstin': gstin,
                            'invoice_date': date,
                            'taxable_value': 0,
                            'igst_amount': 0,
                            'cgst_amount': 0,
                            'sgst_amount': 0,
                            'total_amount': 0
                        },
                        'items': []
                    }
                
                # Add item
                purchases[invoice_no]['items'].append({
                    'sku': sku,
                    'quantity': qty,
                    'unit_price': unit_price,
                    'gst_rate': gst_rate,
                    'taxable_value': taxable,
                    'igst_amount': igst,
                    'cgst_amount': cgst,
                    'sgst_amount': sgst,
                    'line_total': line_total,
                    'hsn_code': hsn_code,
                    'uqc': uqc
                })
                
                # Aggregate invoice totals
                p = purchases[invoice_no]['purchase']
                p['taxable_value'] += taxable
                p['igst_amount'] += igst
                p['cgst_amount'] += cgst
                p['sgst_amount'] += sgst
                p['total_amount'] += line_total
                
        return list(purchases.values())
