"""
operator_analysis.py — Operator Performance Analysis
Project 5: WMS Operational Dashboard — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Analyses individual operator performance across all 180 operators.
Flags below-threshold (coaching) and above-threshold (high performers).
Exports: outputs/operator_scorecard.csv
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import duckdb

warnings.filterwarnings("ignore")

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/05-wms-dashboard/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

COACHING_THRESHOLD     = 98.5
HIGH_PERFORMER_THRESHOLD = 99.8

DHL_RED   = "#D40511"
DHL_DARK  = "#1A1A1A"
DHL_MID   = "#555555"
DHL_LIGHT = "#F5F5F5"

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold", color=DHL_DARK, pad=8)
    ax.set_xlabel(xlabel, fontsize=9, color=DHL_MID)
    ax.set_ylabel(ylabel, fontsize=9, color=DHL_MID)
    ax.tick_params(colors=DHL_MID, labelsize=8)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CCCCCC")
    ax.set_facecolor(DHL_LIGHT)

con = duckdb.connect()
con.execute(f"CREATE VIEW wms AS SELECT * FROM read_csv_auto('{DATA}wms_tasks.csv')")

print("=" * 72)
print("  OPERATOR ANALYSIS — PERFORMANCE SCORECARD")
print("=" * 72)

# ── Base operator scorecard ───────────────────────────────────────────────────
print("\n── A. Operator Base Scorecard (All Task Types)")

op_base = con.execute("""
    SELECT
        Operator_ID,
        Warehouse_ID,
        COUNT(*)                                                     AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_accuracy_pct,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy_pct,
        AVG(Duration_Min)                                            AS avg_task_duration_min,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)           AS total_picks,
        SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END)        AS total_putaways,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)      AS total_errors,
        SUM(CASE WHEN Error_Code='WRONG_SKU' THEN 1 ELSE 0 END)     AS wrong_sku_errors,
        SUM(CASE WHEN Error_Code='WRONG_QTY' THEN 1 ELSE 0 END)     AS wrong_qty_errors,
        SUM(CASE WHEN Error_Code='MISSING_LABEL' THEN 1 ELSE 0 END) AS missing_label_errors,
        SUM(CASE WHEN Error_Code='DAMAGED' THEN 1 ELSE 0 END)       AS damaged_errors,
        SUM(CASE WHEN Error_Code='WRONG_LOCATION' THEN 1 ELSE 0 END) AS wrong_location_errors,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0,0) AS picks_per_hour
    FROM wms
    GROUP BY Operator_ID, Warehouse_ID
    ORDER BY overall_accuracy_pct DESC
""").df()

print(f"   Total operators: {len(op_base)}")
print(f"   High performers (≥{HIGH_PERFORMER_THRESHOLD}%): {(op_base['overall_accuracy_pct']>=HIGH_PERFORMER_THRESHOLD).sum()}")
print(f"   Needs coaching (<{COACHING_THRESHOLD}%):         {(op_base['overall_accuracy_pct']<COACHING_THRESHOLD).sum()}")
print(f"   Accuracy range: {op_base['overall_accuracy_pct'].min():.2f}% – {op_base['overall_accuracy_pct'].max():.2f}%")
print(f"   Mean accuracy:  {op_base['overall_accuracy_pct'].mean():.2f}%")

# ── Performance trend (improving vs declining) ────────────────────────────────
print("\n── B. Performance Trend — First Half vs Second Half")

trend = con.execute("""
    SELECT
        Operator_ID,
        Warehouse_ID,
        SUM(CASE WHEN Task_Date < '2023-01-01' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Date < '2023-01-01' THEN 1 ELSE 0 END),0) AS h1_accuracy_pct,
        SUM(CASE WHEN Task_Date >= '2023-01-01' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Date >= '2023-01-01' THEN 1 ELSE 0 END),0) AS h2_accuracy_pct
    FROM wms
    GROUP BY Operator_ID, Warehouse_ID
""").df()

trend["accuracy_delta"]  = trend["h2_accuracy_pct"] - trend["h1_accuracy_pct"]
trend["trend_direction"] = trend["accuracy_delta"].apply(
    lambda x: "Improving" if x > 0.1 else ("Declining" if x < -0.1 else "Stable"))

trend_summary = trend["trend_direction"].value_counts()
print(f"   Improving:  {trend_summary.get('Improving',0)}")
print(f"   Stable:     {trend_summary.get('Stable',0)}")
print(f"   Declining:  {trend_summary.get('Declining',0)}")

# Merge trend into base
op_scorecard = op_base.merge(
    trend[["Operator_ID","Warehouse_ID","h1_accuracy_pct","h2_accuracy_pct","accuracy_delta","trend_direction"]],
    on=["Operator_ID","Warehouse_ID"], how="left"
)

# ── Operator ranking and flags ────────────────────────────────────────────────
print("\n── C. Operator Ranking and Performance Flags")

op_scorecard["accuracy_rank"]   = op_scorecard["overall_accuracy_pct"].rank(ascending=False, method="min").astype(int)
op_scorecard["performance_flag"] = op_scorecard["overall_accuracy_pct"].apply(
    lambda x: "HIGH_PERFORMER" if x >= HIGH_PERFORMER_THRESHOLD
    else ("NEEDS_COACHING" if x < COACHING_THRESHOLD else "STANDARD"))

high_performers = op_scorecard[op_scorecard["performance_flag"]=="HIGH_PERFORMER"]
coaching        = op_scorecard[op_scorecard["performance_flag"]=="NEEDS_COACHING"]

print(f"\n   HIGH PERFORMERS ({HIGH_PERFORMER_THRESHOLD}%+):")
if len(high_performers) > 0:
    print(high_performers[["Operator_ID","Warehouse_ID","overall_accuracy_pct","total_tasks","trend_direction"]].to_string(index=False))
else:
    print("   None above threshold in this dataset.")

print(f"\n   NEEDS COACHING (<{COACHING_THRESHOLD}%):")
if len(coaching) > 0:
    print(coaching[["Operator_ID","Warehouse_ID","overall_accuracy_pct","total_errors","trend_direction"]].to_string(index=False))
else:
    print("   No operators below coaching threshold — all operators meet minimum standard.")

# ── Accuracy by shift per operator ───────────────────────────────────────────
print("\n── D. Shift-Level Accuracy for Bottom 10 Operators")

bottom10_ids = op_scorecard.nsmallest(10,"overall_accuracy_pct")[["Operator_ID","Warehouse_ID"]].values.tolist()
ids_clause = " OR ".join([f"(Operator_ID='{op}' AND Warehouse_ID='{wh}')" for op,wh in bottom10_ids])

op_shift = con.execute(f"""
    SELECT Operator_ID, Warehouse_ID, Shift,
           COUNT(*) AS tasks,
           SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms
    WHERE {ids_clause}
    GROUP BY Operator_ID, Warehouse_ID, Shift
    ORDER BY Operator_ID, Warehouse_ID, accuracy_pct
