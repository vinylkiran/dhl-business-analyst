"""
affinity_analysis.py — SKU Co-occurrence & Adjacency Analysis
Project 4: Warehouse Optimization — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Identifies SKU pairs that are picked together in the same warehouse
on the same date and shift. High co-occurrence pairs should be slotted
adjacent to reduce picker travel. Exports outputs/adjacency_recommendations.csv.
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from itertools import combinations
import duckdb

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/04-warehouse-optimization/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

DHL_RED   = "#D40511"
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

con = duckdb.connect()
con.execute(f"CREATE VIEW wms AS SELECT * FROM read_csv_auto('{DATA}wms_tasks.csv')")
con.execute(f"CREATE VIEW sku AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

print("=" * 70)
print("  AFFINITY / CO-OCCURRENCE ANALYSIS")
print("=" * 70)

# ── Block A: Build pick session groups ────────────────────────────────────
print("\n── A. Building Pick Session Groups (Warehouse + Date + Shift)")

picks = con.execute("""
    SELECT
        SKU_ID,
        Warehouse_ID,
        Task_Date,
        Shift
    FROM wms
    WHERE Task_Type = 'Pick'
    ORDER BY Warehouse_ID, Task_Date, Shift, SKU_ID
""").df()

print(f"   Pick events loaded: {len(picks):,}")
total_sessions = picks.groupby(["Warehouse_ID","Task_Date","Shift"]).ngroups
print(f"   Unique pick sessions: {total_sessions:,}")
print(f"   Avg SKUs per session: {len(picks) / total_sessions:.1f}")

# ── Block B: Co-occurrence counting ───────────────────────────────────────
print("\n── B. Computing Co-occurrence Pairs (this may take ~30s for large data)")

# Group SKUs per session
sessions = (
    picks
    .groupby(["Warehouse_ID","Task_Date","Shift"])["SKU_ID"]
    .apply(list)
    .reset_index()
)

# Count co-occurrences
pair_counts = {}
for _, row in sessions.iterrows():
    skus = sorted(set(row["SKU_ID"]))  # deduplicate within session
    for a, b in combinations(skus, 2):
        key = (a, b)
        pair_counts[key] = pair_counts.get(key, 0) + 1

print(f"   Unique SKU pairs found: {len(pair_counts):,}")

# Convert to dataframe
pairs_df = pd.DataFrame(
    [(a, b, cnt) for (a, b), cnt in pair_counts.items()],
    columns=["SKU_A", "SKU_B", "co_occurrence_count"]
).sort_values("co_occurrence_count", ascending=False).reset_index(drop=True)

# Enrich with SKU metadata
sku_meta = con.execute("""
    SELECT SKU_ID, Category, ABC_Class, Recommended_Tier
    FROM sku
    LEFT JOIN (
        SELECT SKU_ID AS sid,
               NTILE(4) OVER (ORDER BY pick_ct DESC) AS q
        FROM (SELECT SKU_ID, COUNT(*) AS pick_ct FROM wms WHERE Task_Type='Pick' GROUP BY SKU_ID)
    ) freq ON sku.SKU_ID = freq.sid
""").df() if False else con.execute("""
    SELECT SKU_ID, Category, ABC_Class, Storage_Type
    FROM sku
