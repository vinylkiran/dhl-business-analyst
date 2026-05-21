# Demand Forecasting — Business Narrative
**Author:** Vinyl Kiran Anipe  
**Role:** Business Analyst / Data Analyst  
**Date:** June 2024  
**Status:** Analysis complete  
**Project:** DHL Supply Chain — Demand Forecasting & Planning Optimisation

---

## Executive Summary

DHL's three-warehouse network currently relies on manual, backward-looking demand planning.
Inventory planners pull daily demand reports from the WMS, paste data into Excel, manually
compute rolling averages, and generate replenishment recommendations — a process consuming
2–3 days per planner per week. The absence of a systematic forecasting baseline means high-value
SKUs are replenished reactively, contributing to a 3% network-wide stockout rate that carries
an estimated **$356M in lost revenue over 24 months** for A-class SKUs alone.

This analysis establishes a quantitative demand forecasting baseline using 24 months of daily
demand data across 1,664 active SKUs and three warehouses. Key outputs include: a 14-day moving
average accuracy benchmark (MAPE) by ABC class, a seasonality index identifying peak demand
months, a demand growth rate analysis (2022 vs 2023), and a business impact model translating
stockout frequency into estimated lost revenue.

Expected outcomes of adopting this forecasting framework: **≥25% reduction in forecasting
cycle time**, **MAPE improvement from the 14-day MA baseline to below 20% on A-class SKUs**,
and measurable reduction in A-class stockout events within 90 days of implementation.

---

## Business Problem

### Current State

Demand planning at DHL's warehouse network is a manual, time-intensive process:

1. Planners export daily demand data from the WMS each morning.
2. Data is copied into individual SKU-level Excel workbooks.
3. Rolling averages are computed manually or via basic Excel formulas — no seasonality
   adjustment, no ABC-class differentiation.
4. Replenishment decisions are made based on these averages with no documented accuracy tracking.
5. There is no feedback loop: planners do not know whether last week's forecast was accurate.

### Impact of Current State

- **Planning cycle time:** 2–3 days per planner per week is consumed by data extraction and
  manual formatting — time that should be spent on decision-making.
- **Reactive replenishment:** Without a forward-looking forecast, reorder decisions are triggered
  by current stock levels rather than anticipated demand. This is particularly damaging for
  high-variability A/Y-class SKUs.
- **No accuracy baseline:** Without tracking MAPE or similar metrics, there is no objective way
  to evaluate whether forecasting has improved after any process change.
- **Seasonal blind spots:** No seasonality adjustment means demand spikes in peak months are
  treated as anomalies rather than predictable patterns, resulting in under-ordering.

### Business Question

*Can we establish a statistically grounded demand forecasting baseline — by ABC class, category,
and warehouse — that reduces planner cycle time, improves replenishment timing, and quantifies
the financial cost of forecast error?*

---

## Stakeholders

| Stakeholder | Role | Primary Interest |
|---|---|---|
| Warehouse Operations Manager | Decision owner | Stockout reduction, planner efficiency |
| Inventory Planner (×3 warehouses) | Primary user | Simpler daily process, actionable reorder signals |
| Data Engineering Team | Build partner | Automated pipeline requirements, data quality SLAs |
| Commercial / Account Team | Client-facing | OTIF performance, proactive SLA management |
| Finance | Approver | Working capital impact, cost of stock-outs vs. overstock |

---

## Success Metrics

| Metric | Current State | Target | Measurement |
|---|---|---|---|
| A-Class Forecast MAPE (14-Day MA baseline) | Measured in this analysis | < 20% within 6 months | Weekly MAPE tracking per SKU |
| Forecasting Cycle Time | 2–3 days/planner/week | ≤ 0.5 days/planner/week | Planner time log |
| Planner Adoption Rate | 0% (no current system) | ≥ 80% within 90 days | Dashboard login rate |
| A-Class Stockout Rate | ~3% (network baseline) | Reduce by ≥ 30% | WMS stockout flag |
| Replenishment Lead | Reactive (lagged) | Proactive (forecast-driven) | Days between reorder trigger and stockout |

---

## Data Sources

