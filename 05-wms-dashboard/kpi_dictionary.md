# WMS KPI Dictionary
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Project:** 05 — WMS Operational Dashboard  
**Date:** 2024  
**Version:** 1.0

---

## Purpose

This dictionary defines every metric used in the WMS Operational Dashboard. It exists to ensure consistent interpretation of KPIs across sites, teams, and reporting periods. Any deviation from these definitions — whether in how a KPI is calculated, what data source it draws from, or what thresholds trigger escalation — must be approved and documented as a version update to this dictionary.

---

## 1. Pick Accuracy %

| Field | Detail |
|---|---|
| **Metric Name** | Pick Accuracy % |
| **Business Definition** | The percentage of pick tasks completed without an error, as recorded by the WMS at the point of scan confirmation. A pick is considered accurate if the operator scanned the correct SKU, at the correct quantity, from the correct location. |
| **Formula** | `SUM(Accuracy_Flag = 1 WHERE Task_Type = 'Pick') / COUNT(*  WHERE Task_Type = 'Pick') × 100` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Accuracy_Flag`, `Error_Code` |
| **Refresh Frequency** | Daily (from WMS export); dashboard reflects last full day's data |
| **Owner** | Site Operations Manager (per site); VP Operations (network) |
| **Threshold — GREEN** | ≥ 99.0% |
| **Threshold — AMBER** | 98.5% – 99.0% |
| **Threshold — RED** | < 98.5% |
| **Related Metrics** | Overall Task Accuracy %, Error Rate %, Picks per Labour Hour |
| **Known Limitations** | Accuracy_Flag is set at the time of WMS scan confirmation and does not capture errors discovered downstream (e.g., wrong item identified at packing). Post-scan error corrections are logged as separate adjustment transactions and are not reflected in this KPI. |

---

## 2. Putaway Compliance %

| Field | Detail |
|---|---|
| **Metric Name** | Putaway Compliance % |
| **Business Definition** | The percentage of putaway tasks completed with the item placed in the WMS-designated location and scanned correctly. A putaway is non-compliant if the operator placed the item in a different location than the WMS directed, or if an error was recorded at scan-in. |
| **Formula** | `SUM(Accuracy_Flag = 1 WHERE Task_Type = 'Putaway') / COUNT(* WHERE Task_Type = 'Putaway') × 100` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Accuracy_Flag` |
| **Refresh Frequency** | Daily |
| **Owner** | Site Operations Manager (per site) |
| **Threshold — GREEN** | ≥ 99.5% |
| **Threshold — AMBER** | 99.0% – 99.5% |
| **Threshold — RED** | < 99.0% |
| **Related Metrics** | Pick Accuracy % (downstream impact), WRONG_LOCATION error rate |
| **Known Limitations** | Putaway compliance captures placement accuracy at time of scan. It does not detect cases where the item was placed correctly but the bin was already over-capacity, or where the item was moved post-confirmation by another operator. |

---

## 3. Cycle Count Accuracy %