""").df()
print(op_shift.to_string(index=False))

# ── Figure 13 — Operator accuracy ranked bar ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.patch.set_facecolor("white")
fig.suptitle("Operator Accuracy Ranking by Warehouse", fontsize=12, fontweight="bold", color=DHL_DARK)

for ax, wh in zip(axes, ["DHL-WH-IL02","DHL-WH-NJ01","DHL-WH-TX03"]):
    df = op_scorecard[op_scorecard["Warehouse_ID"]==wh].sort_values("overall_accuracy_pct")
    colors = [DHL_RED if v < COACHING_THRESHOLD else ("#FFCC00" if v < 99.0 else ("#4CAF50" if v < HIGH_PERFORMER_THRESHOLD else "#1565C0")) for v in df["overall_accuracy_pct"]]
    ax.barh(range(len(df)), df["overall_accuracy_pct"]-98.0, color=colors, height=0.7, edgecolor="white")
    ax.axvline(99.0-98.0, color=DHL_RED, linestyle="--", linewidth=1.5, label="SLA 99%")
    ax.axvline(HIGH_PERFORMER_THRESHOLD-98.0, color="#1565C0", linestyle="--", linewidth=1, label="High Perf")
    ax.set_yticks([])
    ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])
    ax.set_xticklabels(["98.0","98.5","99.0","99.5","100.0"], fontsize=7)
    ax.legend(fontsize=7)
    style_ax(ax, wh.replace("DHL-WH-","WH-") + f" ({len(df)} operators)", "Accuracy %", "Operator")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "13_operator_accuracy_ranked.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 13_operator_accuracy_ranked.png")

# ── Figure 14 — Top 5 vs Bottom 5 operators (grouped by warehouse) ───────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.patch.set_facecolor("white")
fig.suptitle("Top 5 vs Bottom 5 Operators by Accuracy — By Warehouse", fontsize=12, fontweight="bold", color=DHL_DARK)

for ax, wh in zip(axes, ["DHL-WH-IL02","DHL-WH-NJ01","DHL-WH-TX03"]):
    df = op_scorecard[op_scorecard["Warehouse_ID"]==wh].sort_values("overall_accuracy_pct", ascending=False)
    top5    = df.head(5)
    bottom5 = df.tail(5)
    combined = pd.concat([top5, bottom5])
    colors = ["#4CAF50"]*5 + [DHL_RED]*5
    ax.barh(range(10), combined["overall_accuracy_pct"], color=colors, height=0.65, edgecolor="white")
    ax.set_yticks(range(10))
    ax.set_yticklabels(combined["Operator_ID"].tolist(), fontsize=8)
    ax.axvline(99.0, color="#555", linestyle="--", linewidth=1)
    mn = combined["overall_accuracy_pct"].min()
    ax.set_xlim(mn-0.1, combined["overall_accuracy_pct"].max()+0.1)
    style_ax(ax, wh.replace("DHL-WH-","WH-"), "Accuracy %", "Operator")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "14_top_bottom_operators.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 14_top_bottom_operators.png")

# ── Export operator_scorecard.csv ─────────────────────────────────────────────
export_cols = ["accuracy_rank","Operator_ID","Warehouse_ID","total_tasks","overall_accuracy_pct",
               "pick_accuracy_pct","putaway_accuracy_pct","cc_accuracy_pct",
               "avg_task_duration_min","total_picks","total_putaways","total_errors",
               "wrong_sku_errors","wrong_qty_errors","missing_label_errors","damaged_errors",
               "wrong_location_errors","picks_per_hour","h1_accuracy_pct","h2_accuracy_pct",
               "accuracy_delta","trend_direction","performance_flag"]
op_scorecard[export_cols].round(4).to_csv(os.path.join(OUTS, "operator_scorecard.csv"), index=False)
print(f"\n  Exported operator_scorecard.csv ({len(op_scorecard)} rows)")

print("\n" + "="*72)
print("  OPERATOR ANALYSIS COMPLETE")
print(f"  High performers: {len(high_performers)}  |  Needs coaching: {len(coaching)}")
print(f"  Accuracy range: {op_scorecard['overall_accuracy_pct'].min():.2f}% – {op_scorecard['overall_accuracy_pct'].max():.2f}%")
print(f"  Trend — Improving: {trend_summary.get('Improving',0)}  Stable: {trend_summary.get('Stable',0)}  Declining: {trend_summary.get('Declining',0)}")
print("="*72)
