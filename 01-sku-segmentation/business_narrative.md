# SKU Segmentation — Business Narrative
**Author:** Vinyl Kiran Anipe  
**Role:** Business Analyst / Data Analyst  
**Date:** June 2024  
**Status:** Analysis in progress  
**Project:** DHL Supply Chain — Inventory Optimisation
---
## Executive Summary
DHL's three-warehouse network (NJ01, IL02, TX03) manages 2,000 active SKUs across 
eight product categories with a single uniform replenishment policy applied to all 
products regardless of value or demand behaviour. This approach causes stockouts on 
high-value fast-moving items and excess carrying costs on slow-moving low-value items. 
This analysis applies ABC classification (by revenue contribution) and XYZ 
classification (by demand variability) to segment the full SKU catalogue into nine 
distinct classes, each with a tailored replenishment policy. Expected outcome: reduction 
in stockout events on critical SKUs and a measurable decrease in inventory carrying cost 
on C/Z items.
---
## Business Problem
### Current State
The warehouse team applies the same reorder point, safety stock level, and replenishment 
frequency to every SKU in the catalogue. There is no differentiation between a 
high-velocity Consumer Electronics SKU generating $50,000/month in revenue and a 
Chemical SKU that ships twice a quarter.
### Impact of Current State
- **Stockouts on A-class items:** High-demand SKUs run out before replenishment triggers, 
  causing missed shipments and OTIF breaches.
- **Excess inventory on C-class items:** Low-velocity SKUs occupy prime pick-face slots 
  and tie up working capital.
- **Operational inefficiency:** Floor operators spend equal time managing fast and slow 
  movers, misallocating labour.
### Business Question
*Which SKUs should receive tighter replenishment controls, which can tolerate looser 
policies, and which should be candidates for delisting — based on their revenue 
contribution and demand predictability?*
---
## Stakeholders
| Stakeholder | Role | Primary Interest |
|---|---|---|
| Warehouse Operations Manager | Decision owner | Stockout reduction, labour efficiency |
| Inventory Planner | Daily user | Reorder point and safety stock guidance |
| Commercial / Account Team | Client-facing | OTIF performance, client SLA compliance |
| Finance | Approver | Working capital reduction, carrying cost |
---
## Success Metrics
| Metric | Definition | Target |
|---|---|---|
| Stockout Rate (A-class) | % of days A-class SKUs have zero available qty | Reduce by ≥ 30% |
| Inventory Carrying Cost (C-class) | Avg on-hand value × carrying cost rate for C items | Reduce by ≥ 20% |
| Segmentation Coverage | % of active SKUs assigned to an ABC/XYZ class | 100% |
| Replenishment Policy Adoption | % of SKUs with updated reorder points post-analysis | ≥ 80% within 90 days |
---
## Data Sources
| Table | Source | Key Fields Used |
|---|---|---|
| `sku_master.csv` | DHL WMS — SKU master extract | SKU_ID, Category, ABC_Class, Unit_Price, Unit_Cost |
| `daily_demand.csv` | DHL WMS — daily fulfilment records | SKU_ID, Date, Quantity_Demanded, Quantity_Fulfilled, Revenue, Stockout_Flag |
| `inventory_snapshot.csv` | DHL ERP — monthly inventory positions | SKU_ID, On_Hand_Qty, Available_Qty, Inventory_Value |
**Data period:** January 2022 – December 2023 (24 months)  
**Scope:** All three warehouses (DHL-WH-NJ01, DHL-WH-IL02, DHL-WH-TX03)
---
## Methodology
### Step 1 — Data Extraction and Validation
Pull SKU-level demand history from `daily_demand.csv`. Validate record counts, check 
for nulls and duplicate SKU-date combinations, confirm date range coverage. Flag any 
SKUs with fewer than 30 days of demand history as insufficient for XYZ classification.
### Step 2 — ABC Classification
Compute total revenue per SKU over the full 24-month period. Rank SKUs by descending 
revenue. Assign:
- **A:** Top SKUs accounting for cumulative 80% of total revenue
- **B:** Next tier accounting for cumulative 15% (80–95%)
- **C:** Remaining SKUs accounting for final 5%
This follows the Pareto principle and aligns with DHL's standard inventory 
stratification framework.
### Step 3 — XYZ Classification
Compute Coefficient of Variation (CV) of daily demand per SKU:  
`CV = Standard Deviation of Daily Demand / Mean Daily Demand`
Assign:
- **X:** CV < 0.30 — stable, predictable demand
- **Y:** 0.30 ≤ CV < 0.70 — moderate variability
- **Z:** CV ≥ 0.70 — highly variable or intermittent demand
### Step 4 — Combined ABC/XYZ Matrix
Combine the two classifications to produce nine segments (AX, AY, AZ, BX, BY, BZ, 
CX, CY, CZ). Map each segment to a replenishment policy recommendation.
### Step 5 — Replenishment Policy Framework
Translate segment assignments into actionable inventory policy guidance covering 
safety stock multipliers, reorder frequency, and storage zone recommendations.
---
## ABC/XYZ Replenishment Policy Framework
| Segment | Description | Safety Stock | Reorder Frequency | Storage Zone | Action |
|---|---|---|---|---|---|
| AX | High value, stable | 1.5× base | Weekly | Prime pick-face | Protect at all costs |
| AY | High value, variable | 2.0× base | Twice weekly | Prime pick-face | Buffer aggressively |
| AZ | High value, erratic | 2.5× base | As-needed + manual review | Prime pick-face | Escalate to planner |
| BX | Mid value, stable | 1.2× base | Bi-weekly | Standard pick | Standard process |
| BY | Mid value, variable | 1.5× base | Weekly | Standard pick | Standard process |
| BZ | Mid value, erratic | 1.8× base | Weekly + review | Standard pick | Monitor closely |
| CX | Low value, stable | 0.8× base | Monthly | Reserve | Reduce stock |
| CY | Low value, variable | 1.0× base | Monthly | Reserve | Review regularly |
| CZ | Low value, erratic | Minimal | On-demand | Reserve / delist | Candidate for delisting |
---
## Key Findings