""").df()

pairs_df = pairs_df.merge(sku_meta.rename(columns={"SKU_ID":"SKU_A","Category":"Cat_A","ABC_Class":"ABC_A","Storage_Type":"ST_A"}), on="SKU_A", how="left")
pairs_df = pairs_df.merge(sku_meta.rename(columns={"SKU_ID":"SKU_B","Category":"Cat_B","ABC_Class":"ABC_B","Storage_Type":"ST_B"}), on="SKU_B", how="left")

# Tag same-category pairs
pairs_df["Same_Category"]    = pairs_df["Cat_A"] == pairs_df["Cat_B"]
pairs_df["Same_ABC"]         = pairs_df["ABC_A"] == pairs_df["ABC_B"]
pairs_df["Adjacency_Priority"] = pd.cut(
    pairs_df["co_occurrence_count"],
    bins=[0, 50, 100, 200, 9999],
    labels=["Low", "Medium", "High", "Critical"]
)

top50 = pairs_df.head(50)
print(f"\n   Top 10 SKU pairs by co-occurrence:")
print(top50.head(10)[["SKU_A","SKU_B","co_occurrence_count","Cat_A","Cat_B","Same_Category","Adjacency_Priority"]].to_string(index=False))

# ── Block C: Summary statistics ───────────────────────────────────────────
print("\n── C. Adjacency Priority Summary")

prio_summary = (
    pairs_df.groupby("Adjacency_Priority", observed=True)
    .agg(pair_count=("SKU_A","count"),
         avg_co_occ=("co_occurrence_count","mean"),
         max_co_occ=("co_occurrence_count","max"))
    .reset_index()
)
print(prio_summary.to_string(index=False))

same_cat_pct = pairs_df["Same_Category"].mean() * 100
print(f"\n   Same-category pairs in top 50: {top50['Same_Category'].sum()} / 50 ({top50['Same_Category'].mean()*100:.0f}%)")
print(f"   Overall same-category rate:    {same_cat_pct:.1f}%")

# ── Block D: Warehouse-level affinity breakdown ────────────────────────────
print("\n── D. Top 10 Pairs per Warehouse")

for wh in picks["Warehouse_ID"].unique():
    wh_picks = picks[picks["Warehouse_ID"] == wh]
    wh_sessions = (
        wh_picks.groupby(["Task_Date","Shift"])["SKU_ID"]
        .apply(list)
        .reset_index()
    )
    wh_pairs = {}
    for _, row in wh_sessions.iterrows():
        skus = sorted(set(row["SKU_ID"]))
        for a, b in combinations(skus, 2):
            wh_pairs[(a, b)] = wh_pairs.get((a, b), 0) + 1

    top_wh = sorted(wh_pairs.items(), key=lambda x: -x[1])[:5]
    print(f"\n   {wh}:")
    for (a, b), cnt in top_wh:
        print(f"     {a} ↔ {b}: {cnt} sessions")

# ── Export ─────────────────────────────────────────────────────────────────
print("\n── Exporting outputs/adjacency_recommendations.csv (top 200 pairs)")

export_cols = ["SKU_A","SKU_B","co_occurrence_count","Cat_A","Cat_B",
               "ABC_A","ABC_B","ST_A","ST_B","Same_Category","Same_ABC","Adjacency_Priority"]
export_df = pairs_df.head(200)[export_cols]
export_df.to_csv(os.path.join(OUTS, "adjacency_recommendations.csv"), index=False)
print(f"   Exported {len(export_df)} rows to adjacency_recommendations.csv")

# ── Figure 14: Top 30 co-occurrence pairs (horizontal bar) ────────────────
fig, ax = plt.subplots(figsize=(12, 9))
fig.patch.set_facecolor("white")
top30 = pairs_df.head(30).sort_values("co_occurrence_count")

colors = [DHL_RED if sc else "#4A90D9" for sc in top30["Same_Category"]]
labels = [f"{a}\n↔ {b}" for a, b in zip(top30["SKU_A"], top30["SKU_B"])]
bars = ax.barh(range(len(top30)), top30["co_occurrence_count"], color=colors, height=0.65, edgecolor="white")
ax.set_yticks(range(len(top30)))
ax.set_yticklabels(labels, fontsize=7.5)
for i, val in enumerate(top30["co_occurrence_count"]):
    ax.text(val + 0.5, i, str(val), va="center", fontsize=8, color=DHL_DARK)

style_ax(ax, "Top 30 SKU Pairs by Co-occurrence (same pick session)",
         "Co-occurrence Count (sessions)", "SKU Pair")

from matplotlib.patches import Patch
legend_els = [Patch(facecolor=DHL_RED, label="Same Category"), Patch(facecolor="#4A90D9", label="Cross-Category")]
ax.legend(handles=legend_els, fontsize=9, loc="lower right")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "14_sku_cooccurrence_top30.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 14_sku_cooccurrence_top30.png")

# ── Figure 15: Co-occurrence count distribution ────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4))
fig.patch.set_facecolor("white")

ax.hist(pairs_df["co_occurrence_count"], bins=50, color=DHL_RED, edgecolor="white", alpha=0.8)
ax.axvline(pairs_df["co_occurrence_count"].median(), color=DHL_DARK, linestyle="--", linewidth=1.5, label=f"Median: {pairs_df['co_occurrence_count'].median():.0f}")
ax.axvline(pairs_df["co_occurrence_count"].quantile(0.9), color="#FFCC00", linestyle="--", linewidth=1.5, label=f"90th pct: {pairs_df['co_occurrence_count'].quantile(0.9):.0f}")
ax.legend(fontsize=9)
style_ax(ax, "Distribution of SKU Co-occurrence Counts", "Co-occurrence Count", "Number of Pairs")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "15_cooccurrence_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 15_cooccurrence_distribution.png")

print("\n" + "=" * 70)
print("  AFFINITY ANALYSIS COMPLETE")
print(f"  Unique pairs: {len(pairs_df):,}   Top pair co-occurrence: {pairs_df['co_occurrence_count'].iloc[0]}")
print(f"  Critical adjacency pairs (>200 sessions): {(pairs_df['co_occurrence_count']>200).sum()}")
print(f"  High adjacency pairs (100-200 sessions):  {((pairs_df['co_occurrence_count']>100)&(pairs_df['co_occurrence_count']<=200)).sum()}")
print("=" * 70)
