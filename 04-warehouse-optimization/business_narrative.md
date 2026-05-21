# Warehouse Optimization — Business Narrative
**Author:** Vinyl Kiran Anipe  
**Role:** Business Analyst / Data Analyst  
**Date:** June 2024  
**Status:** Analysis complete  
**Project:** DHL Supply Chain — Warehouse Slotting & Zone Optimisation

---

## Executive Summary

DHL operates three distribution warehouses (IL02, NJ01, TX03) processing 219,000 tasks
across 24 months. Despite a strong headline accuracy rate of 99.3%, an analysis of
slotting strategy reveals that **61.4% of active SKUs are incorrectly positioned relative
to their pick frequency** — high-velocity SKUs are stored in secondary locations that
require longer picker travel, while slow-moving SKUs occupy premium Pick_Face slots.

This analysis applies frequency-based slotting tiers (Hot / Warm / Cool / Cold) across
1,664 active SKUs, identifies 514 misslotted SKUs requiring remediation, and calculates
a **9.1× ROI on slotting corrections** with an 80-day break-even. A combined
optimisation programme — covering slotting, Pick_Face clearance, and adjacency review —
is estimated to save **$22,414 in labour costs over 24 months** against an
implementation cost of **$3,838**.

---

## Business Problem

### Current State

The three DHL warehouses operate without a systematic, data-driven slotting strategy.
SKU locations are determined at the time of initial receipt and rarely revisited:

1. **Static slotting:** SKUs are placed in locations based on ABC revenue classification
   (A-class near Pick_Face, C-class in Bulk storage). This classification reflects
   revenue value — not pick frequency. A high-revenue SKU that ships in large quantities
   per order but infrequently is treated the same as a high-revenue SKU that ships
   daily.

2. **Velocity blindspot:** ABC class and pick frequency are correlated but not identical.
   Of 1,664 active SKUs, 391 Hot or Warm SKUs (top 30% by pick frequency) are currently
   stored in Reserve or Bulk locations — requiring pickers to travel further for the most
   frequently requested items.

3. **Pick_Face congestion:** 123 Cold SKUs (bottom 40% by pick frequency) occupy
   premium Pick_Face slots that could be used by high-velocity items. These slots
   represent real estate that is actively costing pick time for the most common orders.

4. **No adjacency logic:** SKU placement does not account for which items are
   frequently picked together in the same order wave. Items that commonly co-occur
   in the same pick session are not intentionally co-located.

### Impact of Current State

- **Pick_Face zone carries the highest absolute error count in the network:** 715 errors
  over 24 months, the largest of any zone. As the highest-traffic zone, even a small
  accuracy gap at this location type has outsized operational impact.
- **Misslotted Hot/Warm SKUs add travel time to 26,667 pick events** (24-month total),
  each requiring a trip to Reserve or Bulk rather than Pick_Face.
- **53,334 unnecessary picker-minutes are incurred** over 24 months from Hot/Warm SKUs
  being located in the wrong zone — equivalent to 888.9 operator-hours.

### Business Question

*Which SKUs should be repositioned in the warehouse to minimise picker travel time,
and what is the measurable financial return on executing those moves?*

---

## Stakeholders

| Stakeholder | Role | Primary Interest |
|---|---|---|
| Warehouse Operations Manager | Decision owner | Operational efficiency, accuracy, pick rate |
| Warehouse Operators / Pickers | Execution | Practical slot assignments, clear labelling |
| Finance | Approver | ROI justification, payback period |
| WMS / IT Team | Implementation | Slot master update, label reprint, system sync |

---

## Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Pick_Face Mismatch Rate | % of Hot/Warm SKUs correctly slotted in Pick_Face | Reduce from 38.6% to <10% in Phase 1 |
| Labour Hours Saved | Pick hours saved from correctly slotted Hot SKUs | ≥ 889 hrs over 24 months |
| Break-Even Period | Days until implementation cost is recovered | ≤ 80 days |
| Pick_Face Accuracy | Error rate in Pick_Face zone | Maintain ≥ 99.3% through transition |
| Cold SKU Clearance | Cold SKUs removed from Pick_Face | ≥ 100 of 123 in Phase 2 |

---

## Data Sources

