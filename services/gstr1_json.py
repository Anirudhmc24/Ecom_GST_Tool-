import json
from services.report_generator import get_gstr1_b2cs, get_final_hsn_data

STATE_CODES_MAP = {
    "jammu and kashmir": "01",
    "jammu & kashmir": "01",
    "himachal pradesh": "02",
    "punjab": "03",
    "chandigarh": "04",
    "uttarakhand": "05",
    "haryana": "06",
    "delhi": "07",
    "rajasthan": "08",
    "uttar pradesh": "09",
    "bihar": "10",
    "sikkim": "11",
    "arunachal pradesh": "12",
    "nagaland": "13",
    "manipur": "14",
    "mizoram": "15",
    "tripura": "16",
    "meghalaya": "17",
    "assam": "18",
    "west bengal": "19",
    "jharkhand": "20",
    "odisha": "21",
    "orissa": "21",
    "chhattisgarh": "22",
    "madhya pradesh": "23",
    "gujarat": "24",
    "dadra and nagar haveli": "26",
    "dadra & nagar haveli": "26",
    "daman and diu": "26",
    "daman & diu": "26",
    "maharashtra": "27",
    "karnataka": "29",
    "goa": "30",
    "lakshadweep": "31",
    "kerala": "32",
    "tamil nadu": "33",
    "puducherry": "34",
    "pondicherry": "34",
    "andaman and nicobar islands": "35",
    "andaman & nicobar islands": "35",
    "telangana": "36",
    "andhra pradesh": "37",
    "ladakh": "38",
    "leh ladakh": "38"
}

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
            state_str = str(row['Place of Supply']).strip()
            if state_str and len(state_str) >= 2 and state_str[:2].isdigit():
                pos = state_str[:2]
            elif '-' in state_str and state_str.split('-')[0].strip().isdigit() and len(state_str.split('-')[0].strip()) == 2:
                pos = state_str.split('-')[0].strip()
            else:
                state_clean = state_str.lower().replace('&', 'and').strip()
                if '-' in state_clean:
                    parts = [p.strip() for p in state_clean.split('-')]
                    pos = STATE_CODES_MAP.get(parts[1], STATE_CODES_MAP.get(parts[0], '29'))
                else:
                    pos = STATE_CODES_MAP.get(state_clean, '29')
                
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