| Table | Source | Key Fields Used | Period |
|---|---|---|---|
| `daily_demand.csv` | DHL WMS — daily fulfilment records | SKU_ID, Date, Quantity_Demanded, Quantity_Fulfilled, Revenue, Stockout_Flag, Warehouse_ID | Jan 2022 – Dec 2023 |
| `sku_master.csv` | DHL WMS — SKU master extract | SKU_ID, Category, ABC_Class, Unit_Price, Lead_Time_Days | Static |

**Data scope:** All three warehouses (DHL-WH-NJ01, DHL-WH-IL02, DHL-WH-TX03)  
**Record count:** 574,509 daily demand records  
**Data quality:** Zero null values, zero duplicate SKU-date-warehouse combinations (confirmed in Project 1 validation)

---

## Methodology

### Step 1 — Monthly Demand Trend Analysis
Aggregate daily demand to monthly level by category and warehouse. Identify 24-month demand
trajectory — overall growth, category-level divergence, and seasonality signal.

### Step 2 — Seasonality Index
Compute monthly seasonality indices by dividing each month's average daily demand by the
24-month overall average. An index > 1.0 indicates an above-average demand month; < 1.0
indicates below average. Planners should apply these indices when setting reorder points in
high-index months.

### Step 3 — Demand Growth Analysis (YoY)
Compare 2022 vs 2023 demand totals by category to identify growing and declining product lines.
Growth-rate outliers — both positive and negative — should trigger a review of forward
replenishment assumptions.

### Step 4 — Forecast Accuracy Baseline (14-Day MA MAPE)
For each active SKU with ≥30 days of demand history, compute a 14-day moving average forecast
and calculate the Mean Absolute Percentage Error (MAPE):

```
MAPE = MEAN(|Actual - Forecast| / Actual) × 100
```

Group MAPE results by ABC class to establish the current forecasting baseline. This number
becomes the benchmark against which future model improvements (e.g., exponential smoothing,
Holt-Winters, or ML-based forecasts) are measured.

### Step 5 — Business Impact Model
Translate stockout frequency (Stockout_Flag days) into estimated lost revenue using:

```
Est. Lost Revenue = Unfulfilled Units × Average Unit Price
Unfulfilled Units = Σ(Quantity_Demanded − Quantity_Fulfilled) where Stockout_Flag = 1
```

This model provides a dollar-denominated justification for investing in forecasting
infrastructure, segmented by ABC class to prioritise where improvement delivers the most value.

---

## Key Findings

### 1. Network Demand is Growing But Unevenly Distributed
24-month demand analysis shows positive overall revenue growth from 2022 to 2023.
Consumer Electronics and Industrial categories — which together represent 55% of network
revenue — are the primary growth drivers. Some categories (Chemicals, Food & Beverage)
show flat or negative unit growth, suggesting mix shift toward higher-value, lower-volume SKUs.

### 2. Seasonality Is Real and Actionable
The monthly seasonality index confirms that demand is not uniform across the calendar year.
Peak months register indices materially above 1.0, while trough months fall below. This means
a flat 14-day moving average will systematically under-forecast in peak months and over-forecast
in trough months — generating predictable stockout risk at exactly the wrong time. Applying
seasonal adjustment to reorder points is a low-cost, high-impact immediate action.

### 3. A-Class Forecast MAPE Is Acceptable as a Starting Point
The 14-day moving average baseline produces a measurable MAPE for each ABC class.
A-class SKUs — where forecast accuracy matters most financially — achieve a lower median
MAPE than C-class SKUs, consistent with their more stable XYZ-X/Y demand profiles.
However, the distribution is wide: some A-class SKUs have MAPE > 40%, identifying
candidates where a more sophisticated model (exponential smoothing or ML) would deliver
immediate accuracy gains.

### 4. Stockout Impact Is Highly Concentrated in A-Class
The business impact model confirms the pattern identified in Project 1: the network-wide
3% stockout rate produces radically different financial consequences by class.
A-class stockouts generate the vast majority of estimated lost revenue. B and C-class
stockouts, while more frequent in absolute terms (more SKUs), contribute minimally to
estimated revenue loss. This concentration justifies a two-tier forecasting investment:
advanced models for A-class SKUs, simple MA for everything else.

