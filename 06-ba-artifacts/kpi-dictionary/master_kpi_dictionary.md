# Master KPI Dictionary — DHL Supply Chain BA/DA Portfolio
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Covers:** Projects 01–05 (SKU Segmentation, Demand Forecasting, RFM & A/B Test, Warehouse Optimisation, WMS Dashboard)  
**Date:** 2024 · Version 1.0

---

## How to Use This Dictionary

Every metric used across all five projects is defined here exactly once, in the domain where it most naturally belongs. Where a metric is referenced in multiple projects, a cross-reference note indicates this. The threshold columns represent the DHL internal standards established during project analysis; any deviation must be approved and version-controlled in this document.

**Status codes:** 🟢 Green (above threshold) · 🟡 Amber (near threshold) · 🔴 Red (below threshold / requires action)

---

## Domain 1 — Inventory Performance

### 1.1 ABC Classification

| Field | Detail |
|---|---|
| **KPI Name** | ABC Class |
| **Business Definition** | Stratification of the SKU catalogue into three tiers based on cumulative revenue contribution: A-class (top ~8% of SKUs generating ~70% of revenue), B-class (~11% of SKUs, next ~20% of revenue), C-class (~81% of SKUs, remaining ~10% of revenue). Used to prioritise inventory investment, replenishment frequency, and slotting decisions. |
| **Formula** | Sort SKUs by revenue descending. Cumulative revenue pct ≤ 70% → A; ≤ 90% → B; remainder → C |
| **Data Source** | `sku_master.csv` — columns: `SKU_ID`, `Unit_Price`, `Unit_Cost`; `daily_demand.csv` — column: `Revenue` |
| **Project** | Project 01 (SKU Segmentation); cross-referenced in Projects 02, 04, 05 |
| **Refresh Frequency** | Quarterly (demand shifts can alter tier membership) |
| **Owner** | Inventory Planner / BA |
| **Thresholds** | Not a KPI with green/amber/red — a classification label. Monitor the count of A-class SKUs: a sudden 20%+ increase indicates demand shift requiring safety stock review. |
| **Related KPIs** | XYZ Class, AX/BX/CY Segment, Safety Stock Qty, Reorder Point Qty |
| **Known Limitations** | ABC is revenue-based and may under-prioritise strategically critical low-revenue SKUs (e.g., single-source components, hazmat items). Always cross-check against supply risk before acting on ABC alone. Portfolio result: A=164 SKUs (out of 1,664 active), B=213, C=1,287. |

---

### 1.2 XYZ Classification

| Field | Detail |
|---|---|
| **KPI Name** | XYZ Class |
| **Business Definition** | Stratification of SKUs by demand variability using the Coefficient of Variation (CV). X-class: low variability (CV < 0.2) — highly predictable. Y-class: moderate variability (0.2 ≤ CV < 0.5) — seasonally or cyclically variable. Z-class: high variability (CV ≥ 0.5) — intermittent or erratic demand. |
| **Formula** | `CV = Standard Deviation of daily demand / Mean daily demand`. X: CV < 0.2; Y: 0.2 ≤ CV < 0.5; Z: CV ≥ 0.5 |
| **Data Source** | `daily_demand.csv` — columns: `SKU_ID`, `Quantity_Demanded`, `Date` |
| **Project** | Project 01 (SKU Segmentation); cross-referenced in Project 02 |
| **Refresh Frequency** | Quarterly |
| **Owner** | Inventory Planner / BA |
| **Thresholds** | No direct threshold. Flag any AX SKU (highest priority) with CV creeping above 0.25 — it is approaching Y-class and safety stock needs review. |
| **Related KPIs** | ABC Class, Coefficient of Variation, Safety Stock Qty |
| **Known Limitations** | CV is sensitive to zero-demand periods. SKUs with many stockout days will show artificially low CV (zeros suppress variance). Exclude stockout days from the CV calculation or treat separately. |

---

### 1.3 Coefficient of Variation (CV)

| Field | Detail |
|---|---|
| **KPI Name** | Coefficient of Variation (CV) |
| **Business Definition** | The ratio of the standard deviation to the mean of daily demand. A dimensionless measure of demand unpredictability. Higher CV = more difficult and costly to forecast. |
| **Formula** | `CV = σ(daily demand) / μ(daily demand)` |
| **Data Source** | `daily_demand.csv` — columns: `Quantity_Demanded`, `Date`, `SKU_ID` |
| **Project** | Projects 01, 02 |
| **Refresh Frequency** | Quarterly |
| **Owner** | Inventory Planner |
| **Thresholds** | 🟢 CV < 0.20 (predictable) · 🟡 0.20–0.50 (manageable variability) · 🔴 CV ≥ 0.50 (high risk, requires buffer stock review) |
| **Related KPIs** | XYZ Class, Safety Stock Qty, MAPE |
| **Known Limitations** | Meaningless for SKUs with near-zero mean demand (the ratio explodes). Apply only to SKUs with ≥30 active demand days in the measurement window. |

