"""
slotting_analysis.py — Warehouse Slot Optimisation Analysis
Project 4: Warehouse Optimization — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Assigns SKUs to frequency-based slotting tiers (Hot/Warm/Cool/Cold),
detects mismatches vs ABC-class zone proxy, calculates time savings,
and exports outputs/slotting_recommendations.csv.

Zone proxy convention (wms_tasks has no Zone column):
  ABC A-class → current zone = Pick_Face   (premium shelf space)
  ABC B-class → current zone = Reserve     (secondary storage)
  ABC C-class → current zone = Bulk        (deep storage)

Slotting tier → recommended zone:
  Hot  (top 10% by pick count) → Pick_Face
  Warm (next 20%)              → Reserve
  Cool (next 30%)              → Reserve
  Cold (bottom 40%)            → Bulk
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import duckdb

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/04-warehouse-optimization/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

# ── DHL colour palette ────────────────────────────────────────────────────────
DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
DHL_DARK   = "#1A1A1A"
DHL_MID    = "#555555"
DHL_LIGHT  = "#F5F5F5"
TIER_COLS  = {"Hot": "#D40511", "Warm": "#FF6B35", "Cool": "#4A90D9", "Cold": "#8DB3CC"}

# ── Style helper ─────────────────────────────────────────────────────────────
def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", color=DHL_DARK, pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color=DHL_MID)
    ax.set_ylabel(ylabel, fontsize=10, color=DHL_MID)
    ax.tick_params(colors=DHL_MID, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#CCCCCC")
    ax.set_facecolor(DHL_LIGHT)

# ── Load data ────────────────────────────────────────────────────────────────
con = duckdb.connect()
con.execute(f"CREATE VIEW wms AS SELECT * FROM read_csv_auto('{DATA}wms_tasks.csv')")
con.execute(f"CREATE VIEW sku AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

print("=" * 70)
print("  SLOTTING ANALYSIS — FREQUENCY-BASED TIER ASSIGNMENT")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# BLOCK A — BUILD SKU PICK FREQUENCY TABLE
# ─────────────────────────────────────────────────────────────────────────────
print("\n── A. SKU Pick Frequency (network-wide, 24 months)")

pick_freq = con.execute("""
    SELECT
        w.SKU_ID,
        s.Category,
        s.ABC_Class,
        s.Storage_Type,
        s.Weight_KG,
        COUNT(*)                                      AS pick_count,
        SUM(w.Quantity)                               AS total_qty_picked,
        AVG(w.Duration_Min)                      AS avg_pick_min,
        SUM(CASE WHEN w.Error_Code IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS accuracy_pct
    FROM wms w
    JOIN sku s ON w.SKU_ID = s.SKU_ID
    WHERE w.Task_Type = 'Pick'
    GROUP BY w.SKU_ID, s.Category, s.ABC_Class, s.Storage_Type, s.Weight_KG
    ORDER BY pick_count DESC
""").df()

total_skus   = len(pick_freq)
total_picks  = pick_freq["pick_count"].sum()
print(f"   SKUs with pick activity: {total_skus:,}")
print(f"   Total pick events:       {total_picks:,}")
print(f"   Avg picks per SKU:       {pick_freq['pick_count'].mean():.1f}")
print(f"   Median picks per SKU:    {pick_freq['pick_count'].median():.1f}")
print(f"   Max picks (single SKU):  {pick_freq['pick_count'].max()}")

# ─────────────────────────────────────────────────────────────────────────────
# BLOCK B — ASSIGN SLOTTING TIERS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── B. Slotting Tier Assignment (network-wide pick frequency)")

pick_freq = pick_freq.sort_values("pick_count", ascending=False).reset_index(drop=True)
n = len(pick_freq)
hot_cut  = int(np.ceil(n * 0.10))
warm_cut = int(np.ceil(n * 0.30))
cool_cut = int(np.ceil(n * 0.60))

def assign_tier(rank):
    if rank < hot_cut:                   return "Hot"
    elif rank < warm_cut:                return "Warm"
    elif rank < cool_cut:                return "Cool"
    else:                                return "Cold"

pick_freq["Frequency_Rank"]   = range(1, n + 1)
pick_freq["Recommended_Tier"] = [assign_tier(i) for i in range(n)]
pick_freq["Recommended_Zone"] = pick_freq["Recommended_Tier"].map(
    {"Hot": "Pick_Face", "Warm": "Reserve", "Cool": "Reserve", "Cold": "Bulk"}
)

# Current zone proxy: ABC class → zone
pick_freq["Current_Zone"] = pick_freq["ABC_Class"].map(
    {"A": "Pick_Face", "B": "Reserve", "C": "Bulk"}
)

tier_summary = (
    pick_freq.groupby("Recommended_Tier", observed=True)
    .agg(sku_count=("SKU_ID", "count"),
         avg_pick_count=("pick_count", "mean"),
         min_pick_count=("pick_count", "min"),
         max_pick_count=("pick_count", "max"),
         pct_of_skus=("SKU_ID", lambda x: len(x) * 100 / n))
    .reindex(["Hot", "Warm", "Cool", "Cold"])
    .reset_index()
)
print(tier_summary.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# BLOCK C — MISMATCH DETECTION
# ─────────────────────────────────────────────────────────────────────────────
print("\n── C. Zone Mismatch Detection (Current ABC Zone vs Recommended Tier Zone)")

pick_freq["Mismatch"] = pick_freq["Current_Zone"] != pick_freq["Recommended_Zone"]
pick_freq["Mismatch_Type"] = "Correct"
mask_hot_misplaced  = (pick_freq["Recommended_Tier"].isin(["Hot", "Warm"])) & (pick_freq["Current_Zone"].isin(["Reserve", "Bulk"]))
mask_cold_misplaced = (pick_freq["Recommended_Tier"] == "Cold") & (pick_freq["Current_Zone"] == "Pick_Face")
pick_freq.loc[mask_hot_misplaced,  "Mismatch_Type"] = "Hot/Warm in wrong zone"
pick_freq.loc[mask_cold_misplaced, "Mismatch_Type"] = "Cold occupying Pick_Face"

mismatch_summary = (
    pick_freq.groupby("Mismatch_Type", observed=True)
    .agg(sku_count=("SKU_ID","count"),
         avg_picks=("pick_count","mean"),
         total_picks=("pick_count","sum"))
    .reset_index()
    .sort_values("sku_count", ascending=False)
)
print(mismatch_summary.to_string(index=False))

total_mismatched = pick_freq["Mismatch"].sum()
mismatch_rate    = total_mismatched / n * 100
print(f"\n   Total mismatched SKUs: {total_mismatched:,} / {n:,} ({mismatch_rate:.1f}%)")

# Detail: top mismatches
hot_wrong = pick_freq[mask_hot_misplaced].shape[0]
cold_wrong = pick_freq[mask_cold_misplaced].shape[0]
print(f"   Hot/Warm SKUs in wrong zone:     {hot_wrong}")
print(f"   Cold SKUs occupying Pick_Face:   {cold_wrong}")

# ─────────────────────────────────────────────────────────────────────────────
# BLOCK D — TIME SAVINGS ESTIMATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n── D. Time Savings Estimation")

# Assumptions (documented for business case):
# - Relocating a Hot/Warm SKU from Reserve/Bulk to Pick_Face saves 2 min/pick
#   (reduced travel distance in typical rack layout)
# - Clearing Cold SKUs from Pick_Face doesn't save pick time directly but
#   unlocks space for Hot SKUs — savings attributed to Hot relocation
# - Labour rate: $25/hr (average warehouse operator all-in rate)
# - One-time relocation cost: 15 min/SKU (pick, label, scan, restock)

SAVINGS_PER_PICK_MIN    = 2.0   # minutes saved per pick for correctly slotted Hot/Warm SKU
LABOUR_RATE_HR          = 25.0  # $ per hour
RELOCATION_MIN_PER_SKU  = 15.0  # one-time cost

# Hot/Warm SKUs currently in wrong zone
hot_warm_misplaced = pick_freq[mask_hot_misplaced].copy()
hot_warm_misplaced["annual_picks_est"]      = hot_warm_misplaced["pick_count"]  # 24-month data → use as-is
hot_warm_misplaced["annual_min_saved"]      = hot_warm_misplaced["annual_picks_est"] * SAVINGS_PER_PICK_MIN
hot_warm_misplaced["annual_labour_saved_$"] = hot_warm_misplaced["annual_min_saved"] / 60 * LABOUR_RATE_HR
hot_warm_misplaced["relocation_cost_$"]     = RELOCATION_MIN_PER_SKU / 60 * LABOUR_RATE_HR
hot_warm_misplaced["break_even_days"]       = (
    hot_warm_misplaced["relocation_cost_$"] / (hot_warm_misplaced["annual_labour_saved_$"] / 365)
).round(1)

total_min_saved   = hot_warm_misplaced["annual_min_saved"].sum()
total_hrs_saved   = total_min_saved / 60
total_labour_saved = hot_warm_misplaced["annual_labour_saved_$"].sum()
total_relocation  = hot_warm_misplaced["relocation_cost_$"].sum()
avg_break_even    = hot_warm_misplaced["break_even_days"].median()

print(f"   Hot/Warm SKUs to relocate:         {len(hot_warm_misplaced):,}")
print(f"   Total minutes saved (network):     {total_min_saved:,.0f} min / 24 months")
print(f"   Total hours saved (network):       {total_hrs_saved:,.1f} hrs / 24 months")
print(f"   Estimated labour saving:           ${total_labour_saved:,.0f} / 24 months")
print(f"   One-time relocation cost:          ${total_relocation:,.0f}")
print(f"   Median break-even:                 {avg_break_even:.0f} days")
print(f"   ROI (labour saved / reloc cost):   {total_labour_saved / total_relocation:.1f}×")

# Priority 20 — highest-impact re-slots
top20 = (
    hot_warm_misplaced
    .sort_values("annual_labour_saved_$", ascending=False)
    .head(20)[["SKU_ID","Category","ABC_Class","Recommended_Tier","Current_Zone",
               "Recommended_Zone","pick_count","annual_min_saved","annual_labour_saved_$","break_even_days"]]
)
print(f"\n── D2. Top 20 Priority Re-Slots by Labour Saving")
print(top20.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# BLOCK E — WAREHOUSE-LEVEL SLOTTING BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────
print("\n── E. Slotting Tier Distribution by Warehouse")

wh_tier = con.execute("""
    SELECT
        w.Warehouse_ID,
        s.ABC_Class,
        COUNT(DISTINCT w.SKU_ID)                AS sku_count,
        COUNT(*)                                AS pick_count,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY w.Warehouse_ID) AS pct_picks
    FROM wms w
    JOIN sku s ON w.SKU_ID = s.SKU_ID
    WHERE w.Task_Type = 'Pick'
    GROUP BY w.Warehouse_ID, s.ABC_Class
    ORDER BY w.Warehouse_ID, s.ABC_Class
