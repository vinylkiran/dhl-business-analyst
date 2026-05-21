# Warehouse Slotting — Ops Manager Recommendation
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**For:** Warehouse Operations Manager  
**Date:** June 2024  
**Version:** 1.0  
**Warehouse scope:** DHL-WH-IL02 · DHL-WH-NJ01 · DHL-WH-TX03

---

## What This Document Is

This is a practical action list for the Operations Manager. It tells you which SKUs to
move, where to move them, why they are costing you time, and in what order to work
through them.

The full analysis is in `business_narrative.md` and the complete re-slot list for all
three warehouses is in `outputs/slotting_recommendations.csv`. This document covers the
top 20 immediate priorities.

---

## The Problem in Plain English

Right now, your fastest-moving SKUs are not in your easiest-to-reach locations.

Analysis of 24 months of pick data across all three warehouses shows that **391 SKUs in
your top 30% by pick frequency are stored in Reserve or Bulk zones** — not in Pick_Face
where they belong. Every pick for these SKUs costs your operators extra travel time.

At the same time, **123 slow-moving SKUs are sitting in Pick_Face slots** that should
be used for fast-moving items.

The result: your pickers walk further than necessary on the picks that happen most
often, and the slots closest to the pick zone are taken up by items that rarely move.

---

## The Fix

Move the fast SKUs closer. Move the slow SKUs further back.

This is a standard warehouse slotting exercise. It does not require new equipment, new
systems, or new staff. It requires a planned block of relocation time with your floor
operators, coordinated with WMS slot master updates.

**Estimated cost:** $3,838 total (one-time labour for relocations)  
**Estimated saving:** $22,414 over 24 months  
**Break-even:** 125 days  
**ROI:** 5.8×

---

## Phase 1: Top 20 SKUs to Move First

These are the 20 SKUs that will deliver the fastest return. All are Hot-tier SKUs
(top 10% by pick frequency) currently stored in Reserve or Bulk. Each relocation
takes approximately 15 minutes per SKU including scan, pick, move, and WMS update.

| Priority | SKU ID | Category | Current Zone | Move To | Picks (24 mo) | Labour Saved | Break-Even |
|---|---|---|---|---|---|---|---|
| 1 | ELC-001065 | Consumer Electronics | Bulk | Pick_Face | 85 | $71 | 32 days |
| 2 | FSH-000532 | Fashion & Apparel | Reserve | Pick_Face | 84 | $70 | 33 days |
| 3 | FSH-001972 | Fashion & Apparel | Bulk | Pick_Face | 84 | $70 | 33 days |
| 4 | HLT-000059 | Healthcare | Reserve | Pick_Face | 83 | $69 | 33 days |
| 5 | ELC-001958 | Consumer Electronics | Bulk | Pick_Face | 80 | $67 | 34 days |
| 6 | PHM-000756 | Pharmaceutical | Reserve | Pick_Face | 79 | $66 | 35 days |
| 7 | ELC-001974 | Consumer Electronics | Reserve | Pick_Face | 79 | $66 | 35 days |
| 8 | IND-001436 | Industrial | Reserve | Pick_Face | 78 | $65 | 35 days |
| 9 | FMC-000343 | FMCG | Bulk | Pick_Face | 78 | $65 | 35 days |
| 10 | HLT-000309 | Healthcare | Bulk | Pick_Face | 78 | $65 | 35 days |
| 11 | FMC-000683 | FMCG | Bulk | Pick_Face | 78 | $65 | 35 days |
| 12 | CHM-001544 | Chemical | Reserve | Pick_Face | 78 | $65 | 35 days |
| 13 | AUT-001913 | Automotive | Bulk | Pick_Face | 78 | $65 | 35 days |
| 14 | FMC-000219 | FMCG | Bulk | Pick_Face | 77 | $64 | 36 days |
| 15 | IND-001634 | Industrial | Reserve | Pick_Face | 77 | $64 | 36 days |
| 16 | CHM-001897 | Chemical | Reserve | Pick_Face | 77 | $64 | 36 days |
| 17 | FMC-001299 | FMCG | Reserve | Pick_Face | 77 | $64 | 36 days |
| 18 | PHM-001082 | Pharmaceutical | Reserve | Pick_Face | 76 | $63 | 36 days |
| 19 | FMC-001192 | FMCG | Bulk | Pick_Face | 76 | $63 | 36 days |
| 20 | FMC-000698 | FMCG | Bulk | Pick_Face | 76 | $63 | 36 days |