---

### 1.4 Safety Stock Quantity

| Field | Detail |
|---|---|
| **KPI Name** | Safety Stock Quantity (SS) |
| **Business Definition** | The buffer inventory held above expected demand to guard against demand variability and supply lead time uncertainty. Expressed in units. |
| **Formula** | Base SS: `Z × σ(demand) × √(Lead_Time_Days)`. Adjusted SS applies segment multipliers: AX×1.0, AY×1.5, AZ×2.0, BX×1.0, BY×1.25, CY×0.75 (C-class items carry less buffer by design). |
| **Data Source** | `sku_master.csv` — columns: `Lead_Time_Days`; `daily_demand.csv` — columns: `Quantity_Demanded`, `SKU_ID` |
| **Project** | Project 01 |
| **Refresh Frequency** | Quarterly (or when CV or lead time changes materially) |
| **Owner** | Inventory Planner |
| **Thresholds** | Operational target: ≥95% in-stock rate for A-class SKUs. Monitor actual stockout rate as the outcome KPI (see 1.6). |
| **Related KPIs** | Reorder Point, Stockout Rate, CV |
| **Known Limitations** | Formula assumes normally distributed demand. Z-class SKUs with intermittent demand do not fit this model; use probabilistic or simulation-based methods for Z-class instead. |

---

### 1.5 Reorder Point

| Field | Detail |
|---|---|
| **KPI Name** | Reorder Point (ROP) |
| **Business Definition** | The on-hand inventory level at which a replenishment order must be placed to avoid a stockout, given expected demand during lead time. |
| **Formula** | `ROP = (μ(daily demand) × Lead_Time_Days) + Safety_Stock`. Adjusted ROP applies segment multipliers consistent with adjusted safety stock. |
| **Data Source** | `sku_master.csv`, `daily_demand.csv` |
| **Project** | Project 01 |
| **Refresh Frequency** | Quarterly |
| **Owner** | Inventory Planner |
| **Thresholds** | Operational: actual reorder triggering should occur when on-hand ≤ ROP. A stockout that occurs when on-hand was above ROP at last count indicates a cycle counting failure (see Domain 4). |
| **Related KPIs** | Safety Stock, Stockout Rate, Inventory Record Accuracy % |
| **Known Limitations** | ROP assumes constant lead time. If lead time is variable, use a probabilistic lead time buffer. |

---

### 1.6 Stockout Rate %

| Field | Detail |
|---|---|
| **KPI Name** | Stockout Rate % |
| **Business Definition** | The percentage of demand-days on which a SKU was unavailable for fulfilment (Stockout_Flag = 1). Measures the frequency of stock availability failures from the customer's perspective. |
| **Formula** | `SUM(Stockout_Flag = 1) / COUNT(demand days) × 100` per SKU |
| **Data Source** | `daily_demand.csv` — columns: `SKU_ID`, `Stockout_Flag`, `Date` |
| **Project** | Projects 01, 02, 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Inventory Planner; Demand Planning Manager |
| **Thresholds** | 🟢 ≤ 2.0% · 🟡 2.0–5.0% · 🔴 > 5.0%. For A-class SKUs: 🟢 ≤ 1.0% · 🔴 > 3.0% |
| **Related KPIs** | Estimated Lost Revenue, Pick Accuracy %, OTIF %, Inventory Record Accuracy % |
| **Known Limitations** | Stockout_Flag is binary and does not capture partial stockouts (partial fulfilment). The network average stockout rate across 24 months is approximately 3.2%, with A-class SKUs experiencing lower rates due to higher safety stock multipliers. |

---

### 1.7 Estimated Lost Revenue ($)

