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

def generate_gstr1_json(month_year, gstin, fp, ecom_gstin=None):
    """
    Generates the exact GSTR-1 JSON payload structure required by the GST portal.
    month_year: YYYY-MM
    gstin: Supplier GSTIN
    fp: Financial Period string (e.g., '042026' for April 2026)
    ecom_gstin: E-Commerce Operator GSTIN (Amazon/Flipkart etc.) - required for etin field
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
            txval = round(float(row['Total Taxable Value']), 2)
            
            # GSTR-1 B2CS table does not allow negative/zero values.
            # Net negative states/rates must be handled separately.
            if txval > 0:
                sply_ty = "INTRA" if pos == gstin[:2] else "INTER"
                if sply_ty == "INTRA":
                    iamt = 0.0
                    camt = round(txval * (rate / 2.0) / 100.0, 2)
                    samt = camt
                else:
                    iamt = round(txval * rate / 100.0, 2)
                    camt = 0.0
                    samt = 0.0

                entry = {
                    "sply_ty": sply_ty,
                    "rt": rate,
                    # 'E' = E-Commerce (sales through ECO like Amazon/Flipkart)
                    # 'OE' = Other (direct B2C sales NOT through e-commerce operator)
                    "typ": "E",
                    "pos": pos,
                    "txval": txval,
                    "iamt": iamt,
                    "camt": camt,
                    "samt": samt,
                    "csamt": 0.0
                }
                # etin is mandatory for typ='E' (e-commerce) entries
                if ecom_gstin:
                    entry["etin"] = ecom_gstin
                b2cs_list.append(entry)

    # HSN Data
    hsn_df = get_final_hsn_data(month_year)
    hsn_data_list = []
    if not hsn_df.empty:
        for _, row in hsn_df.iterrows():
            txval = round(float(row['Total Taxable Value']), 2)
            qty = float(row['Total Quantity'])
            
            # GSTR-1 HSN summary table does not allow negative/zero values.
            if txval > 0 and qty > 0:
                rate = float(row['GST Rate'])
                # If rate is represented as a fraction (e.g. 0.18 instead of 18.0), convert it
                if 0.0 < rate < 1.0:
                    rate = rate * 100.0
                    
                iamt_db = round(float(row['IGST']), 2) if 'IGST' in row and row['IGST'] else 0.0
                camt_db = round(float(row['CGST']), 2) if 'CGST' in row and row['CGST'] else 0.0
                samt_db = round(float(row['SGST']), 2) if 'SGST' in row and row['SGST'] else 0.0
                
                total_db_tax = iamt_db + camt_db + samt_db
                if total_db_tax > 0:
                    igst_share = iamt_db / total_db_tax
                    txval_inter = txval * igst_share
                    txval_intra = txval * (1.0 - igst_share)
                    iamt = round(txval_inter * rate / 100.0, 2)
                    camt = round(txval_intra * (rate / 2.0) / 100.0, 2)
                    samt = camt
                else:
                    # Fallback to all IGST if no tax in DB
                    iamt = round(txval * rate / 100.0, 2)
                    camt = 0.0
                    samt = 0.0
                
                hsn_data_list.append({
                    "num": len(hsn_data_list) + 1,  # Dynamically generate sequence number to avoid gaps
                    "hsn_sc": str(row['HSN']),
                    "uqc": str(row['UQC']),
                    "qty": qty,
                    "rt": rate,
                    "txval": txval,
                    "iamt": iamt,
                    "camt": camt,
                    "samt": samt,
                    "csamt": 0.0
                })

    # Final Payload Structure — strictly matches GST portal schema.
    # IMPORTANT: ALL section keys must always be present even if empty.
    # The portal does a top-level key existence check before field-level validation,
    # so any missing section key (b2b, cdnr, nil, doc_issue, etc.) causes
    # "File could not be uploaded!" regardless of the data inside.
    payload = {
        "gstin": gstin,
        "fp": fp,
        "gt": 0.0,       # Gross Turnover (annual) — update if filing annually
        "cur_gt": 0.0,   # Current period gross turnover
        "version": "GST3.2.4",
        "hash": "hash",

        # Always-present sections (empty list = no records for this table)
        "b2b":   [],   # Table 4  — B2B taxable supplies
        "b2cl":  [],   # Table 5  — B2CL (inter-state, invoice > 2.5L)
        "b2cs":  b2cs_list,   # Table 7  — B2CS (small/e-comm, always include)
        "cdnr":  [],   # Table 9B — Credit/Debit notes to registered persons
        "cdnur": [],   # Table 9B — Credit/Debit notes to unregistered persons
        "exp":   [],   # Table 6  — Export invoices
        "at":    [],   # Table 11A — Tax liability on advances received
        "atadj": [],   # Table 11B — Advance amount adjusted
        "nil": {       # Table 8  — Nil-rated / Exempted / Non-GST supplies
            "inv": []
        },
        "hsn": {       # Table 12 — HSN-wise summary (mandatory even if empty)
            "data": hsn_data_list
        },
        "doc_issue": { # Table 13 — Document issue summary (mandatory)
            "doc_det": []
        }
    }

    return json.dumps(payload, indent=2)