| Field | Detail |
|---|---|
| **Metric Name** | Cycle Count Accuracy % |
| **Business Definition** | The percentage of cycle count tasks where the physical count matched the WMS on-hand balance within the accepted tolerance. A cycle count is accurate if the Accuracy_Flag is set to 1 at the point of count confirmation. |
| **Formula** | `SUM(Accuracy_Flag = 1 WHERE Task_Type = 'Cycle Count') / COUNT(* WHERE Task_Type = 'Cycle Count') × 100` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Accuracy_Flag` |
| **Refresh Frequency** | Daily (cycle counts may not occur every day at every site) |
| **Owner** | Quality / Compliance Team; Site Operations Manager |
| **Threshold — GREEN** | ≥ 98.5% |
| **Threshold — AMBER** | 98.0% – 98.5% |
| **Threshold — RED** | < 98.0% |
| **Related Metrics** | Inventory Record Accuracy %, IRA Monthly Trend |
| **Known Limitations** | Cycle count tolerance is set at the WMS level and may differ between sites (e.g., ±1 unit vs. ±5%). If sites apply different tolerances, the Accuracy_Flag is not directly comparable across sites without normalisation. Confirm that all three sites operate under the same cycle count tolerance configuration before using this metric for cross-site benchmarking. |

---

## 4. Overall Task Accuracy %

| Field | Detail |
|---|---|
| **Metric Name** | Overall Task Accuracy % |
| **Business Definition** | The percentage of all warehouse tasks (picks, putaways, and cycle counts combined) completed without a recorded error. This is a composite headline KPI for executive reporting. |
| **Formula** | `SUM(Accuracy_Flag = 1) / COUNT(*) × 100` (across all Task_Type values) |
| **Data Source** | `wms_tasks.csv` — column: `Accuracy_Flag` |
| **Refresh Frequency** | Daily |
| **Owner** | VP Operations (network); Site Operations Manager (per site) |
| **Threshold — GREEN** | ≥ 99.0% |
| **Threshold — AMBER** | 98.5% – 99.0% |
| **Threshold — RED** | < 98.5% |
| **Related Metrics** | Pick Accuracy %, Putaway Compliance %, Cycle Count Accuracy % |
| **Known Limitations** | Because task type volumes differ (picks typically outnumber cycle counts 3:1), overall accuracy is heavily weighted toward pick accuracy. A site with very high pick accuracy but poor cycle count accuracy will still show a strong overall accuracy figure. Always read this metric alongside the task-type-specific KPIs. |

---

## 5. Picks per Labour Hour

| Field | Detail |
|---|---|
| **Metric Name** | Picks per Labour Hour |
| **Business Definition** | The number of pick tasks completed per operator-hour of labour spent on picking. Measures picking efficiency — the rate at which picks are executed, independent of accuracy. |
| **Formula** | `COUNT(* WHERE Task_Type = 'Pick') / (SUM(Duration_Min WHERE Task_Type = 'Pick') / 60)` |
| **Data Source** | `wms_tasks.csv` — columns: `Task_Type`, `Duration_Min` |
| **Refresh Frequency** | Daily |
| **Owner** | Site Operations Manager; Floor Supervisor |
| **Threshold — GREEN** | ≥ 8.0 picks/hr (network average) |
| **Threshold — AMBER** | 7.0 – 8.0 picks/hr |
| **Threshold — RED** | < 7.0 picks/hr |
| **Related Metrics** | Pick Accuracy % (efficiency vs. accuracy trade-off), Average Task Duration |
| **Known Limitations** | Duration_Min reflects the time recorded by the WMS between task assignment and task confirmation. It may include time spent waiting for equipment, searching for a location, or handling an error — not purely productive pick time. Sites with more complex warehouse layouts will naturally show lower PPH. Cross-site PPH comparison should be normalised for warehouse size and task complexity if used for performance-linked incentives. |

---

## 6. Average Task Duration (by Task Type and Warehouse)

| Field | Detail |
|---|---|
| **Metric Name** | Average Task Duration (min) |
| **Business Definition** | The mean time, in minutes, taken to complete a task from WMS assignment to WMS confirmation, broken down by task type and warehouse. |
| **Formula** | `AVG(Duration_Min)` grouped by `Task_Type` and `Warehouse_ID` |
| **Data Source** | `wms_tasks.csv` — columns: `Duration_Min`, `Task_Type`, `Warehouse_ID` |
| **Refresh Frequency** | Daily |
| **Owner** | Floor Supervisor; Site Operations Manager |
| **Threshold** | No fixed threshold; used as a diagnostic metric. A sudden increase in average task duration (>20% above rolling 30-day average) should trigger investigation. |
| **Related Metrics** | Picks per Labour Hour |
| **Known Limitations** | Outlier tasks (e.g., a pick that required a supervisor intervention and took 45 minutes) can significantly distort the average. Use median duration alongside mean for a more robust view of typical task time. |

---

## 7. Error Rate %

| Field | Detail |
|---|---|
| **Metric Name** | Error Rate % |
| **Business Definition** | The percentage of all tasks that resulted in a recorded error code. Inversely related to Overall Task Accuracy: Error Rate % ≈ 100 − Overall Task Accuracy %. |
| **Formula** | `SUM(Error_Code IS NOT NULL) / COUNT(*) × 100` |
| **Data Source** | `wms_tasks.csv` — column: `Error_Code` |
| **Refresh Frequency** | Daily |
| **Owner** | Quality / Compliance Team |
| **Threshold — GREEN** | ≤ 1.0% |
| **Threshold — AMBER** | 1.0% – 1.5% |
| **Threshold — RED** | > 1.5% |
| **Related Metrics** | Overall Task Accuracy %, error code sub-metrics below |
| **Known Limitations** | The Error_Code field is populated only when a specific error type can be identified by the WMS at scan time. Errors that are discovered post-confirmation (e.g., during packing, or reported by the customer) will not appear in this figure. The true error rate may be higher than what is captured at the WMS level. |

---

## 8. Error Code Sub-Metrics

The following five error codes are tracked individually. Each is a count and percentage of total tasks at the site or network level.

| Error Code | Business Definition | Root Cause Hypothesis |
|---|---|---|
| **WRONG_SKU** | Operator picked or putaway a different SKU than directed | Mislabelled shelf, similar packaging between adjacent SKUs, operator shortcut in busy periods |
| **WRONG_QTY** | Correct SKU picked/putaway but wrong quantity | Inner-pack vs outer-pack confusion, unclear quantity display on handheld, unit-of-measure inconsistency |
| **WRONG_LOCATION** | Item placed in or picked from incorrect WMS location | Slot master not updated before physical moves, operator ignoring WMS direction, new operator unfamiliar with layout |
| **MISSING_LABEL** | Label absent or unreadable at time of scan | Label printing failure, label damaged in transit, age of label in slow-moving locations |
| **DAMAGED** | Item found or left in damaged condition during task | Forklift contact, overloaded racking, improper handling of fragile categories |

**Formula (each):** `SUM(Error_Code = '[CODE]') / COUNT(*)  × 100`  
**Data Source:** `wms_tasks.csv` — column: `Error_Code`  
**Owner:** Quality / Compliance Team

---

## 9. Inventory Record Accuracy %

| Field | Detail |
|---|---|
| **Metric Name** | Inventory Record Accuracy % (IRA) |
| **Business Definition** | The ratio of Available Quantity to On-Hand Quantity in the WMS inventory snapshot. Measures how closely the WMS's view of available stock reflects what is physically pickable. A gap indicates that some on-hand stock is reserved, held for quality review, or recorded as damaged but not yet written off. |
| **Formula** | `AVG(Available_Qty / On_Hand_Qty) × 100` across all SKU-warehouse-date combinations |
| **Data Source** | `inventory_snapshot.csv` — columns: `On_Hand_Qty`, `Available_Qty` |
| **Refresh Frequency** | Daily (at time of inventory snapshot) |
| **Owner** | WMS / IT Team; Demand Planning |
| **Threshold — GREEN** | ≥ 85% |
| **Threshold — AMBER** | 80% – 85% |
| **Threshold — RED** | < 80% |
| **Related Metrics** | Cycle Count Accuracy %, Stockout Rate (from demand data) |
| **Known Limitations** | A low IRA does not necessarily mean physical stock is missing — the gap may reflect legitimate reservations, quality holds, or returns in process. IRA should be read alongside cycle count accuracy and stock adjustment logs to distinguish systemic inaccuracy from legitimate holds. |

---

## 10. Stockout Correlation

| Field | Detail |
|---|---|
| **Metric Name** | Stockout Rate % vs Pick Accuracy % (monthly scatter) |
| **Business Definition** | A diagnostic view comparing monthly pick accuracy at each site against the site's monthly stockout rate from demand fulfilment data. Used to identify whether operational accuracy at the WMS level correlates with demand fulfilment failures. |
| **Formula** | `AVG(Stockout_Flag) × 100` per warehouse per month (from `daily_demand.csv`), plotted against monthly pick accuracy |
| **Data Source** | `daily_demand.csv` — column: `Stockout_Flag`; `wms_tasks.csv` — columns: `Task_Type`, `Accuracy_Flag` |
| **Refresh Frequency** | Monthly |
| **Owner** | Demand Planning; VP Operations |
| **Threshold** | No fixed threshold; used as a diagnostic, not a KPI |
| **Known Limitations** | Stockouts at the demand level may be driven by forecasting errors, supplier delays, or minimum order quantity constraints — not by WMS accuracy. The absence of a strong correlation between pick accuracy and stockout rate should not be interpreted as meaning pick accuracy is unimportant; rather, at current accuracy levels, other factors dominate stockout risk. |

---

## Threshold Summary Reference

| KPI | GREEN | AMBER | RED |
|---|---|---|---|
| Pick Accuracy % | ≥ 99.0% | 98.5–99.0% | < 98.5% |
| Putaway Compliance % | ≥ 99.5% | 99.0–99.5% | < 99.0% |
| Cycle Count Accuracy % | ≥ 98.5% | 98.0–98.5% | < 98.0% |
| Overall Task Accuracy % | ≥ 99.0% | 98.5–99.0% | < 98.5% |
| Picks per Labour Hour | ≥ 8.0 | 7.0–8.0 | < 7.0 |
| Error Rate % | ≤ 1.0% | 1.0–1.5% | > 1.5% |
| Inventory Record Accuracy % | ≥ 85% | 80–85% | < 80% |
| Operator Accuracy (individual) | ≥ 99.8% (High Performer) | 98.5–99.8% (Standard) | < 98.5% (Needs Coaching) |

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2024 | Vinyl Kiran Anipe | Initial release |

---

*KPI Dictionary v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 5 · 2024*