| Field | Detail |
|---|---|
| **KPI Name** | Estimated Lost Revenue |
| **Business Definition** | The revenue foregone due to stockout events, estimated as the product of average daily demand, unit price, and the number of stockout days. |
| **Formula** | `Stockout_Days × avg_daily_demand × Unit_Price` per SKU |
| **Data Source** | `daily_demand.csv`, `sku_master.csv` — columns: `Unit_Price` |
| **Project** | Projects 01, 02 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager; Demand Planning Manager |
| **Thresholds** | No fixed threshold. Monitor at the category and portfolio level. Flag any single SKU with > $50,000 estimated lost revenue per quarter for expedited review. |
| **Related KPIs** | Stockout Rate %, ABC Class |
| **Known Limitations** | This is an estimate, not an actuals figure. It assumes all stockout demand is truly lost (not back-ordered or substituted). Actual lost revenue may be lower if customers accept substitutes or back orders. |

---

### 1.8 Inventory Record Accuracy %

| Field | Detail |
|---|---|
| **KPI Name** | Inventory Record Accuracy % (IRA) |
| **Business Definition** | The ratio of available (pickable) stock to total on-hand stock in the WMS. Measures how accurately the system reflects physical reality. A gap indicates reservations, quality holds, or unresolved discrepancies. |
| **Formula** | `AVG(Available_Qty / On_Hand_Qty) × 100` across all SKU-warehouse-snapshot combinations |
| **Data Source** | `inventory_snapshot.csv` — columns: `On_Hand_Qty`, `Available_Qty`, `SKU_ID`, `Warehouse_ID`, `Snapshot_Date` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily (from WMS snapshot) |
| **Owner** | WMS Team; Site Operations Manager |
| **Thresholds** | 🟢 ≥ 85% · 🟡 80–85% · 🔴 < 80%. Network average is currently ~80%, indicating a structural gap requiring investigation. |
| **Related KPIs** | Cycle Count Accuracy %, Stockout Rate % |
| **Known Limitations** | A low IRA may reflect legitimate reservations, quality holds, or returns processing — not necessarily errors. Always investigate the composition of the gap before escalating. |

---

## Domain 2 — Demand and Forecast

### 2.1 Mean Absolute Percentage Error (MAPE)

| Field | Detail |
|---|---|
| **KPI Name** | MAPE — 14-Day Moving Average Baseline |
| **Business Definition** | The average percentage error of the 14-day moving average forecast relative to actual demand. Measures baseline forecast accuracy without any advanced modelling. Lower is better. |
| **Formula** | `MEAN(|Actual - Forecast| / Actual × 100)` calculated on the out-of-sample rolling window |
| **Data Source** | `daily_demand.csv` — columns: `Quantity_Demanded`, `Date`, `SKU_ID` |
| **Project** | Project 02 |
| **Refresh Frequency** | Monthly |
| **Owner** | Demand Planning Manager |
| **Thresholds** | 🟢 MAPE < 15% · 🟡 15–30% · 🔴 > 30%. For AX SKUs the bar is higher: 🟢 < 10%. Network 14-day MA baseline MAPE is approximately 12.5–14% for AX SKUs, confirming simple MA as a viable baseline for the most predictable items. |
| **Related KPIs** | CV, ABC/XYZ Class, Forecast Bias |
| **Known Limitations** | MAPE is undefined when actual demand = 0. Exclude zero-demand days or use sMAPE as an alternative. MAPE also penalises over-forecasting and under-forecasting equally; supply-chain contexts typically prefer to penalise under-forecasting more heavily. |

---

### 2.2 Average Daily Demand

| Field | Detail |
|---|---|
| **KPI Name** | Average Daily Demand |
| **Business Definition** | The mean number of units demanded per day for a given SKU over the measurement period. Used as the baseline input for safety stock and reorder point calculations. |
| **Formula** | `SUM(Quantity_Demanded) / COUNT(active demand days)` per SKU |
| **Data Source** | `daily_demand.csv` — columns: `Quantity_Demanded`, `Date`, `SKU_ID` |
| **Project** | Projects 01, 02 |
| **Refresh Frequency** | Monthly (rolling 90-day window recommended) |
| **Owner** | Demand Planning Manager |
| **Thresholds** | No threshold — a descriptive metric. Flag SKUs where 30-day average demand is > 20% above or below the 12-month average (possible trend or data quality issue). |
| **Related KPIs** | CV, Safety Stock, Reorder Point |
| **Known Limitations** | Mean is sensitive to outliers. For intermittent demand SKUs, use median or modal demand instead. Exclude zero-demand days caused by stockouts before calculating mean. |

---

### 2.3 OTIF % (On-Time In-Full)

