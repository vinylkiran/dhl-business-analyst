# Lessons Learned — DHL BA/DA Portfolio
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Covers:** Projects 01–05  
**Date:** 2024 · Version 1.0

---

## Purpose

This document captures what worked, what didn't, and what should be done differently in a second iteration across the five projects. It is written for future analysts joining this team or working on similar supply chain analytics projects at DHL. It is intentionally honest — the value is in the specifics, not the generalities.

---

## 1. What Worked Well

### 1.1 DuckDB as the SQL Layer

Using DuckDB to query CSV files directly — without loading anything into a relational database — was the right call for a portfolio project of this scope. It enabled full SQL syntax (window functions, CTEs, multi-table joins) against files sitting on the local filesystem, with zero setup overhead. Query performance on 219,000-row datasets was sub-second, and the `read_csv_auto` inference handled schema detection cleanly across all four source files.

**Recommendation for future analysts:** Use DuckDB as the default SQL layer for any project where the data fits in memory and a full database setup is not warranted. The `duckdb.connect()` + `CREATE VIEW ... AS SELECT * FROM read_csv_auto(...)` pattern is a fast, clean, auditable way to set up a queryable data layer in under five lines.

### 1.2 Separating Exploration, Calculation, and Visualisation

Splitting each project into distinct script files — `sql_exploration.py` for open-ended querying, a calculation script for KPI derivation, and a separate dashboard build — prevented the "everything in one notebook" problem. Each script has a single clear purpose, can be run independently, and produces its own outputs. When the dashboard broke, the KPI calculations were unaffected.

**Recommendation:** Keep this separation on any subsequent project. Add a `validate_outputs.py` step that checks output CSVs for expected column names, row counts, and null rates — this would have caught the DuckDB schema differences (e.g., missing Zone column) at the outputs stage rather than at dashboard build time.

### 1.3 Saving Pre-Aggregated CSVs Before Dashboard Build

The most significant technical lesson was to pre-aggregate all data into small CSVs before generating the dashboard HTML. The first dashboard approach attempted to run DuckDB queries inside the Plotly/HTML generation script, which timed out repeatedly on the 219k-row WMS dataset. Pre-aggregating to dashboard-specific CSVs (dash_monthly_net.csv, dash_err_dist.csv, etc.) reduced dashboard generation from a 60+ second operation to a 3-second script.

**Recommendation:** For any dashboard built over datasets > 50k rows: always pre-aggregate first. The aggregation scripts should be deterministic and version-controlled. Dashboard HTML scripts should only consume clean, pre-aggregated CSVs — never raw source data.

### 1.4 Grounding Every Recommendation in Numbers

Every recommendation in the portfolio is accompanied by a specific number: ROI, break-even days, estimated saving, operator count, SKU count. The slotting optimisation section is the clearest example — "move these 167 SKUs, save $22,414 over 24 months, break-even in 125 days" is a decision a manager can act on. "Your slotting is suboptimal" is not.

**Recommendation:** Before writing any recommendation section, ask: "Can I put a number on this?" If the answer is no, the analysis is not complete.

### 1.5 The Formal KPI Dictionary

Formalising every metric's definition — including the formula, the data source column, the threshold, and the known limitations — prevented ambiguity across projects. When "accuracy" was referenced in both Project 04 (slotting) and Project 05 (WMS dashboard), having a dictionary entry ensured both projects used the same definition and the same data source column.

**Recommendation:** Build the KPI dictionary entry at the same time as the first use of the metric, not retrospectively. Writing the limitation field forces the analyst to think carefully about what the metric does and does not capture.

---

## 2. Data Quality Issues Encountered and How They Were Handled

### 2.1 Missing Zone Column in WMS Data

The `wms_tasks.csv` dataset does not contain a `Zone` column — tasks are identified by warehouse, shift, and operator, but not by physical storage zone. When the WMS dashboard was designed to include an "error rate by zone" chart, the query failed with a BinderException.

**How it was handled:** Product category (`Category`) was used as a proxy for zone, since SKU categories are broadly co-located in consistent zones (Pharmaceutical in controlled storage, Automotive in heavy-goods racking, etc.). This was documented in the chart title as "Errors by Product Category" and flagged as a proxy in the dashboard user guide.