**Note on Hazmat and Pharmaceutical SKUs:** PHM and CHM category SKUs must be placed
in Pick_Face slots with the correct storage type (Controlled or Hazmat). Check with
the WMS team before assigning these to standard ambient Pick_Face slots.

**Full re-slot list** (all 391 Hot/Warm SKUs): `outputs/slotting_recommendations.csv`
Filter column `Mismatch_Type = "Hot/Warm in wrong zone"`, sort by `annual_labour_saved_$`
descending.

---

## Phase 2: Free Up the Pick_Face (123 Cold SKUs to Move Out)

After Phase 1 relocations, you will have created demand for more Pick_Face slots.
Phase 2 clears the bottleneck from the other direction.

Run this query in your WMS (or ask the BA team to pull it from
`outputs/slotting_recommendations.csv`):

```
Filter: Mismatch_Type = "Cold occupying Pick_Face"
Action: Move each SKU from Pick_Face → Bulk
```

123 SKUs total. At 15 minutes each, this is approximately 31 operator-hours — roughly
4 full shift-days of relocation work, scheduled during low-volume windows.

---

## Error Rates to Monitor During Transition

Your Pick_Face zone has the highest absolute error count in the network (715 errors,
24 months). The top three error types to watch during the relocation period are:

| Error Type | Count (24 mo) | Likely Cause During Transition |
|---|---|---|
| WRONG_QTY | 149 | Operators unfamiliar with new slot labels |
| MISSING_LABEL | 148 | Labels not yet printed / applied to new locations |
| WRONG_LOCATION | 143 | WMS slot master not yet synced to physical move |

**Before starting any relocation shift:** confirm the WMS slot master has been updated
for that batch of SKUs. Do not physically move SKUs if the system still shows the old
location — this creates WRONG_LOCATION errors that are difficult to clear.

---

## How Long Will This Take?

| Phase | SKUs | Operator-hours | Approach |
|---|---|---|---|
| Phase 1 — Hot SKU re-slot | 167 | ~42 hrs | 2 operators × 3 days per warehouse |
| Phase 2 — Cold SKU clearance | 123 | ~31 hrs | 2 operators × 2 days per warehouse |
| **Total** | **290** | **~73 hrs** | **Spread across 3 warehouses over ~3 weeks** |

Schedule relocations during the Afternoon shift (lowest pick volume is not true — all
shifts are comparable in the data) or during low-demand days based on your operational
calendar. Avoid executing relocations during active pick waves for the same SKUs.

---

## What You Don't Need to Do

- **Do not address the adjacency programme.** Analysis found that SKU co-occurrence
  within pick sessions is too low (max 7 sessions for any pair) to justify
  targeted co-location. Focus relocation effort on slotting tiers only.
- **Do not change Night shift staffing.** Night shift productivity (7.7 tasks/operator)
  is lower due to lower staffing, not operator performance. Morning and Afternoon shifts
  run at 22.7 and 20.5 tasks/operator respectively — both are consistent and healthy.
- **Do not run a separate campaign for Cycle Count errors.** Cycle Count has the highest
  error rate (1.51%) but these are quality-control tasks by design — some errors are
  expected and are corrected in the same task event. Focus on Pick_Face errors first.

---

## Questions?

Contact Vinyl Kiran Anipe (BA/DA) for questions about the full SKU list, the underlying
pick frequency data, or how to interpret `outputs/slotting_recommendations.csv`.

For WMS slot master updates, coordinate with the WMS / IT team — they will need the
SKU_ID and new Location_ID for each move before physical relocation begins.

---

*Recommendation version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 4 · 2024*