| Field | Detail |
|---|---|
| **KPI Name** | OTIF % — On-Time In-Full |
| **Business Definition** | The percentage of outbound customer orders that were both shipped on time (within agreed lead time) and fulfilled in full (shipped quantity = ordered quantity). The primary external service level KPI. |
| **Formula** | `SUM(OTIF_Flag = 1) / COUNT(orders) × 100` |
| **Data Source** | `outbound_orders.csv` — columns: `OTIF_Flag`, `On_Time_Flag`, `In_Full_Flag`, `Order_ID` |
| **Project** | Projects 02, 03 |
| **Refresh Frequency** | Daily |
| **Owner** | VP Operations; Account Manager (per customer) |
| **Thresholds** | 🟢 ≥ 95% · 🟡 90–95% · 🔴 < 90%. For Premium / Champions segment customers, the bar is higher: 🟢 ≥ 98%. |
| **Related KPIs** | Pick Accuracy %, Stockout Rate %, Customer Segment (RFM) |
| **Known Limitations** | OTIF is a binary measure — a shipment that is 99% in-full still fails. This can make OTIF appear worse than the underlying service experience. Track "In-Full %" and "On-Time %" separately alongside OTIF to understand which component is driving failures. |

---

### 2.4 Seasonality Index

| Field | Detail |
|---|---|
| **KPI Name** | Seasonality Index |
| **Business Definition** | The ratio of average demand in a given month to the overall annual average demand. A value above 1.0 indicates above-average demand in that month; below 1.0 indicates below-average. Used to adjust safety stock and promotional stocking plans. |
| **Formula** | `Seasonality_Index(month m) = avg_demand(month m across all years) / avg_monthly_demand(full year)` |
| **Data Source** | `daily_demand.csv` — columns: `Quantity_Demanded`, `Date`, `Category` |
| **Project** | Project 02 |
| **Refresh Frequency** | Annually (recalibrate index once per year with rolling 24-month data) |
| **Owner** | Demand Planning Manager |
| **Thresholds** | No threshold. Flag categories with peak index > 1.4 or trough index < 0.7 for proactive stocking and capacity planning. |
| **Related KPIs** | Average Daily Demand, Safety Stock, MAPE |
| **Known Limitations** | Seasonality index derived from only 24 months of data may conflate true seasonality with year-specific demand spikes. Requires 3+ years of data for reliable seasonal patterns. |

---

## Domain 3 — Customer and Commercial

### 3.1 Recency Score (R)

| Field | Detail |
|---|---|
| **KPI Name** | Recency Score (R) — RFM |
| **Business Definition** | A 1–5 score reflecting how recently a customer placed their last order. Score 5 = most recent (highest priority for retention). Score 1 = longest lapsed (at risk of churn). |
| **Formula** | Days since last order calculated per customer. Quintile-ranked across the customer base. Top quintile = R5; bottom quintile = R1. |
| **Data Source** | `outbound_orders.csv` — columns: `Customer_ID`, `Order_Date` |
| **Project** | Project 03 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager; Account Manager |
| **Thresholds** | No direct threshold. Customer with R ≤ 2 and falling should be in the "At Risk" or "Lost" segment and prioritised for win-back outreach. |
| **Related KPIs** | Frequency Score, Monetary Score, RFM Segment, Customer Lifetime Value |
| **Known Limitations** | Recency alone can be misleading: a customer who places one order per year may still be highly loyal. Always read R alongside F and M. |

---

### 3.2 Frequency Score (F)

| Field | Detail |
|---|---|
| **KPI Name** | Frequency Score (F) — RFM |
| **Business Definition** | A 1–5 score reflecting how many orders a customer placed in the measurement period. Score 5 = most frequent buyer. Measures engagement depth. |
| **Formula** | Count of distinct orders per customer in the 24-month window. Quintile-ranked. |
| **Data Source** | `outbound_orders.csv` — columns: `Customer_ID`, `Order_ID`, `Order_Date` |
| **Project** | Project 03 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager |
| **Thresholds** | Customers with F ≥ 4 and R ≥ 4 qualify for "Champions" or "Loyal Customers" tier. |
| **Related KPIs** | Recency Score, Monetary Score, RFM Segment |
| **Known Limitations** | Frequency is affected by contract structure — some customers place one large quarterly order by agreement rather than many small ones. Adjust measurement window or use order value as primary signal for contracted customers. |

---

### 3.3 Monetary Score (M)

