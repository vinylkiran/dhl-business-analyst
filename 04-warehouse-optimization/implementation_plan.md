# Warehouse Slotting Optimisation — Implementation Plan
**Prepared by:** Vinyl Kiran Anipe (BA/DA)  
**For:** Warehouse Operations Manager + WMS / IT Team  
**Date:** June 2024  
**Version:** 1.0

---

## Overview

This plan covers the end-to-end execution of the slotting optimisation programme across
DHL-WH-IL02, DHL-WH-NJ01, and DHL-WH-TX03. It is organised into three phases over
approximately 8 weeks.

**Total SKUs to relocate:** 290 (167 Hot SKUs in Phase 1 + 123 Cold SKUs in Phase 2)  
**Total implementation cost:** $3,838 (one-time labour)  
**Total projected saving:** $22,414 (24 months, labour only)  
**Overall ROI:** 5.8× · Break-even: 125 days

---

## Phase 1 — Weeks 1–2: Hot SKU Re-slot to Pick_Face

**Objective:** Move the top 167 Hot-tier SKUs from Reserve or Bulk storage to Pick_Face.

**Who does this:**
- WMS / IT Team: updates the slot master before physical moves begin
- 2–3 warehouse operators per warehouse per day for relocation
- Ops Manager: signs off on each batch before and after

**Steps per warehouse (repeat for IL02, NJ01, TX03):**

1. **WMS Team — Day 1, Pre-work:**
   - Export the Hot-SKU re-slot list from `outputs/slotting_recommendations.csv`
     (filter: Mismatch_Type = "Hot/Warm in wrong zone", Recommended_Tier = "Hot")
   - Identify available Pick_Face slot IDs for each SKU
   - Update WMS slot master with new Location_ID for each SKU
   - Print and apply new location labels to target slots
   - Flag any Hazmat or Controlled storage SKUs that require specific slot types

2. **Operators — Days 1–3 per warehouse:**
   - Pick up the printed re-slot work order from Ops Manager
   - Physically move each SKU from old location to new Pick_Face slot
   - Scan in at new location to confirm WMS update
   - Sign off each line on the work order when complete

3. **Ops Manager — Day 4:**
   - Verify spot-check: pull 10 random SKUs from the re-slot list and confirm
     physical location matches WMS slot master
   - Review same-day Pick error log for WRONG_LOCATION spikes
   - Sign off Phase 1 completion

**SKU counts per warehouse (approximate; final counts from slotting_recommendations.csv):**

| Warehouse | Hot SKUs to move | Est. operator-hours |
|---|---|---|
| DHL-WH-IL02 | ~56 | ~14 hrs |
| DHL-WH-NJ01 | ~55 | ~14 hrs |
| DHL-WH-TX03 | ~56 | ~14 hrs |
| **Total** | **~167** | **~42 hrs** |

**Success criteria for Phase 1:**
- ≥ 167 Hot SKUs physically in Pick_Face locations
- WMS slot master matches physical locations (0 WRONG_LOCATION errors attributable to the re-slot batch)
- Phase 1 error log review: no sustained increase in Pick_Face error rate above 0.80%

---

## Phase 2 — Weeks 3–4: Freeze + Clear Cold SKUs from Pick_Face

**Objective:** (a) Prevent any future C-class / Cold-tier SKU from being slotted into
Pick_Face. (b) Physically move existing 123 Cold SKUs out of Pick_Face to Bulk.

**Sub-step 2a: Freeze (Week 3, Day 1 — IT Team, 1–2 hours)**

Update WMS receiving logic so that any new SKU with ABC_Class = C and no prior pick
history defaults to Reserve or Bulk on first receipt — not Pick_Face.

Specifically:
- Add a rule to the WMS slotting suggestion engine: if ABC_Class = C AND first_receipt = true → suggest Bulk
- If manual override is required (Ops Manager discretion for expected-high-velocity new lines), log the override reason in WMS notes

**Sub-step 2b: Cold SKU clearance (Weeks 3–4, Operators)**

The Cold SKU clearance follows the same process as Phase 1:

1. WMS Team identifies available Bulk slot IDs for each Cold SKU
2. Update WMS slot master before physical moves
3. Operators move Cold SKUs from Pick_Face to Bulk, scanning at new location
4. Ops Manager spot-check and sign-off

**SKU counts per warehouse:**

| Warehouse | Cold SKUs to clear | Est. operator-hours |
|---|---|---|
| DHL-WH-IL02 | ~41 | ~10 hrs |
| DHL-WH-NJ01 | ~41 | ~10 hrs |
| DHL-WH-TX03 | ~41 | ~10 hrs |
| **Total** | **~123** | **~31 hrs** |