| Table | Source | Key Fields | Period |
|---|---|---|---|
| `wms_tasks.csv` | DHL WMS — task records | Task_ID, Task_Type, SKU_ID, Warehouse_ID, Operator_ID, Shift, Duration_Min, Quantity, Accuracy_Flag, Error_Code | Jan 2022 – Dec 2023 |
| `warehouse_locations.csv` | DHL WMS — location master | Location_ID, Warehouse_ID, Zone, Aisle, Bay, Level, Capacity_Units, Storage_Type | Static |
| `sku_master.csv` | DHL ERP — SKU master | SKU_ID, Category, ABC_Class, Weight_KG, Storage_Type, Primary_Warehouse | Static |
| `daily_demand.csv` | DHL ERP — demand history | SKU_ID, Date, Demand_Units, Warehouse_ID | Jan 2022 – Dec 2023 |

**Records:** 219,000 WMS tasks · 1,664 active SKUs · 2,640 warehouse slots · 3 warehouses

---

## Methodology

### Slotting Tier Assignment

Pick frequency was calculated as the total number of Pick task events per SKU across
the 24-month period, aggregated at network level. SKUs were then ranked by pick frequency
and assigned to one of four slotting tiers using fixed percentile cutoffs:

| Tier | Percentile | Pick Count Range | Recommended Zone |
|---|---|---|---|
| Hot | Top 10% | 69–86 picks | Pick_Face |
| Warm | 10–30% | 63–69 picks | Reserve |
| Cool | 30–60% | 57–63 picks | Reserve |
| Cold | Bottom 40% | 38–57 picks | Bulk |

### Zone Proxy

Since WMS task records do not include a direct zone or location field, zone assignment
is inferred from Task_Type using the following mapping:

| Task_Type | Zone Proxy |
|---|---|
| Pick | Pick_Face |
| Putaway | Reserve |
| Replenishment | Reserve → Pick_Face |
| Transfer | Bulk |
| Receiving | Receiving |
| Cycle Count | All Zones |

### Current Zone Proxy

The current zone for each SKU is estimated from its ABC classification, following the
DHL standard assignment convention: A-class → Pick_Face, B-class → Reserve, C-class → Bulk.

### Mismatch Detection

A SKU is flagged as misslotted if its recommended zone (frequency-based) differs from
its current zone (ABC-based). Mismatches fall into two types: Hot/Warm SKUs in Reserve
or Bulk, and Cold SKUs occupying Pick_Face.

### ROI Calculation

Time savings are estimated at 2 minutes per pick for Hot/Warm SKUs correctly moved to
Pick_Face (reduced travel distance). Labour value is calculated at $25/hr blended rate.
One-time relocation cost is 15 minutes per SKU. ROI = labour saving ÷ relocation cost
over the same 24-month observation window.

---

## Key Findings

### 1. The ABC→Zone Proxy Produces a 61.4% Mismatch Rate

Frequency-based slotting analysis found 1,022 of 1,664 active SKUs (61.4%) misslotted
relative to their pick velocity. The dominant issue is that ABC class — which measures
revenue contribution — does not reliably predict pick frequency. A C-class SKU that ships
at high frequency should be in Pick_Face; an A-class SKU that ships rarely should not be.

### 2. 391 Hot/Warm SKUs Are in Secondary Storage

The most operationally costly finding is that 391 SKUs in the top 30% by pick frequency
are stored in Reserve or Bulk locations. These SKUs collectively account for 26,667 pick
events over 24 months. Each of these picks requires the operator to travel to a secondary
storage zone rather than the closest Pick_Face slot — an estimated 2 minutes of excess
travel per pick, totalling 888.9 unnecessary operator-hours over the analysis period.

### 3. Pick_Face Carries the Highest Absolute Error Volume

The Pick_Face zone records 715 errors across 24 months — the highest absolute error count
of any zone. While the error rate (0.73%) is not the worst (Cycle Count zone has a higher
rate at 1.51%), the volume of activity in Pick_Face means that even marginal process
improvements here have network-wide impact. WRONG_QTY is the leading error type in
Pick_Face (149 errors), followed by MISSING_LABEL (148) and WRONG_LOCATION (143).

### 4. Cold SKUs Occupy 123 Pick_Face Slots

123 Cold SKUs (bottom 40% by pick frequency) occupy Pick_Face slots that should be
allocated to higher-velocity items. These are not just wasted slots — they actively
push Hot/Warm SKUs into secondary storage, creating a double inefficiency: slow items
are easy to reach, fast items are hard to reach.

### 5. Adjacency Co-occurrence Is Uniformly Low