| Field | Detail |
|---|---|
| **KPI Name** | Monetary Score (M) — RFM |
| **Business Definition** | A 1–5 score reflecting a customer's total revenue contribution in the measurement period. Score 5 = highest-revenue customer. Measures economic importance. |
| **Formula** | Sum of Revenue per Customer_ID in the 24-month window. Quintile-ranked. |
| **Data Source** | `outbound_orders.csv` — columns: `Customer_ID`, `Revenue` |
| **Project** | Project 03 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager; VP Sales |
| **Thresholds** | M5 customers represent the top 20% by revenue. Any M5 customer with declining R should trigger an immediate account review. |
| **Related KPIs** | Recency Score, Frequency Score, RFM Segment, Average Order Value |
| **Known Limitations** | Revenue can be inflated by one-time large orders. Consider using average order value alongside total monetary value to distinguish high-frequency medium-value customers from low-frequency high-value customers. |

---

### 3.4 RFM Segment

| Field | Detail |
|---|---|
| **KPI Name** | RFM Segment |
| **Business Definition** | A composite customer classification derived from combined R, F, and M scores. Seven segments are defined: Champions (R5F5M5 area), Loyal Customers, Potential Loyalists, New Customers, At Risk, About to Sleep, Lost. |
| **Formula** | Rule-based segmentation applied to R+F+M combined score and individual score thresholds. See `03-rfm-ab-test/business_narrative.md` for full segment rule table. |
| **Data Source** | `outbound_orders.csv` |
| **Project** | Project 03 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager |
| **Thresholds** | Monitor the count of customers in "At Risk" and "Lost" segments monthly. Alert if: At Risk count grows > 10% MoM, or Lost count exceeds 25% of total customer base. Portfolio result: Champions=36, Loyal=34, Potential Loyalists=151, New=18, At Risk=46, About to Sleep=33, Lost=80. |
| **Related KPIs** | R, F, M scores; OTIF %; Average Order Value |
| **Known Limitations** | Segment thresholds are set on the current customer base and will drift over time as the base grows or shrinks. Recalibrate quintile boundaries annually. |

---

### 3.5 Average Order Value (AOV)

| Field | Detail |
|---|---|
| **KPI Name** | Average Order Value (AOV) |
| **Business Definition** | The mean revenue per order placed by a customer. Used as a guardrail metric in A/B test analysis — a retention campaign should not significantly reduce AOV as a side effect. |
| **Formula** | `SUM(Revenue) / COUNT(Order_ID)` per customer |
| **Data Source** | `outbound_orders.csv` — columns: `Revenue`, `Order_ID`, `Customer_ID` |
| **Project** | Project 03 |
| **Refresh Frequency** | Monthly |
| **Owner** | Commercial Manager |
| **Thresholds** | Guardrail (A/B test context): 🔴 if campaign group AOV is significantly lower than control group AOV (p < 0.05). As a business metric: no absolute threshold; track trend per segment. |
| **Related KPIs** | RFM Segment, Monetary Score, Total Revenue per Customer |
| **Known Limitations** | AOV is distorted by outlier orders. Use median AOV alongside mean for a more robust view. |

---

### 3.6 A/B Test Conversion Rate (90-Day Re-order)

| Field | Detail |
|---|---|
| **KPI Name** | 90-Day Re-order Conversion Rate |
| **Business Definition** | The percentage of "At Risk" customers in the test group who placed at least one order within 90 days of receiving the retention offer. The primary success metric for the retention campaign A/B test. |
| **Formula** | `COUNT(customers with ≥1 order in 90 days post-offer) / COUNT(test group customers) × 100` |
| **Data Source** | Simulated post-campaign order data; `outbound_orders.csv` |
| **Project** | Project 03 |
| **Refresh Frequency** | Point-in-time (measured at Day 90 post-campaign launch) |
| **Owner** | Commercial Manager |
| **Thresholds** | MDE (Minimum Detectable Effect) set at +10pp lift over control baseline. Portfolio result: not statistically significant (p=0.555). Recommend extending sample size or campaign duration before re-testing. |
| **Related KPIs** | AOV (guardrail), RFM Segment |
| **Known Limitations** | Simulated results only — based on modelled order probability. Actual campaign results must be tracked against this baseline at 90 days post-launch. |

---

## Domain 4 — Warehouse Operations

### 4.1 Pick Accuracy %

