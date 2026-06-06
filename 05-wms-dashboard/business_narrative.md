# WMS Operational Dashboard — Business Narrative
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**Project:** 05 — WMS Operational Dashboard  
**Date:** 2024  
**Version:** 1.0

---

## Executive Summary

DHL operates three warehouse sites — DHL-WH-IL02 (Illinois), DHL-WH-NJ01 (New Jersey), and DHL-WH-TX03 (Texas) — collectively processing approximately 219,000 warehouse management system (WMS) tasks over a 24-month period. Across this network, 180 operators execute picks, putaways, and cycle counts daily across three shifts.

Prior to this project, each site manager tracked operational KPIs independently using local Excel files. This fragmented approach made network-level performance invisible to senior leadership, prevented cross-site benchmarking, and meant that emerging performance issues could go undetected until they became SLA breaches.

This project delivers a single-source-of-truth WMS operational dashboard that standardises KPI definitions across all three sites, enables daily performance monitoring, and surfaces data quality issues before they escalate into operational failures.

**Key findings at a glance:**
- Network pick accuracy is 99.27% — above the 99.0% SLA threshold across all three warehouses
- Putaway compliance is 99.70% — above the 99.5% threshold at network level
- Cycle count accuracy (98.49%) is the weakest KPI; IL02 and NJ01 are AMBER, just below the 98.5% threshold
- 4 operators qualify as high performers (≥99.8% accuracy); no operators are below the 98.5% coaching threshold — a strong baseline for the network
- 20 SKUs have persistent error rates above 2% across 3+ consecutive months, indicating systemic labelling or system configuration issues rather than isolated operator errors
- 3 problem zones (product categories) show above-average error rates, clustered in Fashion & Apparel and FMCG categories

---

## Problem Statement

Warehouse managers across NJ01, IL02, and TX03 have no consistent real-time view of operational performance. The specific gaps identified through stakeholder interviews and data review are:

**1. No standardised KPI definitions.** Each site defines "accuracy" differently. One site counts a task as accurate if the SKU is correct but ignores quantity errors; another flags any deviation. This inconsistency makes network-level reporting unreliable and undermines leadership confidence in the numbers.

**2. No cross-site benchmarking.** Without a shared data model, it is impossible to determine whether IL02's performance is genuinely stronger than TX03's or whether the difference reflects measurement differences. Operators at high-performing sites cannot be identified as sources of best practice.

**3. No early warning system for SLA risk.** By the time a performance issue appears in a weekly report, it may already have triggered client SLA penalties. The existing reporting cadence (weekly or monthly Excel summaries) is too slow to enable intervention before a breach.

**4. Data quality issues are invisible.** SKUs with persistently high error rates, locations with above-average error frequencies, and operators with shift-specific performance spikes exist in the WMS data — but without a structured data quality layer, these patterns are never surfaced. Problems that could be resolved with a labelling fix or targeted training persist indefinitely.

**5. Inventory record accuracy is not monitored in relation to pick performance.** A warehouse can maintain high pick accuracy while simultaneously suffering from poor inventory record accuracy (IRA), meaning the right item is picked from the right location but the system's on-hand balance is wrong — creating downstream stockout risk that is only visible when demand planning data is cross-referenced.

---

## Stakeholder Table

| Stakeholder | Role | Primary Interest in Dashboard | Key Questions |
|---|---|---|---|
| VP Operations | Senior leadership | Network-level KPI summary, SLA compliance, trend direction | Are we meeting SLA targets? Which site needs intervention? |
| Site Managers (IL02, NJ01, TX03) | Site accountability | Site-specific KPIs, shift comparisons, operator performance | How is my site performing vs the network? Which shift needs attention? |
| Floor Supervisors | Daily operations | Shift-level accuracy, real-time operator scorecard, error patterns | Which operators need coaching today? Where are errors clustering? |
| Quality / Compliance Team | Error investigation | Error code distribution, high-error SKUs, data quality flags | What are the root causes of our most frequent errors? Which SKUs need a process review? |
| IT / WMS Team | System administration | Data quality flags, IRA trends, system error patterns | Are there WMS configuration issues driving specific error codes? |
| Demand Planning | Supply chain | Stockout correlation with pick accuracy, IRA trend | How does pick performance affect stockout rates and fulfilment? |

