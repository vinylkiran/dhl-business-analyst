"""
impact_calculator.py — ROI & Business Impact Summary
Project 4: Warehouse Optimization — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Consolidates savings from slotting optimisation and adjacency changes
into a single business impact summary. Exports outputs/impact_summary.csv.

Assumptions:
  - Labour rate: $25/hr (blended warehouse operator all-in rate)
  - Slotting relocation: 15 min/SKU one-time cost
  - Adjacency benefit: 1.5 min saved per co-occurrence session (reduced travel)
  - Adjacency relocation: 30 min per pair (re-slot both SKUs + verification)
  - Analysis horizon: 24 months (matches dataset period)
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/04-warehouse-optimization/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

DHL_RED   = "#D40511"
DHL_YELLOW= "#FFCC00"
DHL_DARK  = "#1A1A1A"
DHL_MID   = "#555555"
DHL_LIGHT = "#F5F5F5"

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", color=DHL_DARK, pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color=DHL_MID)
    ax.set_ylabel(ylabel, fontsize=10, color=DHL_MID)
    ax.tick_params(colors=DHL_MID, labelsize=9)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CCCCCC")
    ax.set_facecolor(DHL_LIGHT)

print("=" * 70)
print("  IMPACT CALCULATOR — ROI & BUSINESS CASE SUMMARY")
print("=" * 70)

# ── Load upstream outputs ─────────────────────────────────────────────────
slotting = pd.read_csv(os.path.join(OUTS, "slotting_recommendations.csv"))
adjacency= pd.read_csv(os.path.join(OUTS, "adjacency_recommendations.csv"))

# ── Parameters ────────────────────────────────────────────────────────────
LABOUR_RATE_HR        = 25.00   # $/hr
SLOT_RELOC_MIN        = 15.00   # one-time min/SKU to relocate
PICK_SAVING_MIN       = 2.00    # min saved per pick for correctly slotted Hot/Warm SKU
ADJ_SAVING_MIN        = 1.50    # min saved per co-occurrence session for adjacent pairs
ADJ_RELOC_MIN         = 30.00   # one-time min/pair to relocate both SKUs
MONTHS                = 24

print(f"\n── Parameters")
print(f"   Labour rate:              ${LABOUR_RATE_HR:.2f}/hr")
print(f"   Slotting relocation cost: {SLOT_RELOC_MIN:.0f} min/SKU (one-time)")
print(f"   Pick time saving:         {PICK_SAVING_MIN:.1f} min/pick (Hot/Warm correctly slotted)")
print(f"   Adjacency saving:         {ADJ_SAVING_MIN:.1f} min/session (co-located pair)")
print(f"   Adjacency relocation:     {ADJ_RELOC_MIN:.0f} min/pair (one-time)")
print(f"   Analysis horizon:         {MONTHS} months")

# ── Initiative 1: Slotting Optimisation ──────────────────────────────────
print("\n── Initiative 1: Slotting Optimisation (Hot/Warm Re-slot to Pick_Face)")

hot_warm_wrong = slotting[slotting["Mismatch_Type"] == "Hot/Warm in wrong zone"].copy()
n_slot_skus    = len(hot_warm_wrong)

# Time savings: pick_count × 2 min/pick
slot_total_min_saved  = (hot_warm_wrong["pick_count"] * PICK_SAVING_MIN).sum()
slot_hrs_saved        = slot_total_min_saved / 60
slot_labour_saved     = slot_hrs_saved * LABOUR_RATE_HR

# One-time cost: 15 min/SKU × $25/hr × n SKUs
slot_reloc_cost       = n_slot_skus * SLOT_RELOC_MIN / 60 * LABOUR_RATE_HR
slot_roi              = slot_labour_saved / slot_reloc_cost if slot_reloc_cost > 0 else 0
slot_break_even_days  = (slot_reloc_cost / (slot_labour_saved / (MONTHS * 30.44))) if slot_labour_saved > 0 else 999

print(f"   SKUs to re-slot:          {n_slot_skus:,}")
print(f"   Min saved (24 months):    {slot_total_min_saved:,.0f} min  →  {slot_hrs_saved:,.1f} hrs")
print(f"   Labour saving:            ${slot_labour_saved:,.0f}")
print(f"   Relocation cost:          ${slot_reloc_cost:,.0f}")
print(f"   ROI:                      {slot_roi:.1f}×")
print(f"   Break-even:               {slot_break_even_days:.0f} days")

# ── Initiative 2: Adjacency Optimisation ──────────────────────────────────
print("\n── Initiative 2: Adjacency Optimisation (Top 50 Co-occurrence Pairs)")

top50_adj    = adjacency.head(50).copy()
n_adj_pairs  = len(top50_adj)

adj_total_min_saved = (top50_adj["co_occurrence_count"] * ADJ_SAVING_MIN).sum()
adj_hrs_saved       = adj_total_min_saved / 60
adj_labour_saved    = adj_hrs_saved * LABOUR_RATE_HR

adj_reloc_cost      = n_adj_pairs * ADJ_RELOC_MIN / 60 * LABOUR_RATE_HR
adj_roi             = adj_labour_saved / adj_reloc_cost if adj_reloc_cost > 0 else 0
adj_break_even_days = (adj_reloc_cost / (adj_labour_saved / (MONTHS * 30.44))) if adj_labour_saved > 0 else 999

print(f"   Pairs optimised:          {n_adj_pairs}")
print(f"   Min saved (24 months):    {adj_total_min_saved:,.0f} min  →  {adj_hrs_saved:,.1f} hrs")
print(f"   Labour saving:            ${adj_labour_saved:,.0f}")
print(f"   Relocation cost:          ${adj_reloc_cost:,.0f}")
print(f"   ROI:                      {adj_roi:.1f}×")
print(f"   Break-even:               {adj_break_even_days:.0f} days")

# ── Initiative 3: Remove Cold SKUs from Pick_Face ─────────────────────────
print("\n── Initiative 3: Clear Cold SKUs from Pick_Face")

cold_pickface = slotting[slotting["Mismatch_Type"] == "Cold occupying Pick_Face"].copy()
n_cold        = len(cold_pickface)

# Benefit: freeing slots for Hot SKUs (capacity unlock, not direct time saving)
# Cost: 15 min/SKU to relocate
cold_reloc_cost = n_cold * SLOT_RELOC_MIN / 60 * LABOUR_RATE_HR
cold_slots_freed = n_cold
# Indirect saving: each freed slot could accommodate 1 Hot SKU → 2 min/pick × avg hot pick count
avg_hot_picks   = slotting[slotting["Recommended_Tier"] == "Hot"]["pick_count"].mean()
cold_indirect_min = min(n_cold, len(hot_warm_wrong)) * avg_hot_picks * PICK_SAVING_MIN
cold_indirect_save = cold_indirect_min / 60 * LABOUR_RATE_HR

print(f"   Cold SKUs to clear:       {n_cold}")
print(f"   Pick_Face slots freed:    {cold_slots_freed}")
print(f"   Relocation cost:          ${cold_reloc_cost:,.0f}")
print(f"   Indirect saving estimate: ${cold_indirect_save:,.0f} (enabling Hot SKU re-slot)")

# ── Combined Summary ───────────────────────────────────────────────────────
total_saving  = slot_labour_saved + adj_labour_saved
total_cost    = slot_reloc_cost + adj_reloc_cost + cold_reloc_cost
combined_roi  = total_saving / total_cost if total_cost > 0 else 0
overall_be    = (total_cost / (total_saving / (MONTHS * 30.44))) if total_saving > 0 else 999

print("\n── Combined Impact Summary")
print(f"   Total estimated saving (24 months):  ${total_saving:,.0f}")
print(f"   Total implementation cost:           ${total_cost:,.0f}")
print(f"   Combined ROI:                        {combined_roi:.1f}×")
print(f"   Overall break-even:                  {overall_be:.0f} days")
print(f"   Total hours saved:                   {(slot_hrs_saved + adj_hrs_saved):,.1f} hrs")

# ── Build impact_summary.csv ──────────────────────────────────────────────
rows = [
    {"Initiative": "Slotting Optimisation",
     "SKUs_or_Pairs": n_slot_skus, "Unit": "SKUs",
     "Min_Saved_24mo": round(slot_total_min_saved, 0),
     "Hrs_Saved_24mo": round(slot_hrs_saved, 1),
     "Labour_Saving_$": round(slot_labour_saved, 0),
     "Implementation_Cost_$": round(slot_reloc_cost, 0),
     "ROI_x": round(slot_roi, 1),
     "Break_Even_Days": round(slot_break_even_days, 0)},
    {"Initiative": "Adjacency Optimisation",
     "SKUs_or_Pairs": n_adj_pairs, "Unit": "Pairs",
     "Min_Saved_24mo": round(adj_total_min_saved, 0),
     "Hrs_Saved_24mo": round(adj_hrs_saved, 1),
     "Labour_Saving_$": round(adj_labour_saved, 0),
     "Implementation_Cost_$": round(adj_reloc_cost, 0),
     "ROI_x": round(adj_roi, 1),
     "Break_Even_Days": round(adj_break_even_days, 0)},
    {"Initiative": "Clear Cold from Pick_Face",
     "SKUs_or_Pairs": n_cold, "Unit": "SKUs",
     "Min_Saved_24mo": 0, "Hrs_Saved_24mo": 0,
     "Labour_Saving_$": round(cold_indirect_save, 0),
     "Implementation_Cost_$": round(cold_reloc_cost, 0),
     "ROI_x": round(cold_indirect_save / cold_reloc_cost if cold_reloc_cost > 0 else 0, 1),
     "Break_Even_Days": None},
    {"Initiative": "TOTAL",
     "SKUs_or_Pairs": n_slot_skus + n_adj_pairs + n_cold, "Unit": "Mixed",
     "Min_Saved_24mo": round(slot_total_min_saved + adj_total_min_saved, 0),
     "Hrs_Saved_24mo": round(slot_hrs_saved + adj_hrs_saved, 1),
     "Labour_Saving_$": round(total_saving, 0),
     "Implementation_Cost_$": round(total_cost, 0),
     "ROI_x": round(combined_roi, 1),
     "Break_Even_Days": round(overall_be, 0)},
]
impact_df = pd.DataFrame(rows)
impact_df.to_csv(os.path.join(OUTS, "impact_summary.csv"), index=False)
print(f"\n   Exported impact_summary.csv ({len(impact_df)} rows)")

# ── Figure 16: ROI waterfall / bar chart ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("white")

# Left: Saving vs cost by initiative
initiatives   = ["Slotting\nOptimisation", "Adjacency\nOptimisation", "Clear Cold\nfrom Pick_Face"]
savings_vals  = [slot_labour_saved, adj_labour_saved, cold_indirect_save]
cost_vals     = [slot_reloc_cost,   adj_reloc_cost,   cold_reloc_cost]

x = np.arange(len(initiatives))
w = 0.35
ax0 = axes[0]
b1 = ax0.bar(x - w/2, savings_vals, w, label="Labour Saving ($)", color=DHL_RED, edgecolor="white")
b2 = ax0.bar(x + w/2, cost_vals,    w, label="Implementation Cost ($)", color="#4A90D9", edgecolor="white")
ax0.set_xticks(x)
ax0.set_xticklabels(initiatives, fontsize=9)
for bar in b1:
    ax0.text(bar.get_x()+bar.get_width()/2, bar.get_height()+100,
             f"${bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8, color=DHL_DARK)
for bar in b2:
    ax0.text(bar.get_x()+bar.get_width()/2, bar.get_height()+100,
             f"${bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8, color=DHL_DARK)
ax0.legend(fontsize=9)
style_ax(ax0, "Saving vs Implementation Cost by Initiative", "Initiative", "$ Value (24 months)")

# Right: ROI and break-even
roi_vals = [slot_roi, adj_roi]
be_vals  = [slot_break_even_days, adj_break_even_days]
ax1 = axes[1]
color_list = [DHL_RED, "#FF6B35"]
bars = ax1.bar(["Slotting", "Adjacency"], roi_vals, color=color_list, width=0.4, edgecolor="white")
for bar, roi, be in zip(bars, roi_vals, be_vals):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
             f"{roi:.1f}×\n(BE: {be:.0f}d)", ha="center", va="bottom",
             fontsize=9, fontweight="bold", color=DHL_DARK)
ax1.axhline(1.0, color="#AAAAAA", linestyle="--", linewidth=1, label="Break-even (1×)")
ax1.legend(fontsize=9)
style_ax(ax1, "ROI by Initiative (with Break-even Days)", "Initiative", "ROI Multiple")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "16_roi_summary.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 16_roi_summary.png")

print("\n" + "=" * 70)
print("  IMPACT CALCULATOR COMPLETE")
print(f"  Combined saving: ${total_saving:,.0f}  |  Cost: ${total_cost:,.0f}")
print(f"  Combined ROI: {combined_roi:.1f}×  |  Break-even: {overall_be:.0f} days")
print("=" * 70)