| Field | Detail |
|---|---|
| **KPI Name** | Pick Accuracy % |
| **Business Definition** | The percentage of pick tasks completed without a recorded error in the WMS. A pick is accurate if the correct SKU was taken from the correct location at the correct quantity. |
| **Formula** | `SUM(Accuracy_Flag=1 WHERE Task_Type='Pick') / COUNT(Task_Type='Pick') × 100` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Accuracy_Flag`, `Error_Code` |
| **Project** | Projects 04, 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Site Operations Manager |
| **Thresholds** | 🟢 ≥ 99.0% · 🟡 98.5–99.0% · 🔴 < 98.5%. Network result: 99.27% (GREEN across all three sites). |
| **Related KPIs** | Putaway Compliance %, Error Rate %, OTIF %, Picks per Labour Hour |
| **Known Limitations** | Captures errors at scan time only. Post-confirmation errors (discovered at packing or by customer) are not reflected. True error rate may be slightly higher. |

---

### 4.2 Putaway Compliance %

| Field | Detail |
|---|---|
| **KPI Name** | Putaway Compliance % |
| **Business Definition** | The percentage of putaway tasks where the item was placed in the WMS-directed location and confirmed with a scan. Non-compliance creates downstream pick errors (WRONG_LOCATION cascade). |
| **Formula** | `SUM(Accuracy_Flag=1 WHERE Task_Type='Putaway') / COUNT(Task_Type='Putaway') × 100` |
| **Data Source** | `wms_tasks.csv` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Site Operations Manager |
| **Thresholds** | 🟢 ≥ 99.5% · 🟡 99.0–99.5% · 🔴 < 99.0%. Network result: 99.70% (GREEN). |
| **Related KPIs** | Pick Accuracy %, WRONG_LOCATION error rate |
| **Known Limitations** | Does not detect post-confirmation relocation by another operator. |

---

### 4.3 Cycle Count Accuracy %

| Field | Detail |
|---|---|
| **KPI Name** | Cycle Count Accuracy % |
| **Business Definition** | The percentage of cycle count tasks where the physical count matched the WMS on-hand balance within tolerance. The leading indicator of Inventory Record Accuracy. |
| **Formula** | `SUM(Accuracy_Flag=1 WHERE Task_Type='Cycle Count') / COUNT(Task_Type='Cycle Count') × 100` |
| **Data Source** | `wms_tasks.csv` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Quality / Compliance Team |
| **Thresholds** | 🟢 ≥ 98.5% · 🟡 98.0–98.5% · 🔴 < 98.0%. Network: 98.49% (AMBER at IL02 98.36%, NJ01 98.49%). |
| **Related KPIs** | Inventory Record Accuracy %, Stockout Rate % |
| **Known Limitations** | Cycle count tolerance may vary by site. Cross-site comparison requires confirmation that all sites use identical tolerance settings. |

---

### 4.4 Overall Task Accuracy %

| Field | Detail |
|---|---|
| **KPI Name** | Overall Task Accuracy % |
| **Business Definition** | Composite accuracy across all WMS task types (pick, putaway, cycle count). Primary headline KPI for executive reporting and SLA compliance. |
| **Formula** | `SUM(Accuracy_Flag=1) / COUNT(*) × 100` across all task types |
| **Data Source** | `wms_tasks.csv` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily |
| **Owner** | VP Operations |
| **Thresholds** | 🟢 ≥ 99.0% · 🟡 98.5–99.0% · 🔴 < 98.5%. Network result: 99.35% (GREEN). |
| **Related KPIs** | Pick Accuracy %, Putaway Compliance %, Cycle Count Accuracy % |
| **Known Limitations** | Heavily weighted by pick volume (picks are ~50% of all tasks). Poor cycle count accuracy will barely move this headline figure. Always read alongside task-type sub-metrics. |

---

### 4.5 Picks per Labour Hour

| Field | Detail |
|---|---|
| **KPI Name** | Picks per Labour Hour (PPH) |
| **Business Definition** | The number of pick tasks completed per operator-hour of labour. Measures picking efficiency alongside pick accuracy — the two must be read together to avoid rewarding speed at the cost of quality. |
| **Formula** | `COUNT(Task_Type='Pick') / (SUM(Duration_Min WHERE Task_Type='Pick') / 60)` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Duration_Min` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Floor Supervisor; Site Operations Manager |
| **Thresholds** | 🟢 ≥ 8.0 picks/hr · 🟡 7.0–8.0 · 🔴 < 7.0. Network average: 8.0 picks/hr (consistent across all three sites). |
| **Related KPIs** | Pick Accuracy %, Average Task Duration |
| **Known Limitations** | Duration_Min includes non-productive time (waiting, equipment search). Cross-site PPH comparison should account for warehouse layout complexity and task mix. |

---

### 4.6 Annual Labour Saved ($) — Slotting

