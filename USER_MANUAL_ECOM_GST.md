# E-Commerce GST & Inventory Tool - Comprehensive User Manual

Welcome to the **E-Commerce GST & Inventory Tool**. This application is engineered to automate your multi-channel sales (Amazon, Flipkart, Meesho) and strictly manage your GSTR-1 filings.

This manual explains every single page, tab, and button in the application to give you complete mastery over the tool.

---

## 1. 📦 Inventory Management
This is the foundational page of the app. Before the tool can map your sales and purchases to correct tax rates, the items must exist here.

- **Tab 1: View Stock**
  - Displays your `Current Inventory` in a dynamic table.
  - You can view columns like `SKU`, `Name`, `HSN Code`, `Unit`, `Quantity`, and `GST Rate`.
  - The `Quantity` column updates automatically when you import sales (decreases) or purchases (increases).

- **Tab 2: Add New SKU**
  - Use this form to register a new product.
  - **SKU ID:** *CRITICAL!* This must be precisely the exact string you use on Amazon/Flipkart/Meesho. If this doesn't match, the app cannot map your sales to an HSN code.
  - **Product Name:** A friendly name for your reference.
  - **HSN Code:** The Government-mandated standard code for your product type.
  - **Unit:** Select standard UQCs (e.g., `Pcs`, `Kg`, `Box`, `Set`).
  - **Initial Quantity:** The starting stock level.
  - **Cost Price & Selling Price (MRP):** For your own profitability tracking.
  - **GST Rate:** Select the tax slab (e.g., `0%`, `5%`, `12%`, `18%`, `28%`).

---

## 2. 📥 Sales Importer
This page allows you to automatically ingest thousands of B2C sales orders in seconds.

- **Select Platform Dropdown:** Choose the origin of the file (`Amazon`, `Flipkart`, or `Meesho`). The app uses entirely different parsers based on your selection.
- **Choose CSV Report:** Upload your file.
  - For Amazon: Use the MTR (Merchant Tax Report).
  - For Flipkart: Use the Seller Central Sales Report.
  - For Meesho: Use the Order Report.
- **Preview Data:** Once uploaded, the app extracts the data and shows you a table preview. It intelligently extracts `Order ID`, `SKU`, `Taxable Value`, `Customer State`, `IGST/CGST/SGST`, and even attempts to pull `HSN` if the platform provides it.
- **Confirm and Import (Button):** Clicking this commits the data to your database and auto-deducts the quantities from your `Inventory Management` stock.

---

## 3. 🛒 Purchase Entry
This page tracks your inbound B2B supplies to increase your stock and map your input taxes.

- **Tab 1: Manual Entry**
  - Use this if you have a physical paper bill.
  - Enter the **Invoice Number**, **Supplier Name**, **Supplier GSTIN**, and **Date**.
  - **Total Taxable & Total GST:** Add the grand totals from the bottom of the bill.
  - **Select Item SKU:** Pick the product you bought from the dropdown (pulls from Inventory Management).
  - Fill in the quantity and unit cost. The system automatically splits the GST into IGST or CGST/SGST based on whether the supplier's GSTIN starts with "29" (Karnataka).
  - **Record Purchase (Button):** Saves the bill and increases your stock.

- **Tab 2: Bulk Excel Upload**
  - **Choose a file:** Upload a CSV or Excel (`.xlsx`) sheet from your supplier.
  - The file should ideally contain columns like `Invoice No`, `Supplier Name`, `SKU`, `Quantity`, `Unit Price`, `GST Rate`, `HSN`, and `UQC`.
  - **Process Purchase File (Button):** The app reads all rows, groups them into invoices, saves them, and auto-increases your stock.

---

## 4. 🔄 Return Reconciliation
Managing customer returns is crucial so you don't pay GST on canceled orders and your stock remains accurate.

- **Tab 1: Manual Recon**
  - Use this if a customer cancels an order or you physically receive a returned box.
  - **Order ID:** Enter the exact platform Order ID.
  - **SKU (Optional):** If the order had multiple items but only one was returned, specify it.
  - **Reconcile and Adjust Stock (Button):** This changes the order's status to `Returned` and adds the product quantity back to your inventory stock.

- **Tab 2: Recent Returns**
  - A view-only table displaying all orders that the app automatically marked as `Returned` during your Bulk Sales Imports (e.g., if a Meesho row said "Returned" or an Amazon row said "Refund").

---

## 5. 📄 GST & Sales Reports
This is the ultimate output of the tool. It aggregates everything for filing.

- **Select Month for GST Return (Dropdown):** *Crucial step.* Always select the target month (e.g., `2026-04`) before looking at any data on this page. All tabs update dynamically based on this selection.

- **Tab 1: GSTR-1 B2CS**
  - Shows your Business-to-Consumer (Small) sales aggregated by **Place of Supply (State)** and **Tax Rate**.
  - Required for your state-wise B2C summary on the GST portal.
  - Contains a CSV download button.

- **Tab 2: HSN Summary**
  - Aggregates all sales grouped strictly by **HSN**, **UQC**, and **GST Rate** (As mandated by GST rules).
  - **🛠️ Manual HSN Override (Expander):** If your data is wrong or missing, open this. Entering a row here and clicking `Save HSN Override` will forcefully append this correct data for the month and ignore the app's auto-calculations for that specific override.

- **Tab 3: Platform Analytics**
  - A visual bar chart and data table comparing your total sales across Amazon, Flipkart, and Meesho for business insights.

- **Tab 4: GSTR-1 JSON Export**
  - The final destination. 
  - **Your GSTIN:** Enter your business GST Number.
  - **⚠️ Missing HSN Warning:** If the app detects sales that couldn't be matched to an HSN code (because the SKU wasn't in inventory and the platform sheet didn't have it), a yellow warning appears. **You must fix these in Inventory or use Manual Overrides, otherwise the GST portal will reject the JSON.**
  - **Generate JSON (Button):** Packages the `B2CS`, `HSN`, and other required arrays into the precise schema required by the government.
  - **Download GSTR-1 JSON:** Click to save the `.json` file, which you can directly upload into the official **GST Offline Tool** to file your returns in one click!