---

## KPI Definitions and Business Rationale

### Pick Accuracy %
**Formula:** `(Picks with Accuracy_Flag = 1) / (Total Picks) × 100`  
**Threshold:** ≥99.0% = GREEN; 98.5–99.0% = AMBER; <98.5% = RED  
**Rationale:** Pick accuracy directly determines whether the right product reaches the customer. At a network volume of ~110,000 picks over 24 months, a 1% error rate means ~1,100 mis-picks — each requiring a returns process, potential customer complaint, and reputational cost. The 99.0% threshold aligns with typical 3PL SLA commitments.

### Putaway Compliance %
**Formula:** `(Putaways with Accuracy_Flag = 1) / (Total Putaways) × 100`  
**Threshold:** ≥99.5% = GREEN; 99.0–99.5% = AMBER; <99.0% = RED  
**Rationale:** Putaway errors create downstream pick errors — if an item is placed in the wrong location, the next picker will either find nothing or pick the wrong item, triggering a cascade of WRONG_LOCATION errors. The threshold is set higher than pick accuracy because putaway errors have a multiplier effect on downstream quality.

### Cycle Count Accuracy %
**Formula:** `(Cycle Counts with Accuracy_Flag = 1) / (Total Cycle Counts) × 100`  
**Threshold:** ≥98.5% = GREEN; 98.0–98.5% = AMBER; <98.0% = RED  
**Rationale:** Cycle counting is the mechanism by which inventory record accuracy is maintained. A lower threshold than pick/putaway reflects the inherently more complex counting process, but sustained accuracy below 98.5% indicates that the inventory record is drifting from physical reality — creating stockout risk and demand planning distortion.

### Overall Task Accuracy %
**Formula:** `(All Tasks with Accuracy_Flag = 1) / (Total Tasks) × 100`  
**Threshold:** ≥99.0% = GREEN; 98.5–99.0% = AMBER; <98.5% = RED  
**Rationale:** A composite KPI that gives leadership a single headline number for each site. Useful for executive reporting and site-level SLA tracking, but should always be read alongside task-type-specific KPIs to understand the composition of any variance.

### Picks per Labour Hour
**Formula:** `Total Picks / (Total Pick Duration in Minutes / 60)`  
**Rationale:** Labour efficiency metric that complements accuracy. A site can achieve high accuracy by operating slowly — PPH ensures that efficiency and accuracy are monitored together. Network average is approximately 8.0 picks per hour; significant deviation in either direction warrants investigation.

### Inventory Record Accuracy %
**Formula:** `Available Quantity / On-Hand Quantity × 100` (averaged across the inventory snapshot)  
**Threshold:** ≥85% = GREEN; 80–85% = AMBER; <80% = RED  
**Rationale:** IRA measures the gap between what the WMS believes is available and what is physically on-hand. A consistent gap of ~20% across all categories indicates either systematic reservation over-counting, damage write-off lag, or receiving discrepancies. This metric links warehouse operations to supply chain health.

---

## Key Findings

### Network Performance
The network is operating above SLA for pick accuracy (99.27%) and putaway compliance (99.70%). Overall task accuracy of 99.35% represents a strong baseline for a three-site operation of this scale.

The primary concern is **cycle count accuracy**, which sits at 98.49% network-wide — marginally above the 98.5% GREEN threshold for the network but below threshold at IL02 (98.36%) and NJ01 (98.49%). This is not a crisis, but it is a leading indicator: if cycle count quality deteriorates, inventory record accuracy will follow, and stockout rates will increase within 60–90 days.

### Shift Performance
The shift heatmap reveals that all warehouse-shift combinations are meeting pick accuracy thresholds. However, a consistent pattern emerges: **night shift (22:00–06:00) performs differently across sites**. At IL02, night shift has lower pick accuracy (99.18%) than morning or afternoon, while at TX03, night shift is the strongest performing shift (99.28%). This asymmetry deserves investigation — it may reflect differences in night shift staffing, supervision quality, or the mix of tasks assigned during that period.

