# DHL Supply Chain — Business Analyst Portfolio

**Prepared by:** Vinyl Kiran Anipe | Business Analyst / Data Analyst  
**Status:** ✅ Complete — 6 projects, 5 dashboards, 1 executive deck  
**Stack:** Python · DuckDB · Chart.js · pandas · Plotly · Markdown

---

## Overview

This portfolio demonstrates end-to-end business analyst work across a simulated DHL supply chain operation covering three warehouses, 2,000 SKUs, 398 customers, and 219,000 WMS tasks spanning 24 months of operational data. Each project follows the full BA lifecycle: problem framing, stakeholder alignment, data exploration, KPI definition, quantified recommendations, and a stakeholder-ready deliverable.

The work is intentionally scoped to what a BA/DA owns: business requirements, SQL-based exploration, KPI design, dashboard build, and narrative communication. Statistical modelling, ML pipeline engineering, and automated data refresh infrastructure are handled in separate Data Science and Data Engineering portfolios. Every recommendation in this portfolio is grounded in a specific number — ROI, break-even period, labour saving, or revenue impact — because analysis without a number is not a business case.

---

## Projects

| # | Project | One-Line Description | Status | Key Output |
|---|---|---|---|---|
| 01 | [SKU Segmentation](./01-sku-segmentation/) | ABC/XYZ classification of 2,000 SKUs with differentiated safety stock and reorder point rules | ✅ Complete | `sku_segments.csv` · `sku_segmentation_dashboard.html` |
| 02 | [Demand Forecasting](./02-demand-forecasting/) | 14-day MA forecast accuracy baseline by segment + DE pipeline specification | ✅ Complete | `demand_summary.csv` · `forecast_dashboard.html` · `pipeline_requirements.md` |
| 03 | [RFM & A/B Test](./03-rfm-segmentation/) | RFM customer segmentation, 7-tier playbook, and statistically designed retention campaign A/B test | ✅ Complete | `customer_rfm.csv` · `rfm_dashboard.html` · `test_design_doc.md` |
| 04 | [Warehouse Optimisation](./04-warehouse-optimisation/) | Slotting mismatch quantification, labour-saving ROI, phased implementation plan | ✅ Complete | `slotting_recommendations.csv` · `warehouse_dashboard.html` · `implementation_plan.md` |
| 05 | [WMS Dashboard](./05-wms-dashboard/) | Multi-site WMS operational dashboard covering 219k tasks, operator scorecards, and data quality alerts | ✅ Complete | `wms_dashboard.html` · `kpi_dictionary.md` · `operator_scorecard.csv` |
| 06 | [BA Artifacts](./06-ba-artifacts/) | Cross-portfolio KPI dictionary, consolidated BRD library, lessons learned, and 10-slide executive deck | ✅ Complete | `master_kpi_dictionary.md` · `brd_summary.md` · `dhl_ba_portfolio_deck.html` |

---

## Portfolio Impact Summary

| Metric | Value |
|---|---|
| SKUs analysed | 2,000 across 3 warehouses |
| Revenue modelled (24 months) | ~$2.3B outbound orders |
| WMS tasks processed | 219,000 |
| Customers segmented | 398 |
| Estimated annual value of recommendations | ~$332K |
| Warehouse slotting ROI | 5.8× over 24 months |
| Slotting break-even | 125 days |
| Projects completed | 6 of 6 |

---

## Tech Stack

| Tool | Role |
|---|---|
| **DuckDB** | SQL layer over CSV files — window functions, CTEs, multi-table joins, zero-setup |
| **Python 3** | All analysis scripts — pandas, numpy, scipy |
| **Chart.js** | Production dashboards (lightweight, pre-aggregated data, no timeout risk) |
| **Plotly / matplotlib / seaborn** | Analytical figures and exploratory charts |
| **pandas** | Data wrangling and aggregation |
| **Markdown** | All narrative documents — business narratives, KPI dictionaries, user guides |

The standard script pattern across every project: `sql_exploration.py` (open-ended querying) → calculation script (KPI derivation) → `build_dashboard.py` (HTML generation from pre-aggregated CSVs). Dashboard HTML scripts never consume raw source data directly — all aggregation happens upstream.

---

## Synthetic Dataset

All data in this portfolio is synthetically generated to mirror real DHL supply chain characteristics. The four source files are produced by `generate_dhl_data.py` and placed in `shared/data/`:

| File | Rows | Description |
|---|---|---|
| `sku_master.csv` | 2,000 | SKU catalogue: unit cost, price, lead time, category, ABC/XYZ class |
| `daily_demand.csv` | ~730k | 24 months daily demand, revenue, stockout flags across all SKUs |
| `inventory_snapshot.csv` | ~60k | Daily on-hand and available quantity snapshots by SKU and warehouse |
| `outbound_orders.csv` | ~50k | 24 months of customer orders: revenue, OTIF flags, channel, customer type |
| `wms_tasks.csv` | 219,000 | Picks, putaways, and cycle counts across 3 sites, 3 shifts, 180 operators |
| `customers.csv` | 398 | Customer metadata: region, type, annual revenue band |

The distributions, error rates, ABC classifications, and seasonal patterns are calibrated to be representative of a mid-scale 3PL operation. No real DHL data is used.

---

## Methodology Note

This is a **BA/DA portfolio**, not a data science or data engineering portfolio. The emphasis is on:

- **Business framing** — defining the problem, the stakeholder, and the decision before touching data
- **Requirements documentation** — BRDs, KPI dictionaries, success criteria, data availability checks
- **SQL-based exploration** — understanding the data structure, distributions, and quality issues before analysis
- **Quantified recommendations** — every finding is tied to a number: ROI, break-even, saving, rate, or risk value
- **Stakeholder communication** — one-page ops summaries, traffic-light dashboards, weekly report templates, user guides

Statistical modelling (forecasting, ML classification, time-series decomposition) and pipeline engineering (Airflow, dbt, automated refresh, cloud infrastructure) are deliberately kept lightweight or out of scope. Those capabilities are demonstrated in separate Data Science and Data Engineering portfolio projects.

---

## Repository Structure

```
dhl-business-analyst/
├── shared/
│   └── data/                    # Source CSVs (synthetic)
├── 01-sku-segmentation/         # ABC/XYZ segmentation + safety stock
├── 02-demand-forecasting/       # Forecast baseline + pipeline spec
├── 03-rfm-segmentation/         # RFM tiers + A/B test design
├── 04-warehouse-optimisation/   # Slotting optimisation + ROI
├── 05-wms-dashboard/            # Multi-site WMS operational dashboard
└── 06-ba-artifacts/
    ├── kpi-dictionary/          # Master KPI dictionary (cross-project)
    ├── brd-library/             # BRD summary + lessons learned
    └── executive-deck/          # 10-slide HTML executive presentation
```

---

*DHL BA/DA Portfolio · Vinyl Kiran Anipe · 2024 · Synthetic data · No real DHL data used*