| Field | Detail |
|---|---|
| **KPI Name** | Annual Labour Saved — Slotting Optimisation |
| **Business Definition** | The estimated annual reduction in operator travel time (converted to labour cost) from moving misplaced Hot/Warm SKUs to optimal pick face locations. Based on observed travel time differentials between pick zones. |
| **Formula** | `(Pick_Face_Time - Current_Zone_Time) × Annual_Pick_Count × Hourly_Labour_Rate`. Annualised from 24-month observed data. |
| **Data Source** | `wms_tasks.csv` — column: `Duration_Min`; `sku_master.csv` |
| **Project** | Project 04 |
| **Refresh Frequency** | Point-in-time (calculated at project delivery; to be recalculated post-implementation) |
| **Owner** | BA/DA; Warehouse Operations Manager |
| **Thresholds** | Implementation decision threshold: ROI ≥ 3.0× (all three initiatives exceed this). Portfolio result: Slotting ROI 9.1×, Break-even 80 days; total programme ROI 5.8×, break-even 125 days. |
| **Related KPIs** | Picks per Labour Hour, SKU Mismatch Count, Implementation Cost |
| **Known Limitations** | Labour saving is estimated from synthetic data modelling. Actual savings depend on operator compliance, slotting implementation completeness, and demand stability. Post-implementation measurement is required to validate the estimate. |

---

### 4.7 Slotting Mismatch Rate

| Field | Detail |
|---|---|
| **KPI Name** | SKU Slotting Mismatch Count / Rate |
| **Business Definition** | The number (and percentage) of SKUs whose current storage zone does not match their demand tier. Hot SKUs in Reserve or Bulk storage, or Cold SKUs occupying Pick_Face space, are mismatches. |
| **Formula** | Count of SKUs where `Recommended_Tier ≠ Current_Zone_Tier`. Rate = `Mismatch_Count / Total_SKUs × 100`. |
| **Data Source** | `wms_tasks.csv` (to derive pick frequency); zone data inferred from task location patterns |
| **Project** | Project 04 |
| **Refresh Frequency** | Quarterly (re-run slotting analysis after demand review) |
| **Owner** | Warehouse Operations Manager; BA/DA |
| **Thresholds** | 🟢 < 10% mismatch rate · 🟡 10–20% · 🔴 > 20%. Portfolio result before optimisation: 290 mismatched SKUs out of 1,664 active = 17.4% (AMBER). |
| **Related KPIs** | Annual Labour Saved, Pick Accuracy %, Picks per Labour Hour |
| **Known Limitations** | Mismatch is defined relative to current demand tiers. A SKU with seasonally variable demand may correctly sit in Reserve during low season and Pick_Face during peak. Use rolling 90-day pick frequency for the most current tier assignment. |

---

## Domain 5 — Data Quality

### 5.1 Error Rate % (WMS)

| Field | Detail |
|---|---|
| **KPI Name** | WMS Error Rate % |
| **Business Definition** | The percentage of all WMS tasks that resulted in a recorded error code. The five error codes are: WRONG_SKU, WRONG_QTY, WRONG_LOCATION, MISSING_LABEL, DAMAGED. |
| **Formula** | `SUM(Error_Code IS NOT NULL) / COUNT(*) × 100` |
| **Data Source** | `wms_tasks.csv` — column: `Error_Code` |
| **Project** | Project 05 |
| **Refresh Frequency** | Daily |
| **Owner** | Quality / Compliance Team |
| **Thresholds** | 🟢 ≤ 1.0% · 🟡 1.0–1.5% · 🔴 > 1.5%. Network result: 0.65% (GREEN). |
| **Related KPIs** | Pick Accuracy %, error code sub-metrics |
| **Known Limitations** | Error codes are only captured when the WMS can identify the error type at scan time. Some errors (wrong item shipped) are discovered downstream and not reflected here. |

---

### 5.2 High-Error SKU Flag

| Field | Detail |
|---|---|
| **KPI Name** | High-Error SKU Flag |
| **Business Definition** | A binary flag applied to SKUs whose error rate has exceeded 2% in three or more consecutive months. Indicates a systemic product-level issue (labelling, packaging, configuration) rather than isolated operator error. |
| **Formula** | Per SKU: count months where `(errors/tasks) > 0.02`. Flag = 1 if count ≥ 3 consecutive months. |
| **Data Source** | `wms_tasks.csv` — columns: `SKU_ID`, `Error_Code`, `Task_Date` |
| **Project** | Project 05 |
| **Refresh Frequency** | Monthly |
| **Owner** | Quality Team; BA/DA |
| **Thresholds** | HIGH severity: ≥4 months above threshold. MEDIUM: 3 months. Portfolio result: 9 HIGH-severity SKUs, 11 MEDIUM = 20 total flagged. |
| **Related KPIs** | Error Rate %, Data Quality Flags count |
| **Known Limitations** | Three consecutive months is an arbitrary threshold. For high-velocity A-class SKUs, a single month above 2% may warrant investigation given the volume of errors involved. |