**Success criteria for Phase 2:**
- ≥ 100 Cold SKUs physically relocated from Pick_Face to Bulk
- WMS receiving freeze confirmed and tested with one incoming C-class SKU receipt
- Pick_Face mismatch rate: Cold SKUs in Pick_Face reduced from 123 to ≤ 23

---

## Phase 3 — Month 2: Warm SKU Re-sort + Monitoring

**Objective:** Complete the remaining Warm-tier re-slots and establish a quarterly
slotting review cadence.

**3a: Warm SKU re-slot (Weeks 5–6)**

Warm SKUs (next 20% by pick frequency; pick count 63–69 over 24 months) that are
currently in Bulk should be moved to Reserve. This is a lower-urgency move than Phase 1
because Warm SKUs have a longer break-even horizon, but it completes the slotting
programme.

Full Warm-SKU list: `outputs/slotting_recommendations.csv`  
Filter: Mismatch_Type = "Hot/Warm in wrong zone", Recommended_Tier = "Warm", Current_Zone = "Bulk"

**3b: WRONG_QTY error investigation (Week 5)**

Schedule a focused one-week observation period in Pick_Face across all three warehouses.
The leading error type in Pick_Face is WRONG_QTY (149 errors over 24 months). Have
the Ops Manager or a senior operator spend 5–10 minutes per shift at the start of each
pick wave checking the following:

- Are quantity fields clearly displayed on the pick list / handheld device?
- Are units of measure (each vs case vs pallet) clearly labelled on the shelf?
- Is there evidence of operator confusion between inner-pack and outer-pack quantities?

Document findings and raise a corrective action if a systemic cause is identified.

**3c: Quarterly slotting rerun (Month 2, BA/DA)**

Schedule a quarterly execution of `slotting_analysis.py` using a fresh pull of WMS pick
data. The output `outputs/slotting_recommendations.csv` should be reviewed by the Ops
Manager to identify new mismatches that have emerged due to demand shifts.

Recommended cadence: January, April, July, October (aligned with seasonal planning windows).

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| WMS slot master not updated before physical move | Medium | High — WRONG_LOCATION errors | Strict process: IT confirms update before operators begin each batch |
| Hazmat / Controlled SKUs placed in non-compliant slots | Low | High — compliance risk | WMS Team flags all PHM and CHM SKUs before Phase 1 work orders are printed |
| Pick_Face accuracy drops during transition | Medium | Medium — operational | Ops Manager monitors error log daily during Phases 1–2; pause if error rate exceeds 1.0% |
| Insufficient Pick_Face slots available for all Hot SKUs | Low | Medium | Phase 1 clears slots concurrently with Phase 2; prioritise top-20 Hot SKUs if slot count is constrained |
| Seasonal demand shift makes current tiers obsolete | Low | Low | Quarterly rerun cadence (3c) catches this within one cycle |

---

## Roles and Responsibilities

| Role | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| BA/DA (Vinyl) | Provide re-slot lists; support Ops Manager queries | Provide Cold-SKU list | Run quarterly rerun; update recommendations |
| WMS / IT Team | Update slot master; print labels | Update slot master; implement receiving freeze | Schedule quarterly data extract |
| Ops Manager | Sign off batches; daily error monitoring | Sign off batches; review freeze logic | Oversee Warm re-sort; manage error investigation |
| Warehouse Operators | Execute relocations | Execute relocations | Execute Warm re-sorts |

---

## Timeline Summary

| Week | Activity | Owner |
|---|---|---|
| Week 1 | WMS updates slot master for Hot SKUs (top 20 priority) | WMS / IT |
| Week 1 | Phase 1 relocation begins — Hot SKUs, all three warehouses | Operators |
| Week 2 | Phase 1 complete; Ops Manager spot-check and sign-off | Ops Manager |
| Week 3 | WMS receiving freeze implemented for Cold / C-class SKUs | WMS / IT |
| Week 3 | Phase 2 clearance begins — Cold SKUs, all three warehouses | Operators |
| Week 4 | Phase 2 complete; Ops Manager sign-off | Ops Manager |
| Week 5 | WRONG_QTY error investigation (Pick_Face) | Ops Manager |
| Week 5–6 | Warm SKU re-sort (Bulk → Reserve) | Operators |
| Month 2 | Quarterly slotting review cadence established | BA/DA |
| Month 3 | First quarterly rerun; review findings | BA/DA + Ops Manager |

---

*Implementation plan version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · Project 4 · 2024*
