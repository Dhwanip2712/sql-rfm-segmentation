# ==========================================================
# PROJECT 3 — EVENING 1: Set Up the Database, Calculate RFM
# Dataset: Online Retail (UCI) — 4,340 customers, 531K transactions
# Paste each "# %%" section into its own Colab cell.
# ==========================================================

# %% 1. Imports
import pandas as pd
import sqlite3

# %% 2. Load the CSV and create a SQLite database from it
df = pd.read_csv('online_retail.csv')

conn = sqlite3.connect('online_retail.db')
df.to_sql('orders', conn, if_exists='replace', index=False)

print("Database created. Row count check:")
print(pd.read_sql("SELECT COUNT(*) as row_count FROM orders", conn))

# %% 3. Add a Sales column (Quantity x UnitPrice) — this dataset gives us
# quantity and unit price separately, not a pre-calculated line total
cur = conn.cursor()
cur.execute("ALTER TABLE orders ADD COLUMN sales REAL")
conn.commit()
cur.execute("UPDATE orders SET sales = Quantity * UnitPrice")
conn.commit()

print("\nSales column check:")
print(pd.read_sql("SELECT Quantity, UnitPrice, sales FROM orders LIMIT 3", conn))

# %% 4. THE CORE QUERY — Recency, Frequency, Monetary per customer
# Dates are already in YYYY-MM-DD format, so no reformatting needed here
# (unlike the Superstore dataset, which needed a date-fix step).
#
# IMPORTANT DATA QUALITY FIX: CustomerID = 0 is not a real customer — it's
# a placeholder used to fill in originally-missing customer IDs during
# earlier cleaning of this dataset. Left in, it would show up as one
# "customer" with thousands of orders and over $1.7M spent, wrecking every
# calculation downstream. We exclude it here.
rfm_query = """
WITH customer_orders AS (
    SELECT
        CustomerID AS customer_id,
        InvoiceDate AS invoice_date,
        InvoiceNo AS invoice_no,
        sales
    FROM orders
    WHERE CustomerID != 0
),
reference_date AS (
    SELECT date(MAX(invoice_date), '+1 day') AS today FROM customer_orders
)
SELECT
    co.customer_id,
    CAST(julianday((SELECT today FROM reference_date)) - julianday(MAX(co.invoice_date)) AS INTEGER) AS recency_days,
    COUNT(DISTINCT co.invoice_no) AS frequency,
    ROUND(SUM(co.sales), 2) AS monetary
FROM customer_orders co
GROUP BY co.customer_id
ORDER BY monetary DESC
"""

rfm = pd.read_sql(rfm_query, conn)
print("\nTop 10 customers by total spend:")
print(rfm.head(10))

print(f"\nTotal customers: {len(rfm)}")
print(rfm[['recency_days', 'frequency', 'monetary']].describe())

# %% 5. Save for Evening 2
rfm.to_csv('rfm_base.csv', index=False)
conn.close()
print("\nSaved: rfm_base.csv, online_retail.db")
