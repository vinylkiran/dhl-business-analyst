# WMS Dashboard — User Guide for Warehouse Managers
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Project:** 05 — WMS Operational Dashboard  
**Date:** 2024  
**Version:** 1.0

---

## How to Open the Dashboard

Open `dashboard/wms_dashboard.html` in any modern web browser (Chrome, Edge, Firefox). The dashboard loads all data from pre-built chart files — no internet connection is required once the file is open, except for loading the Chart.js library (if offline, contact the BA/DA team for an offline version).

Use the navigation bar at the top to jump between the five sections. The bar stays fixed as you scroll, so you can always jump to a different section without scrolling back to the top.

---

## Section 01 — Network Overview

**What you're looking at:** The four coloured KPI cards at the top give you the network-level headline at a glance. Green means you're above target. Amber means you're within 0.5 percentage points of the threshold — watch closely. Red means you're below threshold and action is required.

**The warehouse comparison table** directly below the KPI cards shows how each site is performing on each metric. Colour-coded cells use the same green/amber/red logic.

**The 24-Month KPI Trend chart** shows whether the network is stable, improving, or declining over time. Look for sustained trends rather than single-month dips — a one-month dip is usually volume or seasonality; a three-month downward trend signals a structural issue.

**The Picks per Labour Hour chart** shows efficiency by warehouse. If one site's PPH drops while accuracy holds, it may indicate increased task complexity or reduced workforce. If PPH rises while accuracy drops, operators may be rushing.

**When a KPI card turns AMBER:**
- Verify which warehouse is driving the variance using the comparison table
- Review the 24-month trend to determine whether this is a new development or a continuation of an existing pattern
- Check Section 02 (Floor Operations) for the shift responsible for the variance
- Notify the relevant Site Manager and ask for a verbal update within 24 hours

**When a KPI card turns RED:**
- Escalate to the Site Manager immediately
- Open a formal performance review with a 48-hour response timeline
- Check Section 05 (Data Quality Alerts) for any flagged operators or SKUs that may be contributing
- Document the date and value in the weekly management report

---

## Section 02 — Floor Operations

**Daily Task Volume (with 7-Day Moving Average):** The grey bars show raw daily volume; the red line is the 7-day moving average. The MA smooths out weekend and holiday dips. A significant drop in task volume that is not explained by a known event (public holiday, planned maintenance) should be investigated — it may reflect a WMS outage, a staffing shortage, or a data feed issue.

**Task Type Breakdown:** Shows how tasks are split between picks, putaways, and cycle counts at each warehouse. Large shifts in the ratio (e.g., a sudden drop in cycle counts) may indicate that a cycle counting programme has been paused — which will eventually show up as deteriorating IRA.

**Shift Performance Heatmap:** The table shows pick accuracy by shift and warehouse. Darker green = stronger performance; amber/red = below target. Use this to direct your attention to the right shift-site combination before diving into operator-level data.

**Pick Accuracy Trend by Warehouse:** Shows 24-month pick accuracy for each site on a shared axis. This is your key chart for cross-site benchmarking — if one site diverges from the other two, investigate what changed at that site (staffing, slotting, process changes) during that period.

**Top 5 / Bottom 5 Operators:** These are all-time rankings based on the full 24-month dataset. Use them as a starting point, not as the final word. An operator who was in the bottom 5 two years ago but has been in the top quartile for the last six months should not be treated as an underperformer.

**When a shift turns amber or red in the heatmap:**
- Identify the specific shift-warehouse combination
- Pull the operator roster for that shift from your WMS or HR system
- Check whether the shift is consistently underperforming or had a single bad week
- Meet with the floor supervisor for that shift to understand what is happening operationally (new starters, equipment issues, high-velocity period)

**When the daily task volume drops sharply:**
- Check whether it is a known event (weekend, public holiday)
- If not explained, contact IT/WMS team to confirm data feed is intact
- If data feed is confirmed working, contact site manager to confirm operations ran as scheduled

