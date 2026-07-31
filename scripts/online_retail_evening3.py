# ==========================================================
# PROJECT 3 — EVENING 3: Revenue Concentration & Segment Value
# Paste each "# %%" section into its own Colab cell.
# Picks up from rfm_segments.csv / online_retail.db (Evening 2)
# ==========================================================

# %% 1. Imports
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# %% 2. Reconnect and reload the segmented data
conn = sqlite3.connect('online_retail.db')
segments = pd.read_csv('rfm_segments.csv')

# Also load it into SQLite so we can query it directly alongside `orders`
segments.to_sql('rfm_segments', conn, if_exists='replace', index=False)

# ==========================================================
# PART A: Revenue Concentration (the Pareto / 80-20 check)
# Business question: what % of total revenue comes from the
# top 20% of customers, by spend?
# ==========================================================

# %% 3. THE PARETO QUERY
# CUME_DIST() is another window function — it tells you, for each row,
# what CUMULATIVE percentage of all rows fall at or below this one,
# when sorted. Here we use it to find "the top 20% of customers by spend."
pareto_query = """
WITH ranked_customers AS (
    SELECT
        customer_id,
        monetary,
        CUME_DIST() OVER (ORDER BY monetary DESC) AS cumulative_percentile
    FROM rfm_segments
)
SELECT
    SUM(CASE WHEN cumulative_percentile <= 0.20 THEN monetary ELSE 0 END) AS revenue_from_top_20pct,
    SUM(monetary) AS total_revenue,
    ROUND(
        100.0 * SUM(CASE WHEN cumulative_percentile <= 0.20 THEN monetary ELSE 0 END) / SUM(monetary),
        1
    ) AS pct_revenue_from_top_20pct_customers
FROM ranked_customers
"""

pareto_result = pd.read_sql(pareto_query, conn)
print("Revenue concentration check:")
print(pareto_result)

# ==========================================================
# PART B: Segment Revenue Share vs Headcount Share
# Business question: does a small, loyal segment (Champions)
# contribute a disproportionate share of total revenue?
# ==========================================================

# %% 4. THE SEGMENT CONTRIBUTION QUERY
segment_query = """
SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM rfm_segments), 1) AS pct_of_customers,
    ROUND(SUM(monetary), 2) AS segment_revenue,
    ROUND(100.0 * SUM(monetary) / (SELECT SUM(monetary) FROM rfm_segments), 1) AS pct_of_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY pct_of_revenue DESC
"""

segment_contribution = pd.read_sql(segment_query, conn)
print("\nSegment contribution — headcount share vs revenue share:")
print(segment_contribution)

# %% 5. Chart 1 — Segment revenue share vs headcount share
fig, ax = plt.subplots(figsize=(8, 5))
x = range(len(segment_contribution))
width = 0.35
ax.bar([i - width/2 for i in x], segment_contribution['pct_of_customers'], width, label='% of customers', color='#3498db')
ax.bar([i + width/2 for i in x], segment_contribution['pct_of_revenue'], width, label='% of revenue', color='#2ecc71')
ax.set_xticks(list(x))
ax.set_xticklabels(segment_contribution['segment'], rotation=20, ha='right')
ax.set_ylabel('Percentage')
ax.set_title('Segment Size vs Revenue Contribution')
ax.legend()
plt.tight_layout()
plt.savefig('p3_chart1_segment_contribution.png', dpi=150)
plt.show()

# %% 6. Chart 2 — Revenue concentration curve (cumulative %)
concentration_query = """
SELECT
    customer_id,
    monetary,
    CUME_DIST() OVER (ORDER BY monetary DESC) AS customer_percentile,
    SUM(monetary) OVER (ORDER BY monetary DESC) * 1.0 / SUM(monetary) OVER () AS cumulative_revenue_pct
FROM rfm_segments
ORDER BY monetary DESC
"""
concentration = pd.read_sql(concentration_query, conn)

plt.figure(figsize=(7, 5))
plt.plot(concentration['customer_percentile'] * 100, concentration['cumulative_revenue_pct'] * 100,
         color='#8e44ad', linewidth=2)
plt.plot([0, 100], [0, 100], color='gray', linestyle='--', label='Perfectly even (no concentration)')
plt.xlabel('Top % of Customers (by spend)')
plt.ylabel('Cumulative % of Total Revenue')
plt.title('Revenue Concentration Curve')
plt.legend()
plt.tight_layout()
plt.savefig('p3_chart2_concentration_curve.png', dpi=150)
plt.show()

conn.close()
print("\nCharts saved.")