### Operator Performance
With all 180 operators above the 98.5% coaching threshold, the network has no immediate coaching cases. Four operators have achieved the 99.8%+ high performer designation — OP-0015 (NJ01), OP-0029 (TX03), OP-0043 (IL02), and OP-0012 (IL02). Notably, three of the four high performers show a "Declining" accuracy trend in the second half of the 24-month period. This may reflect regression to the mean, increased task volume, or reduced supervision of operators assumed to be self-sufficient.

**Recommendation:** High performers should be reviewed quarterly even when above threshold, as early decline signals are easier to address than established underperformance.

### Error Analysis
The five error codes (WRONG_LOCATION, WRONG_SKU, WRONG_QTY, MISSING_LABEL, DAMAGED) are distributed relatively evenly across the network, with no single error type dominating. This even distribution is operationally significant: it suggests that errors are not driven by a single systemic cause but by a combination of factors including operator attention, label quality, and process adherence.

**WRONG_LOCATION** is the most common error at TX03 (103 instances). Given that TX03 is also the site with the most recent slotting changes (from Project 4), this may reflect a transition period where WMS slot master updates and physical reality have not yet fully synchronised.

**20 SKUs** have been flagged as having persistently high error rates across 3+ consecutive months. These are not randomly distributed — Fashion & Apparel, FMCG, and Healthcare SKUs account for the majority of flagged items. This category clustering suggests product characteristics (similar packaging, small labelling, case pack confusion) rather than operator error as the primary driver.

### Inventory Health
The inventory record shows a consistent ~20% gap between on-hand and available quantities across all categories and sites. This level of gap is not unusual in a 3PL environment with active reservations and damage holds, but it warrants monitoring. The correlation analysis between pick accuracy and stockout rates shows no strong directional relationship at the monthly level — suggesting that the current accuracy levels, while not perfect, are not the primary driver of stockouts. Stockout risk is more likely driven by demand forecasting and replenishment lead times than by pick errors at current accuracy levels.

---

## Recommendations

### Immediate (0–30 days)
1. **Investigate cycle count accuracy at IL02 and NJ01.** Schedule a focused one-week observation to determine whether the sub-threshold performance is driven by specific operators, specific SKU categories, or counting process ambiguity (e.g., unclear unit of measure on the count sheet).

2. **Review high-error SKU list with the quality team.** The 20 flagged SKUs should be reviewed for labelling clarity, unit-of-measure consistency, and packaging similarity to adjacent SKUs. A targeted labelling review may resolve multiple error types simultaneously.

3. **Investigate WRONG_LOCATION spike at TX03.** Cross-reference against the slotting change log from the Project 4 implementation. If errors are concentrated in recently re-slotted locations, this is a transition issue that will self-resolve; if they are in stable locations, it indicates a more persistent process problem.

### Short-term (30–90 days)
4. **Standardise cycle counting process documentation** across all three sites to a single approved procedure. Differences in how cycle counts are conducted (partial vs. full bin count, handling of partially picked bins) may explain inter-site accuracy variance.

5. **Create a quarterly operator performance review cadence** for high performers. All four high performers show declining trends; structured quarterly feedback will catch early deterioration before it becomes a coaching case.

6. **Monitor the IRA gap.** If the ~20% on-hand/available gap widens beyond 25% at any site, initiate an investigation into the source — damage write-off backlog, receiving discrepancies, or reservation logic errors in the WMS.

### Strategic (90+ days)
7. **Build a daily automated refresh of this dashboard** from the WMS extract. At present the analysis runs on a static 24-month dataset; connecting to a live WMS extract will enable the early warning function the dashboard is designed to provide.

8. **Extend operator analysis to include shift-level performance.** The current scorecard shows lifetime accuracy but does not flag operators who perform consistently on one shift and poorly on another — a pattern that is often the early signal of fatigue, schedule mismatch, or insufficient shift-specific supervision.

---

*Business Narrative v1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 5 · 2024*