---

## Section 03 — Error Analysis

**Error Code Distribution (Pie Chart):** Shows the network-wide split of error types. In a healthy operation you expect to see roughly even distribution — no single error type should dominate. If WRONG_LOCATION suddenly accounts for >40% of errors, it often points to a recent slotting change or label update.

**Error Trend by Code (Line Chart):** Shows monthly counts of each error type over 24 months. Look for sudden spikes (single-month events — usually resolved quickly) vs. gradual increases (systemic issues that require root cause investigation). A gradual increase in MISSING_LABEL errors, for example, points to label printer maintenance falling behind schedule.

**Top 20 SKUs by Error Frequency:** These are the products that have generated the most errors across the 24-month period. A SKU appearing here repeatedly is not an operator problem — it is a process or configuration problem. Refer these SKUs to the quality team for a physical review: check the label clarity, packaging similarity to adjacent SKUs, and whether the WMS configuration (unit of measure, pick instruction) matches the physical reality on the shelf.

**Errors by Category and Warehouse:** Shows which product categories generate the most errors. Categories with high error counts across all three warehouses point to product-level issues (labelling, packaging). Categories with high errors at only one warehouse point to site-specific issues (slotting, training, equipment).

**Monthly Error Rate vs Network Average:** Your target is to keep all three warehouse lines close to the network average and stable over time. A single warehouse persistently above the average line is generating a disproportionate share of network errors. Investigate using the shift heatmap and the data quality alerts in Section 05.

**When a SKU appears repeatedly in the Top 20:**
- Raise a data quality flag with the quality team
- Request a physical shelf audit for that SKU at each warehouse where it has errors
- Check whether the error is consistently one type (e.g., always WRONG_QTY) — this will guide the root cause investigation
- Review the WMS configuration: is the unit of measure correct? Is the pick instruction clear?

---

## Section 04 — Inventory Health

**Inventory Record Accuracy Trend:** Shows what percentage of on-hand stock is actually available for picking, month by month. A value of 80% means that 20% of on-hand stock is tied up in reservations, holds, or unresolved discrepancies. The target is ≥85%.

**On-Hand vs Available by Category:** The grey bars show average on-hand quantities; the red bars show average available quantities. The gap between them is the IRA gap. Categories with large gaps may have systematic reservation issues or a high rate of quality holds — check with the WMS team on the composition of the gap.

**Pick Accuracy vs Stockout Rate (Scatter):** Each point is one warehouse in one month. You are looking for a downward trend (higher pick accuracy = lower stockout rate). If the points are scattered randomly, it means other factors (supplier delays, forecasting errors) are dominating stockout risk at current accuracy levels. This is actually common when pick accuracy is already above 99% — the marginal improvement from 99.3% to 99.5% has less impact on stockouts than improving forecast accuracy by 5%.

**Inventory at Risk:** This chart shows the categories and warehouses where the IRA gap is greatest, weighted by inventory value. A high-value category with a 25% IRA gap represents significant capital tied up in stock that cannot be allocated to demand. Escalate to the WMS team to identify what is driving the reservation/hold balance.

**When IRA falls below 85% at a site:**
- Check whether a large quality hold was placed recently (this will cause a temporary step-down)
- Review cycle count accuracy at that site — declining cycle count accuracy is the leading indicator of IRA deterioration
- Ask the WMS team for a breakdown of the on-hand/available gap: how much is reservations, how much is quality hold, how much is unresolved discrepancy

---

## Section 05 — Data Quality Alerts

**This section is your early warning system.** It surfaces issues that are not yet visible in the headline KPIs but may become problems within 30–90 days if not addressed.

**Operators Needing Coaching:** Any operator below 98.5% accuracy lifetime accuracy is listed here. If this table is empty (as it currently is — all 180 operators are above threshold), that is a positive sign but should not lead to complacency. An operator at 98.6% who is declining is more urgent than an operator at 98.7% who is stable.