SKU co-occurrence analysis across 6,566 pick sessions found 625,473 unique pairs, with
a maximum co-occurrence of 7 sessions for any given pair. No SKU pair occurs together
with sufficient frequency to justify a dedicated adjacency relocation programme at this
time. The product catalogue (1,664 SKUs, 8 categories) is too diverse for strong
co-occurrence patterns to emerge within individual pick sessions. The adjacency
programme (ROI: 0.3×, break-even: 2,380 days) is not financially justified based
on current data.

### 6. Operational Performance Is Consistent Across Warehouses and Shifts

All three warehouses operate at near-identical accuracy rates (IL02: 99.30%,
NJ01: 99.26%, TX03: 99.25%) and task volumes (~73,000 tasks each). The Night shift
records slightly lower accuracy in Pick_Face (99.22% vs 99.30% Morning) but the gap
is small and consistent across all warehouses. Operator productivity is highest in
the Morning shift (22.7 tasks/operator) and lowest on Night (7.7 tasks/operator),
consistent with lower staffing in overnight operations.

---

## Recommendations

### Immediate (Weeks 1–2)

1. **Relocate the top 167 Hot SKUs to Pick_Face.** These are the highest-frequency SKUs
   (69–86 picks over 24 months) and the relocation delivers the fastest break-even
   (~32–36 days per SKU). Prioritise by pick count descending — the top 20 candidates
   are documented in `ops_recommendation.md` and `outputs/slotting_recommendations.csv`.

2. **Freeze new Cold SKU slotting into Pick_Face.** Before relocating existing Cold SKUs,
   prevent the problem from growing. Any new SKU with an initial ABC C-class and no
   prior pick history should be assigned to Reserve or Bulk on receipt.

### Medium Term (Weeks 3–8)

3. **Clear 123 Cold SKUs from Pick_Face.** Once Hot SKU relocation is complete, free
   the occupied slots by moving Cold SKUs to Bulk. This unlocks capacity for remaining
   Warm SKU re-slots and reduces the mismatch rate further. Implementation cost:
   $769 (123 SKUs × 15 min × $25/hr).

4. **Complete Warm SKU re-slot (224 SKUs).** Move remaining Warm SKUs (next 20% by
   pick frequency) from Reserve/Bulk to Reserve (or Pick_Face where capacity allows).

5. **Address WRONG_QTY errors in Pick_Face.** The leading error type in the highest-traffic
   zone is quantity miscount. Investigate whether this is a pick list display issue, a
   unit-of-measure labelling problem, or an operator training gap. A 5-minute targeted
   inspection per shift in Pick_Face would cover the full aisle in one week.

### Longer Term (Month 2+)

6. **Re-run slotting analysis quarterly.** Pick frequency shifts with demand patterns.
   A quarterly rerun of `slotting_analysis.py` will identify new mismatches as the SKU
   mix evolves, preventing the current backlog from re-accumulating.

7. **Revisit adjacency analysis at 18-month mark.** If the SKU catalogue narrows or
   if DHL introduces category-focused pick waves, co-occurrence may reach actionable
   levels. The current data does not support a dedicated adjacency programme.

---

## Open Questions

1. Are there physical constraints (aisle width, weight capacity, hazmat restrictions)
   that prevent certain Hot SKUs from being assigned to specific Pick_Face slots?
2. Does the WMS allow slot master bulk updates, or does each relocation require
   individual system entry (which would increase the per-SKU relocation cost)?
3. What is the Night shift staffing model — are fewer operators the reason for lower
   throughput, or does the shift handle a different task mix?

---

## Next Steps

| Action | Owner | Timeline |
|---|---|---|
| Review top 20 re-slot list with Ops Manager | BA/DA + Ops Manager | Week 1 |
| Create relocation work orders for Hot SKUs | Ops Manager + WMS Team | Week 1–2 |
| Execute Phase 1 Hot SKU relocations (167 SKUs) | Warehouse Operators | Weeks 2–3 |
| Freeze Cold SKU → Pick_Face assignments | WMS Team | Week 2 |
| Clear Cold SKUs from Pick_Face (123 SKUs) | Warehouse Operators | Weeks 4–6 |
| Investigate WRONG_QTY errors in Pick_Face | Ops Manager | Week 3 |
| Schedule quarterly slotting rerun | BA/DA | Month 2 |

---

*Document version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 4 · 2024*
