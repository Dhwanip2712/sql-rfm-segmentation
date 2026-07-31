# Customer RFM segmentation (SQL-only)

Which customers are genuinely valuable to a business, and which ones are quietly slipping away? This is a classic technique — RFM (Recency, Frequency, Monetary) analysis — solved entirely in SQL, no Python modeling required.

It's a good example of picking the right tool for a problem rather than the most advanced one available: RFM is naturally SQL-shaped (aggregations, window functions, no prediction needed), so that's what this project uses.

## The idea

1. For every customer, calculate three things using SQL: how recently they last bought (Recency), how often they buy (Frequency), and how much they've spent in total (Monetary)
2. Rank customers against each other — not against arbitrary fixed numbers — using SQL window functions (`NTILE`)
3. Combine those ranks into plain-language segments: Champions, Loyal customers, At risk, Lost, and more
4. Check what this actually means in revenue terms, using another window function (`CUME_DIST`)

## What I found

- The **top 20% of customers generate roughly 68-70% of total revenue** — a strong version of the classic 80/20 (Pareto) pattern
- **Champions** make up about **22%** of the customer base but drive **over half** of total revenue
- **Lost customers** are the single largest group by headcount (roughly 22-25%) but contribute only **4-5%** of revenue

## A data quality catch along the way

The raw dataset had a placeholder `CustomerID = 0`, used to fill in originally-missing customer IDs during prior cleaning. Left in, it would have looked like a single "customer" with over 2,000 orders and $1.7M spent, wrecking every calculation. Excluded before any analysis ran — see `scripts/1_rfm_setup.py`.

## Tools

SQLite (via Python's built-in `sqlite3`) for all analysis — CTEs, window functions (`NTILE`, `CUME_DIST`), aggregations. Matplotlib used only for the final charts, not the analysis itself.

## Data

[Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail) (UCI Machine Learning Repository) — a year of real transactions (Dec 2010–Dec 2011) from a UK-based online retailer. This is the dataset used in the original academic paper that established RFM segmentation as a modern data mining technique (Chen, Sain & Guo, 2012).

## Repo structure

```
data/        the raw dataset
scripts/     SQL/Python analysis, in order
outputs/     chart images
```

## Scripts

- `1_rfm_setup.py` — load data into SQLite, calculate raw Recency/Frequency/Monetary per customer
- `2_scoring_segmentation.py` — window-function-based scoring and segment labeling
- `3_revenue_analysis.py` — Pareto/revenue concentration check, segment contribution charts
