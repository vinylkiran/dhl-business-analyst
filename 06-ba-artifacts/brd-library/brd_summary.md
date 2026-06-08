# Business Requirements Summary — DHL BA/DA Portfolio
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Covers:** Projects 01–05  
**Date:** 2024 · Version 1.0

---

## Purpose

This document provides any incoming analyst or stakeholder with an instant orientation to every analytical project completed in this portfolio. For each project it records the business problem, what was built, who it was for, what the data said, and what decisions were made. It is intentionally brief — the full context lives in each project's `business_narrative.md`.

---

## Project 01 — SKU Segmentation and Inventory Optimisation

**Problem Statement:** DHL's inventory planners had no systematic, data-driven method for prioritising which SKUs required tight replenishment management and which could be managed with lighter-touch reorder rules. All 2,000 SKUs across three warehouses were treated with broadly the same safety stock policy, resulting in over-investment in slow-moving C-class items and under-buffering of high-revenue, high-velocity A-class SKUs. Planners relied on manual experience and ad-hoc spreadsheets, with no auditable methodology.

**Business Objective:** Segment the full SKU catalogue using ABC (revenue importance) and XYZ (demand variability) classification. Derive differentiated safety stock and reorder point recommendations by segment. Identify which SKUs are at highest risk of stockout and which are consuming disproportionate working capital.

**Primary Stakeholders:** Inventory Planner, Demand Planning Manager, VP Operations

**Success Metrics Defined:**
- Full segmentation of all active SKUs into AX/AY/AZ/BX/BY/CX/CY/CZ categories
- Safety stock and reorder point recommendations for each SKU with documented formula
- Identification of high-stockout-risk A-class SKUs (stockout rate > 3%)
- Tableau-compatible export for planner self-service use

**Data Sources Used:**
- `sku_master.csv` — 2,000 SKUs with unit cost, price, lead time, category
- `daily_demand.csv` — 24 months of daily demand, stockout flags, revenue
- `inventory_snapshot.csv` — on-hand and available quantity snapshots

**Key Decisions Made:**
- ABC thresholds set at 70%/90% cumulative revenue (industry standard; not site-specific)
- XYZ thresholds: CV < 0.2 = X, 0.2–0.5 = Y, ≥ 0.5 = Z
- Safety stock multipliers by segment (AX×1.0 to AZ×2.0) agreed with Inventory Planner
- CZ SKUs flagged for potential rationalisation rather than increased safety stock

**Key Findings:**
- 164 A-class SKUs (out of 1,664 active) drive ~70% of revenue; Industrial and Consumer Electronics categories are over-represented in the A-class
- 49 AX SKUs are the highest-priority replenishment items — predictable and high-value
- C-class SKUs account for 77% of the catalogue but only ~10% of revenue; 1,048 CY SKUs represent over-investment risk
- Several AZ SKUs have stockout rates above 5% — erratic demand and high value is the most dangerous combination
- Estimated lost revenue from stockouts across the A-class exceeds $50M in the 24-month window

**Status:** ✅ Complete. Outputs: `sku_segments.csv`, Tableau export CSVs, `sku_segmentation_dashboard.html`, `business_narrative.md`

---

## Project 02 — Demand Forecasting and Pipeline Requirements

**Problem Statement:** The demand planning team used ad-hoc Excel-based forecasts with no standardised methodology, making it impossible to measure forecast accuracy or improve systematically. There was no agreed definition of "good enough" forecasting, no documented baseline against which to compare any future improvements, and no pipeline specification for a data engineer to build an automated forecast refresh.

**Business Objective:** Establish a quantified forecast accuracy baseline using a 14-day moving average model. Identify which SKU segments can be served well by simple methods and which require more sophisticated approaches. Produce a formal pipeline requirements document for the DE team to build an automated daily forecast refresh. Produce a planner guide for daily use.

**Primary Stakeholders:** Demand Planning Manager, VP Operations, Data Engineering Team (pipeline consumer), Finance (for budget planning cycle alignment)

**Success Metrics Defined:**
- MAPE baseline established per ABC/XYZ segment
- Clear identification of segments where simple MA ≥ acceptable accuracy
- Pipeline specification meeting DE team requirements (schema, refresh cadence, SLA)
- Seasonality index derived for all eight product categories

**Data Sources Used:**
- `daily_demand.csv` — 24 months daily demand, revenue, stockout flags
- `sku_master.csv` — ABC/XYZ classification, category

**Key Decisions Made:**
- 14-day moving average chosen as the baseline (not 7-day or 30-day) — balances responsiveness and smoothing for the observed demand patterns
- MAPE calculated on out-of-sample last-30-day window to prevent look-ahead bias
- Pipeline spec written to produce daily outputs by 06:00 for same-day planner use
- Z-class SKUs explicitly excluded from the moving average model — flagged for probabilistic or simulation-based methods

