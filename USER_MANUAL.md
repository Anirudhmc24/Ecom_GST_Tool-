# E-Commerce GST & Inventory Tool - User Manual

## Introduction
This tool is designed for Indian e-commerce sellers to manage multi-channel inventory (Amazon, Flipkart, Meesho) and simplify GSTR-1 filing.

## Getting Started
1. **Initialize Inventory**: Before importing sales, add your products in the **Inventory Management** section. Ensure the SKU matches exactly with the platform's SKU.
2. **Importing Sales**: 
   - Download your B2C sales reports (MTR for Amazon, Sales Report for Flipkart/Meesho).
   - Go to **Sales Importer**, select the platform, and upload the CSV.
   - Confirm the import to update sales records and auto-deduct stock.
3. **Recording Purchases**: Use **Purchase Entry** to record B2B purchases from suppliers like Shukaan Mall. This will automatically increase your inventory stock levels.
4. **Handling Returns**: 
   - Use **Return Reconciliation** to mark orders as returned. This adds the items back to your stock and adjusts GST reports.
5. **Filing GST**:
   - Go to the **Reports** section.
   - Copy/Download the **B2CS** summary for State-wise filing.
   - Use the **HSN Summary** for the HSN-wise summary table in GSTR-1.

## Platform Specifics
- **Amazon**: Supports both comma and tab-separated reports (MTR).
- **Flipkart**: Use the "Sales Report" from the Seller Central.
- **Meesho**: Use the standard "Order Report".

## Troubleshooting
- **Missing HSN**: If HSN codes are missing in reports, check if the SKU is correctly registered in the Inventory section.
- **CSV Errors**: Ensure the file is a valid CSV and contains headers like 'Order ID', 'SKU', and 'Total Amount'.
