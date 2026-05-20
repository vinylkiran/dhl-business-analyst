"""
DHL Supply Chain | SKU Segmentation — SQL Exploration Runner
BA/DA Portfolio | Project 1 | Step 2 of 4
Author: Vinyl Kiran Anipe

Executes exploratory SQL queries against DHL synthetic datasets
using DuckDB. No database setup required — queries run directly
against CSV files.
"""

import duckdb
import pandas as pd
import os

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:,.2f}".format)

DATA = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
con  = duckdb.connect()

# Register CSV files as named views so SQL stays clean
con.execute(f"CREATE VIEW sku_master   AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")
con.execute(f"CREATE VIEW daily_demand AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def run(label, sql):
    print(f"\n── {label}")
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    return df

# ── BLOCK 1: DATA QUALITY ─────────────────────────────────────
section("BLOCK 1 — DATA QUALITY CHECKS")

run("1a. Daily Demand — Row Count & Date Range", """
    SELECT COUNT(*) AS total_rows, COUNT(DISTINCT SKU_ID) AS unique_skus,
           MIN(Date) AS first_date, MAX(Date) AS last_date,
           COUNT(DISTINCT Date) AS unique_dates
    FROM daily_demand
""")

run("1b. Null Check — Critical Fields", """
    SELECT
        COUNT(*) - COUNT(SKU_ID)            AS null_sku_ids,
        COUNT(*) - COUNT(Quantity_Demanded) AS null_qty_demanded,
        COUNT(*) - COUNT(Revenue)           AS null_revenue,
        COUNT(*) - COUNT(Warehouse_ID)      AS null_warehouse
    FROM daily_demand
""")

run("1c. Duplicate Check — SKU + Date + Warehouse", """
    SELECT COUNT(*) AS total_rows,
           COUNT(DISTINCT SKU_ID || '|' || Date || '|' || Warehouse_ID) AS unique_combos
    FROM daily_demand
""")

run("1d. SKU Master — Active SKUs by Category", """
    SELECT Category, COUNT(*) AS total_skus, SUM(Active_Flag) AS active_skus,
           ROUND(AVG(Unit_Price), 2) AS avg_unit_price,
           ROUND(AVG(Lead_Time_Days), 1) AS avg_lead_days
    FROM sku_master
    GROUP BY Category
    ORDER BY active_skus DESC
""")

# ── BLOCK 2: REVENUE (ABC FOUNDATION) ────────────────────────
section("BLOCK 2 — REVENUE DISTRIBUTION (ABC FOUNDATION)")

run("2a. Revenue by Category — Pareto View", """
    SELECT Category,
           ROUND(SUM(Revenue), 0) AS total_revenue,
           ROUND(SUM(Revenue)*100.0/SUM(SUM(Revenue)) OVER(), 2) AS pct_of_total,
           COUNT(DISTINCT SKU_ID) AS sku_count
    FROM daily_demand
    GROUP BY Category
    ORDER BY total_revenue DESC
""")

run("2b. Computed ABC Classes — Pareto Segmentation", """
    WITH sku_rev AS (
        SELECT SKU_ID, SUM(Revenue) AS total_rev FROM daily_demand GROUP BY SKU_ID
    ),
    grand AS (SELECT SUM(total_rev) AS gt FROM sku_rev),
    ranked AS (
        SELECT SKU_ID, total_rev,
               SUM(total_rev) OVER (ORDER BY total_rev DESC) AS cum_rev,
               (SELECT gt FROM grand) AS gt
        FROM sku_rev
    )
    SELECT
        CASE WHEN cum_rev/gt <= 0.80 THEN 'A'
             WHEN cum_rev/gt <= 0.95 THEN 'B'
             ELSE 'C' END AS ABC_Class,
        COUNT(*) AS sku_count,
        ROUND(SUM(total_rev), 0) AS segment_revenue,
        ROUND(SUM(total_rev)*100.0/MAX(gt), 2) AS revenue_pct
    FROM ranked GROUP BY 1 ORDER BY 1
""")

# ── BLOCK 3: VARIABILITY (XYZ FOUNDATION) ────────────────────
section("BLOCK 3 — DEMAND VARIABILITY (XYZ FOUNDATION)")

run("3a. Coefficient of Variation → XYZ Distribution", """
    WITH stats AS (
        SELECT SKU_ID,
               AVG(Quantity_Demanded) AS mu,
               STDDEV(Quantity_Demanded) AS sigma
        FROM daily_demand GROUP BY SKU_ID HAVING AVG(Quantity_Demanded) > 0
    )
    SELECT
        CASE WHEN sigma/mu < 0.30 THEN 'X'
             WHEN sigma/mu < 0.70 THEN 'Y'
             ELSE 'Z' END AS XYZ_Class,
        COUNT(*) AS sku_count,
        ROUND(AVG(sigma/mu), 3) AS avg_cv,
        ROUND(MIN(sigma/mu), 3) AS min_cv,
        ROUND(MAX(sigma/mu), 3) AS max_cv
    FROM stats GROUP BY 1 ORDER BY 1
""")

# ── BLOCK 4: STOCKOUT ANALYSIS ────────────────────────────────
section("BLOCK 4 — STOCKOUT ANALYSIS")

run("4a. Stockout Rate by ABC Class", """
    SELECT ABC_Class,
           COUNT(*) AS demand_days,
           SUM(Stockout_Flag) AS stockout_days,
           ROUND(SUM(Stockout_Flag)*100.0/COUNT(*), 2) AS stockout_rate_pct,
           ROUND(SUM(Quantity_Demanded - Quantity_Fulfilled), 0) AS unfulfilled_units
    FROM daily_demand GROUP BY ABC_Class ORDER BY ABC_Class
""")

run("4b. Stockout Rate by Category", """
    SELECT Category,
           SUM(Stockout_Flag) AS stockout_days,
           ROUND(SUM(Stockout_Flag)*100.0/COUNT(*), 2) AS stockout_rate_pct,
           ROUND(SUM(Revenue), 0) AS total_revenue
    FROM daily_demand GROUP BY Category ORDER BY stockout_rate_pct DESC
""")

# ── BLOCK 5: WAREHOUSE PERFORMANCE ───────────────────────────
section("BLOCK 5 — WAREHOUSE PERFORMANCE")

run("5a. Revenue, Stockouts & Fill Rate by Warehouse", """
    SELECT Warehouse_ID,
           COUNT(DISTINCT SKU_ID) AS unique_skus,
           ROUND(SUM(Revenue), 0) AS total_revenue,
           SUM(Stockout_Flag) AS total_stockouts,
           ROUND(SUM(Quantity_Fulfilled)*100.0/NULLIF(SUM(Quantity_Demanded),0), 2) AS fill_rate_pct
    FROM daily_demand GROUP BY Warehouse_ID ORDER BY total_revenue DESC
""")

# ── BLOCK 6: TOP SKUs ─────────────────────────────────────────
section("BLOCK 6 — TOP SKUs BY REVENUE")

run("6a. Top 15 SKUs with Stockout Exposure", """
    SELECT d.SKU_ID, s.Category, s.ABC_Class,
           ROUND(SUM(d.Revenue), 0) AS total_revenue,
           ROUND(SUM(d.Quantity_Fulfilled), 0) AS units_shipped,
           SUM(d.Stockout_Flag) AS stockout_days,
           ROUND(SUM(d.Stockout_Flag)*100.0/COUNT(*), 2) AS stockout_rate_pct
    FROM daily_demand d JOIN sku_master s ON d.SKU_ID = s.SKU_ID
    GROUP BY d.SKU_ID, s.Category, s.ABC_Class
    ORDER BY total_revenue DESC LIMIT 15
""")

print(f"\n{'='*65}")
print("  SQL EXPLORATION COMPLETE")
print("  Review findings above, then proceed to:")
print("  Step 3 — ABC/XYZ Python Analysis (analysis.ipynb)")
print(f"{'='*65}\n")
