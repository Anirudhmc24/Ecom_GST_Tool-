import unittest
import json
import re
from services.platform_parsers import AmazonParser
from services.gstr1_json import generate_gstr1_json
import pandas as pd
from unittest.mock import patch

class TestGSTR1JSON(unittest.TestCase):
    def test_safe_float_preserves_negative(self):
        parser = AmazonParser()
        # Should clean currency and keep negative signs
        self.assertEqual(parser._safe_float("-$123.45"), -123.45)
        self.assertEqual(parser._safe_float("-150.48"), -150.48)
        self.assertEqual(parser._safe_float("1,234.56"), 1234.56)
        self.assertEqual(parser._safe_float(""), 0.0)
        self.assertEqual(parser._safe_float(None), 0.0)

    @patch('services.gstr1_json.get_gstr1_b2cs')
    @patch('services.gstr1_json.get_final_hsn_data')
    def test_generate_json_filters_and_omits(self, mock_hsn, mock_b2cs):
        # Setup mock data for B2CS (contains positive, zero, and negative taxable values)
        mock_b2cs.return_value = pd.DataFrame([
            {
                "Place of Supply": "10-Delhi",
                "Tax Rate": "5%",
                "Total Taxable Value": -114.29,
                "Total IGST": -5.71,
                "Total CGST": 0.0,
                "Total SGST": 0.0
            },
            {
                "Place of Supply": "24-Gujarat",
                "Tax Rate": "5%",
                "Total Taxable Value": 173.33,
                "Total IGST": 8.67,
                "Total CGST": 0.0,
                "Total SGST": 0.0
            },
            {
                "Place of Supply": "29-Karnataka",
                "Tax Rate": "18%",
                "Total Taxable Value": 0.0,
                "Total IGST": 0.0,
                "Total CGST": 0.0,
                "Total SGST": 0.0
            }
        ])

        # Setup mock data for HSN (contains positive and negative values)
        mock_hsn.return_value = pd.DataFrame([
            {
                "HSN": "330499",
                "UQC": "Pcs",
                "Total Quantity": 2.0,
                "GST Rate": 0.18,
                "Total Taxable Value": 355.93,
                "IGST": 64.07,
                "CGST": 0.0,
                "SGST": 0.0
            },
            {
                "HSN": "3924",
                "UQC": "Pcs",
                "Total Quantity": -4.0,
                "GST Rate": 0.05,
                "Total Taxable Value": -264.76,
                "IGST": -13.24,
                "CGST": 0.0,
                "SGST": 0.0
            }
        ])

        # Generate GSTR-1 JSON
        gstin = "29QHBPS0590F1ZT"
        result_str = generate_gstr1_json("2026-04", gstin, "042026")
        result = json.loads(result_str)

        # Assertions
        # 1. Base keys should exist
        self.assertEqual(result["gstin"], gstin)
        self.assertEqual(result["fp"], "042026")
        self.assertEqual(result["gt"], 0.0)
        self.assertEqual(result["cur_gt"], 0.0)

        # 2. Empty tables should be omitted entirely
        self.assertNotIn("b2b", result)
        self.assertNotIn("b2cl", result)
        self.assertNotIn("cdnr", result)
        self.assertNotIn("cdnur", result)
        self.assertNotIn("nil", result)

        # 3. B2CS should only contain the positive entry
        self.assertIn("b2cs", result)
        self.assertEqual(len(result["b2cs"]), 1)
        self.assertEqual(result["b2cs"][0]["pos"], "24")
        self.assertEqual(result["b2cs"][0]["rt"], 5.0)
        self.assertEqual(result["b2cs"][0]["txval"], 173.33)
        self.assertEqual(result["b2cs"][0]["iamt"], 8.67)
        self.assertEqual(result["b2cs"][0]["camt"], 0.0)
        self.assertEqual(result["b2cs"][0]["samt"], 0.0)

        # 4. HSN should only contain the positive entry and 'num' should be 1
        self.assertIn("hsn", result)
        self.assertEqual(len(result["hsn"]["data"]), 1)
        self.assertEqual(result["hsn"]["data"][0]["hsn_sc"], "330499")
        self.assertEqual(result["hsn"]["data"][0]["qty"], 2.0)
        self.assertEqual(result["hsn"]["data"][0]["num"], 1)
        self.assertEqual(result["hsn"]["data"][0]["rt"], 18.0)
        self.assertEqual(result["hsn"]["data"][0]["iamt"], 64.07)
        self.assertEqual(result["hsn"]["data"][0]["camt"], 0.0)
        self.assertEqual(result["hsn"]["data"][0]["samt"], 0.0)

if __name__ == '__main__':
    unittest.main()