---

### 5.3 Operator Coaching Flag

| Field | Detail |
|---|---|
| **KPI Name** | Operator Coaching Flag |
| **Business Definition** | A flag applied to individual operators whose overall task accuracy falls below 98.5% across their full task history. Triggers a coaching conversation and improvement plan. Operators above 99.8% receive a High Performer flag. |
| **Formula** | `SUM(Accuracy_Flag=1) / COUNT(*) × 100` per Operator_ID. Apply flag if < 98.5% (coaching) or ≥ 99.8% (high performer). |
| **Data Source** | `wms_tasks.csv` — columns: `Operator_ID`, `Accuracy_Flag` |
| **Project** | Project 05 |
| **Refresh Frequency** | Monthly |
| **Owner** | Floor Supervisor; Site Operations Manager |
| **Thresholds** | Coaching: < 98.5%. Standard: 98.5–99.8%. High Performer: ≥ 99.8%. Portfolio result: 0 coaching, 176 standard, 4 high performers (out of 180 operators). |
| **Related KPIs** | Pick Accuracy %, Shift Error Spike Flag |
| **Known Limitations** | Lifetime accuracy smooths over recent performance. An operator with strong historical performance but declining recent accuracy needs current-period monitoring, not just lifetime scoring. |

---

### 5.4 Shift Error Spike Flag

| Field | Detail |
|---|---|
| **KPI Name** | Shift Error Spike Flag |
| **Business Definition** | A flag applied to an operator-shift combination where that operator's error rate on one specific shift is significantly higher than their error rate on other shifts. Indicates potential fatigue, training gap, or supervision issue on that shift. |
| **Formula** | Per operator: calculate error rate by shift. Flag if any single shift's error rate is ≥ 2× the operator's average error rate on other shifts, and the shift has ≥ 30 tasks. |
| **Data Source** | `wms_tasks.csv` — columns: `Operator_ID`, `Shift`, `Error_Code` |
| **Project** | Project 05 |
| **Refresh Frequency** | Monthly |
| **Owner** | Floor Supervisor |
| **Thresholds** | Any spike flag triggers a supervisor conversation (not necessarily a formal coaching action). Portfolio result: 10 shift error spikes flagged across the network. |
| **Related KPIs** | Operator Coaching Flag, Shift Heatmap |
| **Known Limitations** | Small sample sizes per shift can make this flag noisy. Always verify the task count before acting on a spike flag. |

---

## Threshold Summary Reference

| Domain | KPI | 🟢 Green | 🟡 Amber | 🔴 Red |
|---|---|---|---|---|
| Inventory | Stockout Rate % (A-class) | ≤ 1.0% | 1.0–3.0% | > 3.0% |
| Inventory | Inventory Record Accuracy % | ≥ 85% | 80–85% | < 80% |
| Demand | MAPE (14-day MA, AX) | < 10% | 10–15% | > 15% |
| Demand | CV | < 0.20 | 0.20–0.50 | ≥ 0.50 |
| Customer | OTIF % | ≥ 95% | 90–95% | < 90% |
| Customer | At Risk customer growth MoM | ≤ 5% | 5–10% | > 10% |
| Warehouse | Pick Accuracy % | ≥ 99.0% | 98.5–99.0% | < 98.5% |
| Warehouse | Putaway Compliance % | ≥ 99.5% | 99.0–99.5% | < 99.0% |
| Warehouse | Cycle Count Accuracy % | ≥ 98.5% | 98.0–98.5% | < 98.0% |
| Warehouse | Overall Task Accuracy % | ≥ 99.0% | 98.5–99.0% | < 98.5% |
| Warehouse | Picks per Labour Hour | ≥ 8.0 | 7.0–8.0 | < 7.0 |
| Warehouse | Slotting Mismatch Rate | < 10% | 10–20% | > 20% |
| Data Quality | WMS Error Rate % | ≤ 1.0% | 1.0–1.5% | > 1.5% |
| Data Quality | High-Error SKU count | 0 | 1–5 | > 5 |

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2024 | Vinyl Kiran Anipe | Initial release — consolidates Projects 01–05 |

---

*Master KPI Dictionary v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · 2024*