**High-Error SKUs:** SKUs that have been above a 2% error rate for three or more consecutive months. These are the most actionable data quality flags — they are specific, persistent, and correctable. Refer each to the quality team using the SKU ID and the detail description shown in the table.

**Problem Zones:** Location zones (in this dashboard, product categories are used as a zone proxy) with above-average error rates. A zone-level flag often indicates a physical layout issue, a labelling problem on a rack or bay, or a training gap for operators working in that area.

**Shift Error Spikes:** Operator-shift combinations where one shift's error rate is significantly higher than that operator's average on other shifts. This is the most targeted coaching signal in the dashboard. An operator who performs well on morning shift but has a high error rate on nights is not a poor operator — they may be struggling with the night shift environment, fatigue, or different supervision. A conversation is the right first step, not a formal coaching action.

**How to act on data quality flags:**

| Flag Type | First Action | Owner | Timeline |
|---|---|---|---|
| High-Error SKU | Physical shelf audit + WMS config check | Quality Team | 5 business days |
| Problem Zone | Walk the zone with floor supervisor, check labels and layout | Floor Supervisor | 3 business days |
| Shift Error Spike | One-to-one conversation with operator | Floor Supervisor | Within next shift |
| Coaching threshold breach | Formal coaching meeting + improvement plan | Site Manager | 2 business days |

---

## Escalation Protocol

| Situation | Escalate To | Method | Timeline |
|---|---|---|---|
| Any KPI turns RED | Site Manager + VP Operations | Email + verbal | Within 4 hours |
| Any KPI turns AMBER for 3+ consecutive days | Site Manager | Email | Same day |
| 3+ operators below coaching threshold | Site Manager + HR | Meeting | Within 2 business days |
| New high-error SKU (not previously flagged) | Quality Team | Email with SKU ID | Within 2 business days |
| IRA drops below 80% at any site | WMS Team + Demand Planning | Meeting | Within 24 hours |
| Dashboard data appears stale (dates not updated) | BA/DA + IT | Immediate | Within 1 hour |

---

## Frequently Asked Questions

**Q: The dashboard shows a different accuracy number than my local Excel report. Which one is correct?**  
A: The dashboard uses the standardised KPI definitions from the KPI Dictionary (see `kpi_dictionary.md`). Your Excel report may use a different definition — for example, some reports count partial accuracy (correct SKU, wrong quantity) as half an error rather than a full error. The dashboard counts any task with a non-null Error_Code as inaccurate. If you believe your definition is more appropriate, raise it with the BA/DA team for a formal dictionary update.

**Q: An operator is showing as "STANDARD" in the dashboard but I know they've been struggling this week. What should I do?**  
A: The dashboard rankings are based on all-time accuracy over 24 months. A recent dip will not immediately move an operator's flag. If you have current-period concerns, pull the shift-level error log from your WMS and take direct action based on that. The dashboard is a strategic view, not a replacement for day-to-day floor supervision.

**Q: The stockout chart doesn't seem to show a clear relationship between pick accuracy and stockouts. Does that mean pick accuracy doesn't matter?**  
A: Not at all. At current accuracy levels (above 99%), the marginal impact of pick accuracy on stockouts is low because other factors — forecast accuracy, supplier lead time, minimum order quantities — dominate. If pick accuracy fell to 97%, you would see a clear relationship. The chart tells you that you are currently operating in the zone where pick accuracy is not the primary driver of stockouts, which is a sign of a well-run operation, not a reason to relax standards.

**Q: How often is the dashboard data refreshed?**  
A: The current version uses a static 24-month dataset. Refresh cadence is manual — the BA/DA team can regenerate the dashboard from a new WMS extract on request. The goal for Phase 2 is to connect the dashboard to a daily automated WMS export. Contact the BA/DA team to request a refresh.

---

*Dashboard User Guide v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 5 · 2024*
