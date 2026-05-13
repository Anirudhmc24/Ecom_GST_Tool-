import json
from services.report_generator import get_gstr1_b2cs, get_final_hsn_data

def generate_gstr1_json(month_year, gstin, fp):
    """
    Generates the exact GSTR-1 JSON payload structure required by the GST portal.
    month_year: YYYY-MM
    gstin: string
    fp: Financial Period (e.g., '042026' for April 2026)
    """
    
    # B2CS Data
    b2cs_df = get_gstr1_b2cs(month_year)
    b2cs_list = []
    if not b2cs_df.empty:
        for _, row in b2cs_df.iterrows():
            pos = str(row['Place of Supply'])[:2] if row['Place of Supply'] and row['Place of Supply'][0].isdigit() else '29' # Defaulting to KA if unparseable state code, user should fix data ideally
            if '-' in str(row['Place of Supply']):
                pos = str(row['Place of Supply']).split('-')[0].strip()
                
            rate = float(str(row['Tax Rate']).replace('%', '')) if row['Tax Rate'] else 0.0
            b2cs_list.append({
                "sply_ty": "INTRA" if pos == gstin[:2] else "INTER",
                "rt": rate,
                "typ": "OE",
                "pos": pos,
                "txval": round(float(row['Total Taxable Value']), 2),
                "iamt": round(float(row['Total IGST']), 2),
                "camt": round(float(row['Total CGST']), 2),
                "samt": round(float(row['Total SGST']), 2),
                "csamt": 0.0
            })

    # HSN Data
    hsn_df = get_final_hsn_data(month_year)
    hsn_data_list = []
    if not hsn_df.empty:
        for idx, row in hsn_df.iterrows():
            hsn_data_list.append({
                "num": idx + 1,
                "hsn_sc": str(row['HSN']),
                "uqc": str(row['UQC']),
                "qty": float(row['Total Quantity']),
                "rt": float(row['GST Rate']),
                "txval": round(float(row['Total Taxable Value']), 2),
                "iamt": round(float(row['IGST']), 2),
                "camt": round(float(row['CGST']), 2),
                "samt": round(float(row['SGST']), 2),
                "csamt": 0.0
            })

    # Final Payload Structure
    payload = {
        "gstin": gstin,
        "fp": fp,
        "gt": 0, # Gross Turnover - user can edit if needed
        "cur_gt": 0,
        "version": "GST3.0.0",
        "hash": "hash",
        "b2b": [],
        "b2cl": [],
        "b2cs": b2cs_list,
        "cdnr": [],
        "cdnur": [],
        "exp": [],
        "at": [],
        "atadj": [],
        "nil": {
            "inv": []
        },
        "hsn": {
            "data": hsn_data_list
        },
        "doc_issue": {
            "doc_det": []
        }
    }
    
    return json.dumps(payload, indent=2)