""").df()
print(wh_tier.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT — slotting_recommendations.csv
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Exporting outputs/slotting_recommendations.csv")

export_df = pick_freq[[
    "SKU_ID","Category","ABC_Class","Storage_Type","Weight_KG",
    "Frequency_Rank","Recommended_Tier","Recommended_Zone","Current_Zone",
    "Mismatch","Mismatch_Type","pick_count","total_qty_picked",
    "avg_pick_min","accuracy_pct"
]].copy()

# Add savings columns (fill 0 for non-mismatched)
pick_freq["annual_min_saved_est"]      = 0.0
pick_freq["annual_labour_saved_$_est"] = 0.0
pick_freq["break_even_days_est"]       = 0.0
pick_freq.loc[mask_hot_misplaced, "annual_min_saved_est"]      = hot_warm_misplaced["annual_min_saved"].values
pick_freq.loc[mask_hot_misplaced, "annual_labour_saved_$_est"] = hot_warm_misplaced["annual_labour_saved_$"].values
pick_freq.loc[mask_hot_misplaced, "break_even_days_est"]       = hot_warm_misplaced["break_even_days"].values

export_df = pick_freq[[
    "SKU_ID","Category","ABC_Class","Storage_Type","Weight_KG",
    "Frequency_Rank","Recommended_Tier","Recommended_Zone","Current_Zone",
    "Mismatch","Mismatch_Type","pick_count","total_qty_picked","avg_pick_min","accuracy_pct",
    "annual_min_saved_est","annual_labour_saved_$_est","break_even_days_est"
]]
export_df.to_csv(os.path.join(OUTS, "slotting_recommendations.csv"), index=False)
print(f"   Exported {len(export_df):,} rows to slotting_recommendations.csv")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────────────────────────────────────

# ── Figure 09: Slotting tier distribution + mismatch rate
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.patch.set_facecolor("white")
fig.suptitle("Warehouse Slotting Analysis — Tier Distribution & Mismatches",
             fontsize=14, fontweight="bold", color=DHL_DARK, y=1.02)

# Left: tier distribution (SKU count)
ax0 = axes[0]
tiers = ["Hot", "Warm", "Cool", "Cold"]
counts = [tier_summary.set_index("Recommended_Tier").loc[t, "sku_count"] for t in tiers]
bars = ax0.bar(tiers, counts, color=[TIER_COLS[t] for t in tiers], width=0.55, edgecolor="white", linewidth=1.5)
for bar, cnt in zip(bars, counts):
    ax0.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, str(cnt),
             ha="center", va="bottom", fontsize=10, fontweight="bold", color=DHL_DARK)
style_ax(ax0, "SKU Count by Slotting Tier", "Tier", "SKU Count")

# Middle: pick volume share by tier
ax1 = axes[1]
tier_picks = [pick_freq[pick_freq["Recommended_Tier"] == t]["pick_count"].sum() for t in tiers]
wedges, texts, autotexts = ax1.pie(
    tier_picks, labels=tiers, autopct="%1.0f%%",
    colors=[TIER_COLS[t] for t in tiers],
    startangle=90, pctdistance=0.75,
    wedgeprops={"edgecolor": "white", "linewidth": 2}
)
for at in autotexts:
    at.set_fontsize(10); at.set_fontweight("bold"); at.set_color("white")
ax1.set_title("Pick Volume Share by Tier", fontsize=13, fontweight="bold", color=DHL_DARK, pad=10)

# Right: mismatch breakdown
ax2 = axes[2]
mismatch_labels = ["Correct\nSlotting", "Hot/Warm\nin Wrong Zone", "Cold in\nPick_Face"]
mismatch_counts = [
    n - total_mismatched,
    hot_wrong,
    cold_wrong
]
colors_mm = ["#4CAF50", DHL_RED, DHL_YELLOW]
bars2 = ax2.bar(mismatch_labels, mismatch_counts, color=colors_mm, width=0.5, edgecolor="white", linewidth=1.5)
for bar, cnt in zip(bars2, mismatch_counts):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(cnt),
             ha="center", va="bottom", fontsize=10, fontweight="bold", color=DHL_DARK)
style_ax(ax2, "Zone Mismatch Breakdown", "Mismatch Type", "SKU Count")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "09_slotting_tier_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 09_slotting_tier_distribution.png")

# ── Figure 10: Top 20 re-slot candidates (horizontal bar chart)
fig, ax = plt.subplots(figsize=(13, 8))
fig.patch.set_facecolor("white")

top20_plot = top20.sort_values("annual_labour_saved_$").tail(20)
y_pos = range(len(top20_plot))
colors_bar = [TIER_COLS[t] for t in top20_plot["Recommended_Tier"]]
bars = ax.barh(y_pos, top20_plot["annual_labour_saved_$"], color=colors_bar, height=0.65, edgecolor="white", linewidth=0.8)

for i, (val, sku, tier) in enumerate(zip(top20_plot["annual_labour_saved_$"],
                                           top20_plot["SKU_ID"],
                                           top20_plot["Recommended_Tier"])):
    ax.text(val + 0.3, i, f"  ${val:.0f}", va="center", ha="left", fontsize=8.5, color=DHL_DARK)

ax.set_yticks(y_pos)
ax.set_yticklabels(
    [f"{row['SKU_ID']} ({row['ABC_Class']}) → {row['Recommended_Zone']}"
     for _, row in top20_plot.iterrows()],
    fontsize=8.5
)
style_ax(ax, "Top 20 Re-Slot Priorities by Labour Saving (24 months)",
         "Estimated Labour Saving ($)", "SKU")

# Legend
from matplotlib.patches import Patch
legend_els = [Patch(facecolor=TIER_COLS[t], label=t) for t in ["Hot","Warm"]]
ax.legend(handles=legend_els, title="Tier", loc="lower right", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "10_top20_reslot_priorities.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 10_top20_reslot_priorities.png")

# ── Figure 11: Pick distribution (box by tier)
fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("white")

tier_data = [pick_freq[pick_freq["Recommended_Tier"] == t]["pick_count"].values for t in tiers]
bp = ax.boxplot(tier_data, patch_artist=True, widths=0.5,
                medianprops={"color": "white", "linewidth": 2},
                whiskerprops={"color": DHL_MID},
                capprops={"color": DHL_MID},
                flierprops={"marker": "o", "markersize": 4, "alpha": 0.5})
for patch, t in zip(bp["boxes"], tiers):
    patch.set_facecolor(TIER_COLS[t])
    patch.set_alpha(0.85)

ax.set_xticklabels(tiers, fontsize=10)
style_ax(ax, "Pick Count Distribution by Slotting Tier", "Tier", "Pick Count (24 months)")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "11_pick_distribution_by_tier.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 11_pick_distribution_by_tier.png")

print("\n" + "=" * 70)
print("  SLOTTING ANALYSIS COMPLETE")
print(f"  Mismatched SKUs: {total_mismatched}/{n} ({mismatch_rate:.1f}%)")
print(f"  Hot/Warm misplaced: {hot_wrong}   Cold in Pick_Face: {cold_wrong}")
print(f"  Estimated labour saving: ${total_labour_saved:,.0f} (24 months)")
print(f"  Relocation cost: ${total_relocation:,.0f}   ROI: {total_labour_saved/total_relocation:.1f}x")
print(f"  Median break-even: {avg_break_even:.0f} days")
print("=" * 70)
