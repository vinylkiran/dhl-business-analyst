-- ============================================================
-- DHL Supply Chain | SKU Segmentation — SQL Exploration
-- Author: Vinyl Kiran Anipe | Role: BA/DA
-- Purpose: Data validation and business pattern discovery
--          prior to ABC/XYZ classification analysis
-- ============================================================


-- ── BLOCK 1: DATA QUALITY ────────────────────────────────────

-- 1a. Daily demand — row count and date coverage
SELECT
    COUNT(*)              AS total_rows,
    COUNT(DISTINCT SKU_ID)AS unique_skus,
    MIN(Date)             AS first_date,
    MAX(Date)             AS last_date,
    COUNT(DISTINCT Date)  AS unique_dates
FROM daily_demand;

-- 1b. Null check on critical fields
SELECT
    COUNT(*) - COUNT(SKU_ID)            AS null_sku_ids,
    COUNT(*) - COUNT(Quantity_Demanded) AS null_qty_demanded,
    COUNT(*) - COUNT(Revenue)           AS null_revenue,
    COUNT(*) - COUNT(Warehouse_ID)      AS null_warehouse
FROM daily_demand;

-- 1c. Duplicate SKU-Date-Warehouse combinations (data quality flag)
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT SKU_ID || '|' || Date || '|' || Warehouse_ID) AS unique_combos
FROM daily_demand;

-- 1d. SKU master — active SKU breakdown by category
SELECT
    Category,
    COUNT(*)          AS total_skus,
    SUM(Active_Flag)  AS active_skus,
    ROUND(AVG(Unit_Price), 2)     AS avg_unit_price,
    ROUND(AVG(Lead_Time_Days), 1) AS avg_lead_days,
    COUNT(DISTINCT Storage_Type)  AS storage_types
FROM sku_master
GROUP BY Category
ORDER BY active_skus DESC;


-- ── BLOCK 2: REVENUE DISTRIBUTION (ABC FOUNDATION) ───────────

-- 2a. Revenue by category — Pareto view
SELECT
    Category,
    ROUND(SUM(Revenue), 0) AS total_revenue,
    ROUND(SUM(Revenue) * 100.0 / SUM(SUM(Revenue)) OVER (), 2) AS pct_of_total,
    COUNT(DISTINCT SKU_ID) AS sku_count
FROM daily_demand
GROUP BY Category
ORDER BY total_revenue DESC;

-- 2b. Computed ABC classification based on revenue Pareto
WITH sku_revenue AS (
    SELECT SKU_ID, SUM(Revenue) AS total_rev
    FROM daily_demand
    GROUP BY SKU_ID
),
total AS (
    SELECT SUM(total_rev) AS grand_total FROM sku_revenue
),
ranked AS (
    SELECT
        SKU_ID,
        total_rev,
        SUM(total_rev) OVER (ORDER BY total_rev DESC) AS cumulative_rev,
        (SELECT grand_total FROM total) AS grand_total
    FROM sku_revenue
)
SELECT
    CASE
        WHEN cumulative_rev / grand_total <= 0.80 THEN 'A'
        WHEN cumulative_rev / grand_total <= 0.95 THEN 'B'
        ELSE 'C'
    END AS ABC_Class_Computed,
    COUNT(*)                       AS sku_count,
    ROUND(SUM(total_rev), 0)       AS segment_revenue,
    ROUND(SUM(total_rev) * 100.0 / MAX(grand_total), 2) AS revenue_pct
FROM ranked
GROUP BY 1
ORDER BY 1;


-- ── BLOCK 3: DEMAND VARIABILITY (XYZ FOUNDATION) ─────────────

-- 3a. Coefficient of variation per SKU → XYZ distribution
WITH demand_stats AS (
    SELECT
        SKU_ID,
        AVG(Quantity_Demanded)   AS mean_demand,
        STDDEV(Quantity_Demanded)AS std_demand
    FROM daily_demand
    GROUP BY SKU_ID
    HAVING AVG(Quantity_Demanded) > 0
),
xyz_classified AS (
    SELECT
        SKU_ID,
        ROUND(std_demand / mean_demand, 3) AS CV,
        CASE
            WHEN std_demand / mean_demand < 0.30 THEN 'X'
            WHEN std_demand / mean_demand < 0.70 THEN 'Y'
            ELSE 'Z'
        END AS XYZ_Class
    FROM demand_stats
)
SELECT
    XYZ_Class,
    COUNT(*)        AS sku_count,
    ROUND(AVG(CV), 3) AS avg_cv,
    ROUND(MIN(CV), 3) AS min_cv,
    ROUND(MAX(CV), 3) AS max_cv
FROM xyz_classified
GROUP BY XYZ_Class
ORDER BY XYZ_Class;


-- ── BLOCK 4: STOCKOUT ANALYSIS ────────────────────────────────

-- 4a. Stockout rate by ABC class
SELECT
    ABC_Class,
    COUNT(*)                                          AS demand_days,
    SUM(Stockout_Flag)                                AS stockout_days,
    ROUND(SUM(Stockout_Flag) * 100.0 / COUNT(*), 2)  AS stockout_rate_pct,
    ROUND(SUM(Quantity_Demanded - Quantity_Fulfilled), 0) AS total_unfulfilled_units
FROM daily_demand
GROUP BY ABC_Class
ORDER BY ABC_Class;

-- 4b. Stockout rate by category
SELECT
    Category,
    COUNT(*)                                         AS demand_days,
    SUM(Stockout_Flag)                               AS stockout_days,
    ROUND(SUM(Stockout_Flag) * 100.0 / COUNT(*), 2) AS stockout_rate_pct,
    ROUND(SUM(Revenue), 0)                           AS total_revenue
FROM daily_demand
GROUP BY Category
ORDER BY stockout_rate_pct DESC;


-- ── BLOCK 5: WAREHOUSE PERFORMANCE ───────────────────────────

-- 5a. Revenue, stockouts and fill rate by warehouse
SELECT
    Warehouse_ID,
    COUNT(DISTINCT SKU_ID)                                         AS unique_skus,
    ROUND(SUM(Revenue), 0)                                         AS total_revenue,
    SUM(Stockout_Flag)                                             AS total_stockouts,
    ROUND(SUM(Quantity_Fulfilled) * 100.0 /
          NULLIF(SUM(Quantity_Demanded), 0), 2)                    AS fill_rate_pct
FROM daily_demand
GROUP BY Warehouse_ID
ORDER BY total_revenue DESC;


-- ── BLOCK 6: TOP SKUS ─────────────────────────────────────────

-- 6a. Top 15 SKUs by total revenue with stockout exposure
SELECT
    d.SKU_ID,
    s.Category,
    s.ABC_Class,
    ROUND(SUM(d.Revenue), 0)            AS total_revenue,
    ROUND(SUM(d.Quantity_Fulfilled), 0) AS total_units_shipped,
    SUM(d.Stockout_Flag)                AS stockout_days,
    ROUND(SUM(d.Stockout_Flag) * 100.0
          / COUNT(*), 2)                AS stockout_rate_pct
FROM daily_demand d
JOIN sku_master s ON d.SKU_ID = s.SKU_ID
GROUP BY d.SKU_ID, s.Category, s.ABC_Class
ORDER BY total_revenue DESC
LIMIT 15;
