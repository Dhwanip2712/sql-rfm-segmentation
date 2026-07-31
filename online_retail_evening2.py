# ==========================================================
# PROJECT 3 — EVENING 2: Score and Segment Customers
# Paste each "# %%" section into its own Colab cell.
# Picks up from rfm_base.csv / online_retail.db (Evening 1)
# ==========================================================

# %% 1. Imports
import pandas as pd
import sqlite3

# %% 2. Reconnect to the database from Evening 1
conn = sqlite3.connect('online_retail.db')

# %% 3. THE SCORING QUERY — window functions doing the real work
# NTILE(5) splits all customers into 5 equal-sized groups (quintiles),
# ordered by whichever column we choose. This is a WINDOW FUNCTION —
# it looks across all rows at once to figure out relative ranking,
# something a normal WHERE clause or aggregate can't do.
scoring_query = """
WITH rfm AS (
    SELECT
        CustomerID AS customer_id,
        CAST(julianday((SELECT date(MAX(InvoiceDate), '+1 day') FROM orders)) - julianday(MAX(InvoiceDate)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT InvoiceNo) AS frequency,
        ROUND(SUM(Quantity * UnitPrice), 2) AS monetary
    FROM orders
    WHERE CustomerID != 0
    GROUP BY CustomerID
),
scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        -- Recency: LOWER days = BETTER, so we order ASCENDING and then
        -- flip the bucket number (6 - bucket) so a score of 5 = most recent
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC)) AS recency_score,
        -- Frequency and Monetary: HIGHER = BETTER, so the bucket number
        -- IS the score directly — no flipping needed
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS monetary_score
    FROM rfm
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,
    -- A single combined score, useful as a quick overall ranking
    (recency_score + frequency_score + monetary_score) AS rfm_total_score,
    -- THE ACTUAL BUSINESS LABEL — plain-English segments a marketing
    -- team could act on directly, built from simple, defensible rules
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal customers'
        WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New customers'
        WHEN recency_score <= 2 AND frequency_score >= 4 THEN 'At risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost'
        ELSE 'Needs attention'
    END AS segment
FROM scored
ORDER BY rfm_total_score DESC
"""

segments = pd.read_sql(scoring_query, conn)
print(segments.head(10))

# %% 4. Sanity check — segment sizes
print("\nSegment sizes:")
print(segments['segment'].value_counts())

# %% 5. Sanity check — do the segments make business sense?
# Champions should have low recency_days, high frequency, high monetary.
# Lost should have the opposite. Confirm with averages per segment.
print("\nAverage R/F/M by segment (sense-check):")
print(segments.groupby('segment')[['recency_days', 'frequency', 'monetary']].mean().round(1)
      .sort_values('monetary', ascending=False))

# %% 6. Save for Evening 3
segments.to_csv('rfm_segments.csv', index=False)
conn.close()
print("\nSaved: rfm_segments.csv")