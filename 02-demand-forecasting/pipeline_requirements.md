# Demand Forecasting Pipeline — Requirements Document
**Document type:** DE Handoff / Technical Specification  
**Author:** Vinyl Kiran Anipe (BA/DA)  
**Audience:** Data Engineering Team  
**Date:** June 2024  
**Status:** Ready for DE scoping  
**Related:** `business_narrative.md` (full context), `planner_guide.md` (downstream consumer)

---

## Overview

This document specifies the requirements for an automated daily demand forecasting pipeline
to replace the current manual Excel-based process. The pipeline must ingest daily WMS demand
data, produce SKU-level forecasts and reorder signals, and write outputs to a format
consumable by the Tableau / BI dashboard used by inventory planners.

Estimated scope: 1,664 active SKUs × 3 warehouses × daily refresh.

---

## Inputs

### Primary Data Sources

| Source | System | Format | Refresh | Volume |
|---|---|---|---|---|
| Daily fulfilment records | DHL WMS | CSV extract / SFTP | Daily (T+0 by 06:00 local) | ~2,300 rows/day |
| SKU master | DHL WMS | CSV / static table | Weekly (or on change) | 2,000 rows |
| Inventory snapshot | DHL ERP | CSV / API | Daily | ~2,000 rows |

### Required Input Fields

**daily_demand (append-daily):**
- `SKU_ID` (varchar) — unique SKU identifier
- `Date` (date, YYYY-MM-DD) — demand date
- `Warehouse_ID` (varchar) — one of: DHL-WH-NJ01, DHL-WH-IL02, DHL-WH-TX03
- `Quantity_Demanded` (integer) — total units requested
- `Quantity_Fulfilled` (integer) — units actually shipped
- `Revenue` (float) — revenue for fulfilled units
- `Stockout_Flag` (integer, 0/1) — 1 if Quantity_Fulfilled < Quantity_Demanded
- `ABC_Class` (char) — A, B, or C (from SKU master join)

**sku_master (static reference):**
- `SKU_ID`, `Category`, `ABC_Class`, `Unit_Price`, `Unit_Cost`, `Lead_Time_Days`, `Active_Flag`

---

## Transformations

### Step 1 — Ingestion & Validation
- Ingest new daily_demand records for `Date = TODAY() - 1` (T+1 refresh) or `Date = TODAY()` (T+0).
- Validate: no nulls in `SKU_ID`, `Date`, `Warehouse_ID`, `Quantity_Demanded`.
- Validate: no duplicate `SKU_ID + Date + Warehouse_ID` combinations.
- Validate: `Quantity_Fulfilled` ≤ `Quantity_Demanded` for all rows.
- Alert on validation failure — do not proceed to forecast step with bad data.
- Log row count per warehouse; alert if count deviates > 20% from 30-day average.

### Step 2 — Historical Aggregation
- Maintain a rolling 90-day window of daily demand per SKU (warehouse-level and network-level).
- Aggregate to SKU × Date level (summing across warehouses) for network-level forecast.
- Keep warehouse-level data separate for warehouse-split outputs.

### Step 3 — Forecast Computation

Compute the following forecasts per SKU, per day:

| Forecast | Method | Period | Priority |
|---|---|---|---|
| MA7 | Simple moving average | 7 days | All SKUs |
| MA14 | Simple moving average | 14 days | All SKUs (primary baseline) |
| MA28 | Simple moving average | 28 days | All SKUs |
| Seasonal MA14 | MA14 × seasonality index for current month | 14 days + seasonal factor | A and B-class |

**Seasonality index table** (pre-computed from 24-month history, to be refreshed quarterly):

| Month | Index |
|---|---|
| Jan | TBD — see analysis output |
| Feb | TBD |
| ... | ... |

The seasonality index file path: `shared/data/seasonality_index.csv` — the BA/DA team
will maintain this file and version it quarterly.

**Minimum history requirement:** 14 days of demand data required before any forecast is produced.
SKUs with < 14 days history: output `null` for all forecast columns and flag `forecast_ready = 0`.

### Step 4 — Reorder Signal Computation

For each SKU, compute a daily reorder signal:

```
Reorder_Signal = 1  IF  Current_On_Hand_Qty < (MA14_Forecast × Lead_Time_Days × Safety_Stock_Multiplier)
Reorder_Signal = 0  OTHERWISE
```

Safety stock multipliers by segment (from Project 1 policy framework):

| Segment | SS Multiplier |
|---|---|
| AX | 1.5 |
| AY | 2.0 |
| BX | 1.2 |
| BY | 1.5 |
| CX | 0.8 |
| CY | 1.0 |

`On_Hand_Qty` sourced from `inventory_snapshot.csv` (daily ERP extract).

### Step 5 — MAPE Tracking