**Key Findings:**
- AX SKUs achieve 12.5–14% MAPE with a simple 14-day MA — acceptable for operational planning
- AY SKUs show MAPE of 18–22% — seasonal adjustment needed to bring within acceptable range
- Z-class SKUs are fundamentally unsuitable for moving average methods; intermittent demand requires a separate approach
- Consumer Electronics and Fashion & Apparel categories show the strongest seasonality (peak index ~1.3–1.4 in Q4)
- Network stockout rate of ~3.2% is highest in AZ and BZ segments — confirming that unpredictable, medium-high-value SKUs carry the most risk

**Status:** ✅ Complete. Outputs: `demand_summary.csv`, 13 figures, `forecast_dashboard.html`, `business_narrative.md`, `pipeline_requirements.md`, `planner_guide.md`

---

## Project 03 — RFM Customer Segmentation and A/B Test Design

**Problem Statement:** The commercial team had 398 active customers but no structured view of which customers were at risk of churn, which were growing, and which had lapsed. Account management was largely reactive — issues were identified when a customer called, not before. There was no data-backed framework for prioritising outreach or designing differentiated retention and growth offers.

**Business Objective:** Segment all customers using the RFM framework (Recency, Frequency, Monetary) to create an actionable customer tier structure. Design a statistically rigorous A/B test for a retention campaign targeting the "At Risk" segment. Produce a segment playbook for account managers, a test design document for the commercial team, and an interactive dashboard.

**Primary Stakeholders:** Commercial Manager, Account Managers (×3), VP Sales, Marketing Team

**Success Metrics Defined:**
- All 398 customers classified into one of seven RFM segments
- A/B test design with calculated sample size (power = 0.80, α = 0.05, MDE = +10pp conversion lift)
- Test readout produced on simulated post-campaign data
- Segment playbook delivered for account manager daily use

**Data Sources Used:**
- `outbound_orders.csv` — 24 months of order history, revenue, OTIF flags, channel, customer type
- `customers.csv` — customer metadata (region, type, annual revenue band)

**Key Decisions Made:**
- RFM quintile scoring applied across the full customer base (not by segment type)
- Seven segment labels chosen (Champions through Lost) aligned with industry-standard RFM taxonomy
- A/B test targets "At Risk" segment (46 customers) — the highest-value recoverable group
- Minimum Detectable Effect set at +10pp conversion rate lift, yielding required n=46 per group (full At Risk segment as test group)
- Control group drawn from historically non-contacted customers in the same RFM range

**Key Findings:**
- 46 "At Risk" customers have combined prior-year revenue that makes retention commercially material
- 80 "Lost" customers represent significant lapsed revenue — win-back is lower probability but higher upside per conversion
- Champions and Loyal Customers (70 total) have OTIF rates 3–5pp higher than the rest of the base — service quality is a retention driver for top customers
- A/B test result: NOT statistically significant (p=0.555) — the sample is at the boundary of statistical power and the simulated effect is smaller than the MDE; recommend extending to 120-day follow-up period
- Potential Loyalists (151 customers) are the most actionable growth segment — already engaged, not yet fully committed

**Status:** ✅ Complete. Outputs: `customer_rfm.csv`, `rfm_segments.csv`, `ab_test_readout.txt`, `rfm_dashboard.html`, `business_narrative.md`, `segment_playbook.md`, `test_design_doc.md`

---

## Project 04 — Warehouse Slotting Optimisation

**Problem Statement:** Across three DHL warehouses, high-velocity "Hot" SKUs were stored in suboptimal zones (Reserve or Bulk) while low-velocity "Cold" SKUs occupied premium Pick_Face space. This misalignment forced operators to travel further per pick on high-frequency items, inflating pick duration and labour cost without any corresponding benefit. The magnitude of the misalignment had never been quantified, making it impossible to build a business case for remediation.

**Business Objective:** Quantify the SKU slotting mismatch across all three sites. Build a frequency-based slotting recommendation for every misplaced SKU with a calculated ROI, labour saving, and break-even period. Produce a zone utilisation analysis, a SKU affinity analysis (commonly co-picked items), and a phased implementation plan for the operations team.

**Primary Stakeholders:** Warehouse Operations Manager, WMS/IT Team, Floor Supervisors, VP Operations

**Success Metrics Defined:**
- All misplaced SKUs identified and ranked by labour saving
- ROI calculated for slotting programme (target ≥ 3.0×)
- Implementation plan with clear owner, timeline, and success criteria per phase
- WRONG_LOCATION error baseline established for post-implementation comparison

**Data Sources Used:**
- `wms_tasks.csv` — 24 months of task data including zone, duration, error codes
- `sku_master.csv` — ABC class, category, unit cost

**Key Decisions Made:**
- Hot/Warm/Cold tiers defined by pick frequency percentile (Hot: top 30%, Warm: next 20%, Cold: bottom 50%) — calibrated to DHL's actual task distribution
- Labour saving calculated using average pick-time differential between zones (Pick_Face vs Reserve vs Bulk), derived from the Duration_Min data
- Adjacency analysis limited to pairs with ≥ 5 co-pick occurrences to avoid noise from coincidental co-picks
- Implementation sequenced in three phases: Hot SKUs first (highest ROI), Cold SKU clearance second, Warm re-sort and monitoring third