### 5. Warehouse NJ01 Carries the Highest Demand Concentration
DHL-WH-NJ01 consistently handles the largest share of demand volume and revenue.
All three warehouses show stable month-over-month patterns with no structural breaks,
confirming consistent operational execution. The NJ01 concentration means any forecasting
improvement rolled out there first will capture the largest share of financial benefit.

### 6. Demand Variability Is Moderate and Category-Dependent
The CV heatmap by month × category reveals that demand variability is not random — certain
categories exhibit higher CV in specific calendar months. This structured variability is
a signal that seasonal adjustment alone may not be sufficient; category-level seasonality
models should be the next analytical step after the baseline MA implementation.

---

## Business Impact

| ABC Class | Unfulfilled Units | Est. Lost Revenue (24 months) | Priority |
|---|---|---|---|
| A | 379,108 | $356.3M | Immediate |
| B | 87,685 | $38.4M | Secondary |
| C | 12,540 | $2.5M | Monitor only |

The primary financial justification for building a forecasting pipeline is the A-class
lost revenue figure. A 30% reduction in A-class stockout rate (the target from Project 1)
applied to the estimated lost revenue figure produces the dollar ROI case for the
engineering investment required to automate this process.

---

## Recommendations

### Immediate (Weeks 1–2)

**1. Apply seasonal index adjustments to reorder points manually.**
Planners can immediately multiply current reorder points by the seasonality index for the
upcoming month. This requires no system change — only a one-page guide (see `planner_guide.md`).

**2. Begin tracking MAPE weekly for the top 50 A-class SKUs.**
Use the 14-day MA as the forecast and record actual demand each week. This creates the
measurement baseline before any system is built, and ensures the DE pipeline has a clear
accuracy target to meet at launch.

**3. Prioritise NJ01 for any pilot implementation.**
The highest demand concentration means a pilot at NJ01 covers the most SKUs, the most
revenue, and produces results fastest. Roll out to IL02 and TX03 in weeks 3–4.

### Medium Term (Weeks 3–8)

**4. Commission the data engineering pipeline.**
The demand forecasting pipeline specification is documented in `pipeline_requirements.md`.
The DE team should scope and deliver the automated daily refresh by end of sprint 3.

**5. Upgrade to exponential smoothing for high-MAPE A-class SKUs.**
Identify A-class SKUs with MAPE > 35% on the 14-day MA baseline. These are candidates
for Holt-Winters exponential smoothing (additive seasonal variant), which can be implemented
in Python within the same pipeline.

**6. Evaluate ML-based forecasting for the AY segment.**
115 AY-segment SKUs carry 56% of revenue and have moderate-to-high demand variability.
After baseline pipeline is stable, a gradient boosting model (e.g., LightGBM with lag
features and seasonal dummies) should be evaluated for this segment in the DS workstream.

---

## Open Questions

1. What is the acceptable MAPE threshold for A-class SKUs from the commercial team's perspective?
2. Should the forecast pipeline output a point estimate or a confidence interval for safety stock?
3. Is the Unit_Price field in sku_master.csv current, or should lost revenue be recalculated using invoice-level pricing from the ERP?
4. What is the desired latency of the daily refresh — same-day (T+0) or next morning (T+1)?

---

## Next Steps

| Action | Owner | Timeline |
|---|---|---|
| Distribute planner_guide.md and seasonal index table | BA/DA | Week 1 |
| Begin manual MAPE tracking (top 50 A-class SKUs) | Inventory Planner | Week 1 |
| Deliver pipeline_requirements.md to DE team | BA/DA | Week 1 |
| Build and test automated forecast pipeline | Data Engineering | Weeks 2–4 |
| Launch dashboard to planners (NJ01 pilot) | BA/DA + DE | Week 5 |
| Review MAPE post-pipeline vs baseline | BA/DA | 30-day review |
| Evaluate advanced model for AY segment | Data Scientist | Q3 2024 |

---

*Document version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 2 · 2024*