### 1. Data Quality — Clean and Complete
574,509 demand records across 730 days. Zero null values, zero duplicate
SKU-date-warehouse combinations, full date range confirmed across all three
warehouses. 1,664 active SKUs out of 2,000 total (83.2% active rate).
Data is ready for segmentation without pre-processing intervention.

### 2. Revenue Concentration — Tighter Pareto Than the 20/80 Rule
Standard Pareto principle predicts 20% of SKUs drive 80% of revenue.
In this network, only **164 SKUs — 9.9% of the active catalogue** — account
for 80% of total revenue. The concentration is steeper than expected, which
makes the case for targeted A-class controls even more compelling: protecting
fewer than 200 SKUs protects the vast majority of network revenue.

Consumer Electronics and Industrial together generate **55% of total revenue**
despite representing approximately 25% of active SKUs. These two categories
are the highest-priority targets for policy tightening.

### 3. Demand Variability — Network More Predictable Than Typical
XYZ classification against 24 months of daily demand data produced only
X-class (348 SKUs, CV < 0.30) and Y-class (1,316 SKUs, CV 0.30–0.70)
results. No SKUs exceeded the Z-class threshold (CV ≥ 0.70).

This is a meaningful network characteristic: demand is more stable than
typical contract logistics environments where 15–25% of SKUs are usually
Z-class. The practical implication is that the replenishment framework is
simpler to operationalise — planners work with six active segments (AX, AY,
BX, BY, CX, CY) rather than nine. AZ, BZ, and CZ policies are retained in
the framework for future onboarding of more volatile product lines.

### 4. Stockout Impact — Same Rate, Vastly Different Dollar Consequences
The network-wide stockout rate is approximately 3% across all ABC classes.
However, the absolute unit impact differs dramatically:

| ABC Class | Unfulfilled Units | Business Implication |
|---|---|---|
| A | 379,000+ | Direct revenue loss and OTIF breach risk |
| B | Mid-range | Moderate service impact |
| C | ~12,500 | Minimal financial consequence |

A 3% stockout rate applied uniformly treats a $500M-revenue SKU identically
to a $5K-revenue SKU. This is the core failure of the current single-policy
approach. ABC-differentiated safety stock directly addresses this asymmetry.

### 5. Warehouse Performance — Consistent Execution, Uneven SKU Distribution
DHL-WH-NJ01 leads in revenue throughput ($7.1B vs approximately $6.1B each
for IL02 and TX03), indicating higher concentration of A-class or
high-volume SKUs in the New Jersey facility. All three warehouses maintain
approximately 98% fill rates, confirming consistent operational execution
across the network. The improvement lever is replenishment policy, not
operational performance.

### 6. Highest-Revenue SKU Has Above-Average Stockout Exposure
IND-001303 (Industrial category) generated $598M in revenue over the
analysis period — the single highest-revenue SKU in the network. It also
carries a 4.06% stockout rate, above the 3% network average. This is a
ready-made intervention: the SKU with the greatest financial exposure is
also one of the most stockout-prone. It should be the first candidate for
A-class policy tightening under the new framework.

---

## Recommendations

### Immediate Priority Actions

**1. Protect the top 164 SKUs above all else.**
These SKUs represent 9.9% of the active catalogue but 80% of network
revenue. Any stockout in this cohort creates disproportionate financial
and SLA consequences. Safety stock for all 164 should be reviewed and
tightened before any other intervention.

**2. Investigate IND-001303 and any A-class SKU with stockout rate above 3%.**
The highest-revenue SKU in the network has above-average stockout exposure.
This should trigger an immediate safety stock and reorder point audit in
the WMS. Do not wait for full framework rollout.

**3. Start with Consumer Electronics and Industrial categories.**
These two categories account for 55% of revenue. Implementing the
replenishment policy framework for these categories first covers the
majority of financial risk with a manageable scope of change.

**4. Retire the Z-class policy rows from the operational handbook for now.**
No active SKUs currently qualify for Z-class. Keeping these rows in
documentation invites confusion. Retain them in the framework design
document as a forward-looking provision, but remove from operational
planner guidance until needed.

### Full Segmentation-Based Policy (Post Python Analysis)
Detailed reorder point and safety stock multiplier recommendations by
ABC/XYZ segment will be added after the Python classification analysis
is complete. The policy framework in the Methodology section defines
the logic that will govern each of the six active segments.

---
## Open Questions
1. Should SKUs with fewer than 30 days of demand data be excluded or handled separately?
2. Does the commercial team want to override ABC classification for any strategic SKUs 
   (e.g. a low-revenue but contractually critical item)?
3. What is the carrying cost rate currently used by finance for working capital calculations?
4. What is the target review cycle for reclassifying SKUs as demand patterns evolve?
---
## Next Steps
| Action | Owner | Timeline |
|---|---|---|
| Complete ABC/XYZ analysis | BA/DA | This sprint |
| Present findings to Ops Manager | BA/DA | Week 2 |
| Update reorder points in WMS | Inventory Planner | Week 3–4 |
| Track stockout rate (A-class) post-implementation | BA/DA | 90-day review |
---
*Document version 1.0 — findings and recommendations sections to be updated 
post-analysis.*