**Key Findings:**
- 290 SKUs are misplaced (17.4% mismatch rate — AMBER): 167 Hot SKUs not in Pick_Face, 123 Cold SKUs occupying Pick_Face
- Total programme ROI: 5.8× over 24 months. Break-even: 125 days. Implementation cost: $3,838
- Slotting optimisation alone (391 SKUs) saves $22,222 in labour over 24 months; ROI 9.1×
- Cold SKU clearance from Pick_Face frees high-value shelf space: $7,462 opportunity saving
- WRONG_LOCATION errors are highest at TX03 — consistent with recent slotting changes not yet fully settled
- 50 high-affinity SKU pairs identified; co-locating them would reduce multi-zone picks, but adjacency ROI is marginal (0.3× — not prioritised in Phase 1)

**Status:** ✅ Complete. Outputs: `slotting_recommendations.csv`, `zone_summary.csv`, `impact_summary.csv`, `adjacency_recommendations.csv`, `warehouse_dashboard.html`, `business_narrative.md`, `ops_recommendation.md`, `implementation_plan.md`

---

## Project 05 — WMS Operational Dashboard

**Problem Statement:** Warehouse managers across three sites each tracked KPIs using local, inconsistent Excel files. This meant network-level performance was invisible to VP Operations, cross-site benchmarking was impossible (because KPI definitions differed between sites), and data quality issues — SKUs with persistent error rates, operators with shift-specific performance spikes — were never surfaced until they caused operational failures. There was no single source of truth for WMS performance.

**Business Objective:** Build a standardised, multi-site WMS operational dashboard covering all three sites. Define KPIs uniformly in a formal KPI dictionary. Analyse 219,000 WMS tasks across 24 months to establish performance baselines, operator scorecards, and a data quality monitoring layer. Produce a user guide, weekly report template, and management narrative for the VP Operations team.

**Primary Stakeholders:** VP Operations, Site Operations Managers (×3), Floor Supervisors, Quality/Compliance Team, WMS/IT Team, Demand Planning (for inventory correlation)

**Success Metrics Defined:**
- Network-wide KPI baselines established for all five core metrics
- All 180 operators scored and flagged
- Data quality flags exported for 34 entities (SKUs, zones, operators)
- Dashboard available to all site managers with no technical dependency
- KPI dictionary approved and versioned

**Data Sources Used:**
- `wms_tasks.csv` — 219,000 tasks: picks, putaways, cycle counts across 3 sites, 3 shifts, 180 operators, 24 months
- `inventory_snapshot.csv` — daily IRA snapshots
- `daily_demand.csv` — stockout correlation analysis
- `sku_master.csv` — SKU category and ABC class enrichment

**Key Decisions Made:**
- KPI thresholds set at industry-standard 3PL SLA levels (pick accuracy 99.0%, putaway 99.5%) with amber at 0.5pp below threshold
- H1/H2 split used for performance trend classification (improving/stable/declining) at operator level
- Data quality flags use a 3-consecutive-months threshold for SKU error persistence — avoids noise from single-month spikes
- Dashboard built in Chart.js (not Plotly) to avoid timeout issues with 219k-row dataset; data pre-aggregated into CSVs before HTML generation

**Key Findings:**
- Network pick accuracy 99.27% (GREEN), putaway 99.70% (GREEN), cycle count 98.49% (AMBER at IL02 and NJ01)
- 4 high performers identified; 0 operators below coaching threshold — strong network baseline
- 20 SKUs flagged with persistent high error rates (≥3 months above 2%); primarily Fashion & Apparel and FMCG categories
- Night shift performance varies significantly by site: IL02 night is the weakest shift; TX03 night is the strongest
- Inventory record accuracy sits at ~80% across all sites — structural ~20% on-hand/available gap requiring investigation
- No strong statistical correlation between pick accuracy and stockout rates at current accuracy levels — other factors dominate stockout risk

**Status:** ✅ Complete. Outputs: `kpi_summary.csv`, `kpi_by_warehouse_shift.csv`, `operator_scorecard.csv`, `data_quality_flags.csv`, 16 figures, `wms_dashboard.html`, `business_narrative.md`, `kpi_dictionary.md`, `dashboard_user_guide.md`, `management_report_template.md`

---

## Portfolio Status Summary

| Project | Status | Key Output | Business Value |
|---|---|---|---|
| 01 — SKU Segmentation | ✅ Complete | Segmented catalogue + SS/ROP rules | Working capital optimisation; reduces over-stocking of C-class SKUs |
| 02 — Demand Forecasting | ✅ Complete | Forecast baseline + DE pipeline spec | Enables automated daily forecast; reduces planner manual effort |
| 03 — RFM & A/B Test | ✅ Complete | Customer tier playbook + test framework | Prioritises commercial outreach; provides rigorous campaign evaluation framework |
| 04 — Warehouse Optimisation | ✅ Complete | Slotting recommendations + implementation plan | $22,414 labour saving, 5.8× ROI, 125-day break-even |
| 05 — WMS Dashboard | ✅ Complete | 5-section operational dashboard + KPI dictionary | Network-wide performance visibility; early warning for SLA breaches |

---

*BRD Summary v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · 2024*
