import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Path where the .exe is located
        return os.path.dirname(sys.executable)
    else:
        # Path where the script is located
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_path()
DB_PATH = os.path.join(BASE_DIR, "ecom_data.db")

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