For each SKU on each day (where actuals are available for the prior forecast period):
```
MAPE_14d = MEAN(|Actual_t - Forecast_t| / Actual_t)  over the rolling 14-day window
```
Write `MAPE_14d` to the output table daily. Flag any A-class SKU where `MAPE_14d > 35%`
as `accuracy_alert = 1` for planner review.

---

## Output Format

### Primary Output Table: `forecast_output`

Write as a flat CSV (or database table) with one row per `SKU_ID × Date`:

| Column | Type | Description |
|---|---|---|
| `run_date` | date | Date the pipeline ran |
| `forecast_date` | date | Date being forecast (T+1) |
| `SKU_ID` | varchar | SKU identifier |
| `Warehouse_ID` | varchar | Warehouse (or "NETWORK" for aggregated) |
| `ABC_Class` | char | A, B, or C |
| `XYZ_Class` | char | X, Y, or Z |
| `Segment` | varchar | E.g. "AY" |
| `Category` | varchar | Product category |
| `MA7_Forecast` | float | 7-day MA forecast (units) |
| `MA14_Forecast` | float | 14-day MA forecast (units) |
| `MA28_Forecast` | float | 28-day MA forecast (units) |
| `Seasonal_MA14_Forecast` | float | Seasonally adjusted MA14 |
| `Seasonality_Index` | float | Index for forecast_date month |
| `Reorder_Signal` | int (0/1) | 1 = reorder recommended |
| `On_Hand_Qty` | float | Current inventory (from ERP) |
| `Lead_Time_Days` | int | SKU lead time |
| `Safety_Stock_Qty` | float | Computed safety stock |
| `MAPE_14d` | float | Rolling 14-day MAPE (%) |
| `accuracy_alert` | int (0/1) | 1 = MAPE > 35% on A-class |
| `forecast_ready` | int (0/1) | 0 = insufficient history |

### Secondary Output: `seasonality_index.csv`

Refreshed quarterly. Columns: `month_num`, `month_name`, `seasonality_index`.
Path: `shared/data/seasonality_index.csv`.

---

## Refresh Frequency

| Layer | Frequency | Time (local ET) | SLA |
|---|---|---|---|
| Raw demand ingestion | Daily | 06:00 | Data available by 06:30 |
| Forecast computation | Daily | 06:30 | Outputs available by 07:00 |
| Dashboard refresh | Daily | 07:00 | Planners see fresh data at shift start |
| Seasonality index | Quarterly | Manual trigger | BA/DA publishes updated CSV |
| MAPE alert | Daily | 07:00 | Alerts delivered to planner inbox |

---

## Validation Checks

All checks must pass before pipeline outputs are written. On failure: log error, send alert,
write previous day's output with `stale_data_flag = 1`.

| Check | Type | Threshold | Action on Fail |
|---|---|---|---|
| Row count deviation | Warning → Error | > 20% vs 30-day avg | Alert + hold |
| Null values in key fields | Hard error | Any null | Reject batch |
| Duplicate SKU-Date-WH | Hard error | Any duplicate | Reject batch |
| Qty_Fulfilled > Qty_Demanded | Warning | Any row | Log + continue |
| MA14 < 0 | Hard error | Any negative forecast | Alert + investigate |
| MAPE > 60% on A-class | Accuracy alert | Any SKU | Flag + notify planner |

---

## Success Criteria

The pipeline is considered production-ready when:

1. Daily refresh completes and is available to planners by 07:00 ET.
2. All validation checks pass for 5 consecutive business days.
3. MAPE tracking outputs match manual MAPE calculations within 0.1% tolerance.
4. Reorder signals are verified by at least one inventory planner against their current manual process.
5. Dashboard shows forecast data for 100% of active SKUs (1,664 expected).

---

## Dependencies & Assumptions

- WMS SFTP drop is reliable and on schedule. If delayed > 30 minutes, pipeline should retry
  up to 3 times before alerting.
- ERP inventory snapshot uses the same SKU_ID key as WMS demand data — no key mapping required.
- ABC_Class and XYZ_Class assignments from Project 1 analysis are stable for 6 months.
  Pipeline should re-read `sku_master.csv` for ABC_Class; XYZ_Class will be computed
  dynamically from rolling CV in a later pipeline version.
- Initial pipeline language: Python (pandas + DuckDB). Orchestration: Airflow or cron job
  (DE team to decide).
- Storage: output CSV to shared S3 bucket or network drive accessible by Tableau.

---

## Open Items for DE Scoping Call

1. Confirm SFTP vs API extraction method for WMS daily export.
2. Confirm ERP inventory snapshot format and key fields.
3. Agree on orchestration tool (Airflow DAG vs cron + shell script).
4. Confirm Tableau data source connection method (CSV on shared drive vs live database connection).
5. Define alert channel: email, Slack, or PagerDuty for pipeline failures and MAPE alerts.

---

## Contact

**BA/DA owner:** Vinyl Kiran Anipe  
**Review cycle:** Two-week sprint cadence; BA/DA available for requirements questions daily.

---

*Document version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 2 · 2024*