**What to do differently:** Before designing any dashboard section that requires a specific field, confirm that field exists in the source data by running `DESCRIBE [view]` at the start of the exploration script. Add a data availability checklist to the project setup step.

### 2.2 Git Lock Files on Mounted Filesystem

When attempting to commit Project 5 from the sandbox, the `.git/index.lock` and `.git/HEAD.lock` files on the mounted filesystem could not be deleted — the mount enforced file permissions that prevented removal even by the file owner. This blocked all standard `git add / commit` operations.

**How it was handled:** Cloned the remote repository to a fresh `/tmp` directory (not the mounted filesystem), copied the new project files in, committed and pushed from the clean clone. This worked cleanly.

**What to do differently:** For any project hosted on a mounted filesystem, always commit from a `/tmp` clone rather than the mount path directly. The clone-copy-commit pattern should be the standard workflow.

### 2.3 Inconsistent Date Column Naming

The `daily_demand.csv` file uses a `Date` column; other files use `Task_Date` (wms_tasks.csv) and `Snapshot_Date` (inventory_snapshot.csv). This inconsistency caused a BinderException when the WMS stockout correlation query used `d.Demand_Date` (assumed field name) instead of `d.Date`.

**How it was handled:** Fixed by inspecting the actual column names with `DESCRIBE` before writing the join query.

**What to do differently:** Add a standard schema documentation step at the start of every project that prints all column names for all source files. This takes two minutes and prevents hours of debugging.

### 2.4 Dashboard Timeout on Large Plotly Objects

Generating Plotly HTML with embedded data from a 219k-row dataset timed out the sandbox shell repeatedly. The root cause was that Plotly's `to_html()` method embeds full datasets in the HTML as JSON, and at 219k rows this produces HTML files > 50MB.

**How it was handled:** Switched from Plotly to Chart.js for the WMS dashboard, which accepts pre-aggregated JSON arrays and generates compact, fast-loading HTML (53KB).

**What to do differently:** For operational dashboards over large datasets, always use Chart.js or a similar lightweight library that consumes pre-aggregated data. Reserve Plotly for analytical/exploratory dashboards where interactive drill-down into raw data is genuinely needed.

### 2.5 ABC Class Counts Differ Between Projects

In Project 01, the ABC classification was applied to 2,000 SKUs from sku_master.csv and returned A=164, B=213, C=1,287 (total 1,664 active SKUs). In the demand forecasting project (Project 02), the same data showed A=411, B=610, C=979. This discrepancy arose because Project 01 used a pre-filtered segmentation dataset (excluding zero-revenue SKUs), while Project 02 used the full demand summary.

**How it was handled:** Both are correct in their own context; the discrepancy was documented in the business narrative for each project.

**What to do differently:** Define a single "active SKU" definition at the portfolio level (e.g., "SKU with ≥1 demand transaction in the last 12 months") and apply it consistently across all projects. This should live in a shared `data_dictionary.md` file in the `shared/` directory.

---

## 3. Stakeholder Communication Approaches That Worked

### 3.1 One-Page Ops Recommendation Before the Full Narrative

In Project 04 (Warehouse Optimisation), writing `ops_recommendation.md` — a one-page, plain-English document with a top-10 priority list — before the full business narrative was the right sequencing for the Operations Manager audience. Busy operations stakeholders read the top-10 list first and only go to the full narrative if they want the methodology. Reversing this order (narrative first) would have buried the actionable content.

### 3.2 Traffic-Light Status in Every Summary Table

Every KPI table across the portfolio uses green/amber/red status. This is simple and works: stakeholders scan for red cells, not for column values. The traffic-light system also forces the analyst to define thresholds explicitly — you cannot colour a cell without first deciding what "good" means.

### 3.3 The Implementation Plan as a Handoff Document

The `implementation_plan.md` in Project 04 was written to be handed directly to the Operations Manager, WMS team, and floor supervisors without any further interpretation. It names specific roles, specific steps, and specific success criteria. Writing it this way forced precision — vague instructions are unusable in an operational setting.

