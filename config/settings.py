import os

DB_PATH = os.path.abspath(os.path.join(os.getcwd(), "ecom_data.db"))

SHOP_NAME = "E-Commerce Retailer"
GSTIN = "29XXXXXXXXXXXXX"
STATE_CODE = "29" # Karnataka

PLATFORMS = ["Amazon", "Flipkart", "Meesho", "Shukaan Mall"]

GST_RATES = {
    "0%": 0.00,
    "5%": 0.05,
    "12%": 0.12,
    "18%": 0.18,
    "28%": 0.28,
}