### 3.4 Documenting What the A/B Test Did Not Show

In Project 03, the A/B test result was not statistically significant. Documenting this honestly — including the p-value, the confidence interval, and the recommendation to extend the test duration — was more valuable than glossing over a null result. Stakeholders trust analysts who report inconclusive results clearly; they distrust analysts who find significance everywhere.

---

## 4. What Would Be Done Differently in a Second Iteration

### 4.1 Build a Shared Data Layer First

All five projects read from the same four source CSV files but each project set up its own DuckDB connection and view definitions independently. A better approach would be to build a shared `data_layer.py` module that creates all views once and is imported by every script. This would eliminate the repeated boilerplate connection code and ensure that any schema change (e.g., adding a Zone column to wms_tasks.csv) only needs to be updated in one place.

### 4.2 Define a Standard Project Template

Each project independently developed its folder structure, script naming convention, and output naming convention. A standard template at the start of the portfolio would have produced more consistent, browsable outputs. The template should specify: required folder names, required script names, required output files (KPI CSV, narrative MD, dashboard HTML), and the standard boilerplate for connecting to shared data.

### 4.3 Add a Validation Script to Every Project

Every project should include a `validate.py` that runs after all analysis scripts and confirms: all expected output files exist, output CSVs have expected column names and non-zero row counts, key KPI values are within plausible ranges (e.g., accuracy % is between 0 and 100), and no outputs contain more than 5% null values in non-nullable columns. This would have caught the missing Zone column issue and the ABC count discrepancy at the validation stage.

### 4.4 Version-Control the Source Data

The four source CSV files were placed in a shared directory but never version-controlled. If the data generation script (`generate_dhl_data.py`) is re-run with a different random seed, all downstream analysis changes. Version-controlling the CSVs alongside the analysis code would ensure full reproducibility.

### 4.5 Build the KPI Dictionary First, Not Last

The `master_kpi_dictionary.md` was written in Project 06 as a consolidation exercise. It should have been written in Project 01 and maintained throughout. Writing it retrospectively surfaced several minor inconsistencies (different threshold values between projects, different column references for the same underlying metric) that would have been caught earlier if the dictionary had been live from the start.

### 4.6 Include a Post-Implementation Measurement Plan

Every project delivers recommendations but none explicitly specifies how to measure whether the recommendation worked after implementation. Project 04, for example, should include a "Re-run this script 6 months after implementation and compare PPH and slotting mismatch rate against the pre-implementation baseline." Adding a measurement plan to each project deliverable turns one-time analysis into a continuous improvement cycle.

---

## 5. Recommendations for Future Analysts

**On methodology:**
- Always establish a clear business question before writing any SQL. "What does the business need to decide?" is more useful than "what can I find in this data?"
- ABC/XYZ segmentation is a strong starting point for any inventory analytics engagement. It is explainable, actionable, and produces immediate stakeholder value.
- For A/B test design, always calculate the required sample size before running the test. An underpowered test that returns a null result is ambiguous — you cannot tell whether the intervention had no effect or whether the test simply lacked the power to detect it.

**On data:**
- Inspect column names, data types, and null rates before writing analysis. Ten minutes of exploration prevents hours of debugging.
- Always document the date range of the analysis clearly. Many KPIs change dramatically when the window shifts from 12 to 24 months.
- When a field you expected does not exist (e.g., Zone column), use the closest available proxy and document the substitution clearly. Never silently drop the analysis.

**On delivery:**
- Write the one-page executive summary first, not last. It forces clarity about what the analysis actually found.
- Every recommendation needs: a number, an owner, a timeline, and a success criterion. Without all four, it will not be acted on.
- The dashboard is not the deliverable. The decision it enables is the deliverable. Keep this hierarchy in mind when prioritising what goes on the dashboard.

**On tooling:**
- DuckDB + Python + Chart.js is a lightweight, dependency-minimal stack that works reliably in constrained environments. Use it.
- Avoid Plotly for dashboards over large datasets unless you pre-aggregate first.
- Git commit from clean `/tmp` directories when working on mounted filesystems.

---

*Lessons Learned v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · 2024*
