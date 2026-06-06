"""
kpi_calculation.py — Core WMS KPI Calculation and Validation
Project 5: WMS Operational Dashboard — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Calculates all core WMS KPIs at network, warehouse, and shift level.
Flags warehouse-shift combos below threshold.
Exports: outputs/kpi_summary.csv, outputs/kpi_by_warehouse_shift.csv
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import duckdb

warnings.filterwarnings("ignore")

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/05-wms-dashboard/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

# SLA thresholds
PICK_THRESHOLD    = 99.0
PUTAWAY_THRESHOLD = 99.5
CC_THRESHOLD      = 98.5
OVERALL_THRESHOLD = 99.0

DHL_RED   = "#D40511"
DHL_DARK  = "#1A1A1A"
DHL_MID   = "#555555"
DHL_LIGHT = "#F5F5F5"
WH_COLS   = {"DHL-WH-IL02":DHL_RED,"DHL-WH-NJ01":"#FF6B35","DHL-WH-TX03":"#4A90D9"}

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
con.execute(f"CREATE VIEW dd  AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")
con.execute(f"CREATE VIEW inv AS SELECT * FROM read_csv_auto('{DATA}inventory_snapshot.csv')")
con.execute(f"CREATE VIEW sku AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

print("=" * 72)
print("  KPI CALCULATION — ALL LEVELS")
print("=" * 72)

# ── LEVEL 1: Network-wide KPIs ───────────────────────────────────────────────
print("\n── LEVEL 1: Network-Wide KPIs")

net = con.execute("""
    SELECT
        COUNT(*)                                                    AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_compliance_pct,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0,0) AS picks_per_labour_hour,
        AVG(CASE WHEN Task_Type='Pick' THEN Duration_Min END)       AS avg_pick_duration_min,
        AVG(CASE WHEN Task_Type='Putaway' THEN Duration_Min END)    AS avg_putaway_duration_min,
        AVG(CASE WHEN Task_Type='Cycle Count' THEN Duration_Min END) AS avg_cc_duration_min,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)     AS total_errors,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms
""").df()

print(net.T.to_string(header=False))

# ── LEVEL 2: Per Warehouse KPIs ─────────────────────────────────────────────
print("\n── LEVEL 2: Per Warehouse KPIs")

wh_kpi = con.execute("""
    SELECT
        Warehouse_ID,
        COUNT(*)                                                    AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_compliance_pct,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0,0) AS picks_per_labour_hour,
        AVG(CASE WHEN Task_Type='Pick' THEN Duration_Min END)       AS avg_pick_duration_min,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms
    GROUP BY Warehouse_ID
    ORDER BY Warehouse_ID
""").df()

print(wh_kpi.to_string(index=False))

# ── LEVEL 3: Per Warehouse × Shift KPIs ──────────────────────────────────────
print("\n── LEVEL 3: Per Warehouse × Shift KPIs")

ws_kpi = con.execute("""
    SELECT
        Warehouse_ID,
        Shift,
        COUNT(*)                                                    AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_compliance_pct,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy_pct,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0,0) AS picks_per_labour_hour
    FROM wms
    GROUP BY Warehouse_ID, Shift
    ORDER BY Warehouse_ID, Shift
""").df()

print(ws_kpi.to_string(index=False))

# ── Threshold Flagging ────────────────────────────────────────────────────────
print("\n── Threshold Flagging (Warehouse × Shift)")

ws_kpi["pick_status"]   = ws_kpi["pick_accuracy_pct"].apply(
    lambda x: "GREEN" if x>=PICK_THRESHOLD else ("AMBER" if x>=(PICK_THRESHOLD-0.5) else "RED"))
ws_kpi["putaway_status"] = ws_kpi["putaway_compliance_pct"].apply(
    lambda x: "GREEN" if x>=PUTAWAY_THRESHOLD else ("AMBER" if x>=(PUTAWAY_THRESHOLD-0.5) else "RED"))
ws_kpi["cc_status"]     = ws_kpi["cc_accuracy_pct"].apply(
    lambda x: "GREEN" if x>=CC_THRESHOLD else ("AMBER" if x>=(CC_THRESHOLD-0.5) else "RED"))

flagged = ws_kpi[(ws_kpi["pick_status"]!="GREEN")|(ws_kpi["putaway_status"]!="GREEN")|(ws_kpi["cc_status"]!="GREEN")]
print(f"   Flagged combos (any metric not GREEN): {len(flagged)}")
if len(flagged) > 0:
    print(flagged[["Warehouse_ID","Shift","pick_accuracy_pct","pick_status","putaway_compliance_pct","putaway_status","cc_accuracy_pct","cc_status"]].to_string(index=False))
else:
    print("   All warehouse-shift combinations meet SLA thresholds.")

# ── OTIF Contribution ─────────────────────────────────────────────────────────
print("\n── OTIF / Stockout Correlation with Pick Accuracy")

pick_monthly = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS year_month,
           Warehouse_ID,
           SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct
    FROM wms
    GROUP BY year_month, Warehouse_ID
""").df()

stockout_monthly = con.execute("""
    SELECT strftime(Date,'%Y-%m') AS year_month, Warehouse_ID,
           AVG(Stockout_Flag)*100 AS stockout_rate_pct
    FROM dd
    GROUP BY year_month, Warehouse_ID
""").df()

merged = pick_monthly.merge(stockout_monthly, on=["year_month","Warehouse_ID"])
corr = merged["pick_accuracy_pct"].corr(merged["stockout_rate_pct"])
print(f"   Pick accuracy ↔ stockout rate correlation (Pearson): {corr:.4f}")
print("   (Negative correlation = higher accuracy → lower stockouts)")

# ── Inventory Record Accuracy ─────────────────────────────────────────────────
print("\n── Inventory Record Accuracy (from inventory_snapshot)")

ira = con.execute("""
    SELECT
        Warehouse_ID,
        COUNT(*)                                                    AS total_records,
        SUM(ABS(On_Hand_Qty - Available_Qty - Committed_Qty))       AS total_variance,
        AVG(ABS(On_Hand_Qty - Available_Qty - Committed_Qty))       AS avg_variance_units,
        SUM(CASE WHEN ABS(On_Hand_Qty - Available_Qty - Committed_Qty) = 0 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS ira_pct
    FROM inv
    GROUP BY Warehouse_ID
    ORDER BY Warehouse_ID
""").df()

print(ira.to_string(index=False))
print(f"\n   Network IRA: {ira['ira_pct'].mean():.2f}%")

# ── Average Task Duration by Type and Warehouse ──────────────────────────────
print("\n── Average Task Duration by Type and Warehouse")

task_dur = con.execute("""
    SELECT Warehouse_ID, Task_Type, AVG(Duration_Min) AS avg_min,
           STDDEV(Duration_Min) AS std_min, COUNT(*) AS n
    FROM wms GROUP BY Warehouse_ID, Task_Type ORDER BY Warehouse_ID, avg_min DESC
""").df()
print(task_dur.to_string(index=False))

# ── Figure 11: KPI scorecard bar chart ──────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
fig.patch.set_facecolor("white")
fig.suptitle("Warehouse KPI Comparison — All Three Warehouses", fontsize=12, fontweight="bold", color=DHL_DARK)

metrics  = ["pick_accuracy_pct","putaway_compliance_pct","cc_accuracy_pct"]
labels   = ["Pick Accuracy %","Putaway Compliance %","CC Accuracy %"]
thresholds = [PICK_THRESHOLD, PUTAWAY_THRESHOLD, CC_THRESHOLD]

for ax, col, lbl, thr in zip(axes, metrics, labels, thresholds):
    vals = wh_kpi[col].tolist()
    whs  = [w.replace("DHL-WH-","WH-") for w in wh_kpi["Warehouse_ID"]]
    bar_colors = [DHL_RED if v < thr else ("#FFCC00" if v < thr+0.5 else "#4CAF50") for v in vals]
    bars = ax.bar(whs, vals, color=bar_colors, edgecolor="white", width=0.5)
    ax.axhline(thr, color=DHL_RED, linestyle="--", linewidth=1.5, alpha=0.8, label=f"SLA {thr}%")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height(),
                f"{val:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    mn = min(vals+[thr])
    ax.set_ylim(mn - 0.4, max(vals)+0.3)
    ax.legend(fontsize=8)
    style_ax(ax, lbl, "Warehouse", lbl)

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "11_kpi_scorecard.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 11_kpi_scorecard.png")

# ── Figure 12: Monthly KPI trend per warehouse ───────────────────────────────
monthly_wh_kpi = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS year_month, Warehouse_ID,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy_pct,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_pct
    FROM wms GROUP BY year_month, Warehouse_ID ORDER BY year_month, Warehouse_ID
""").df()

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
fig.patch.set_facecolor("white")
for wh, col in WH_COLS.items():
    df = monthly_wh_kpi[monthly_wh_kpi["Warehouse_ID"]==wh]
    axes[0].plot(range(len(df)), df["pick_accuracy_pct"], color=col, linewidth=1.8, label=wh.replace("DHL-WH-","WH-"), marker="o", markersize=2.5)
    axes[1].plot(range(len(df)), df["putaway_pct"], color=col, linewidth=1.8, label=wh.replace("DHL-WH-","WH-"), marker="o", markersize=2.5)
for ax, thr, lbl in zip(axes, [PICK_THRESHOLD, PUTAWAY_THRESHOLD], ["Pick Accuracy %","Putaway Compliance %"]):
    ax.axhline(thr, color="#555", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xticks(range(0,24,4))
    months = monthly_wh_kpi["year_month"].unique()
    ax.set_xticklabels(months[::4], rotation=20, fontsize=7)
    ax.legend(fontsize=8)
    style_ax(ax, f"{lbl} — Monthly by Warehouse", "Month", lbl)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "12_monthly_kpi_by_warehouse.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 12_monthly_kpi_by_warehouse.png")

# ── Export KPI CSVs ──────────────────────────────────────────────────────────
# kpi_summary.csv — network + warehouse level
net_row = {"Level":"Network","Warehouse_ID":"ALL","Shift":"ALL",
           "total_tasks":int(net["total_tasks"].iloc[0]),
           "pick_accuracy_pct":round(net["pick_accuracy_pct"].iloc[0],4),
           "putaway_compliance_pct":round(net["putaway_compliance_pct"].iloc[0],4),
           "cc_accuracy_pct":round(net["cc_accuracy_pct"].iloc[0],4),
           "overall_accuracy_pct":round(net["overall_accuracy_pct"].iloc[0],4),
           "picks_per_labour_hour":round(net["picks_per_labour_hour"].iloc[0],3),
           "error_rate_pct":round(net["error_rate_pct"].iloc[0],4),
           "pick_status":"GREEN","putaway_status":"GREEN","cc_status":"GREEN"}

wh_rows = wh_kpi.copy()
wh_rows["Level"] = "Warehouse"
wh_rows["Shift"] = "ALL"
wh_rows["pick_status"] = wh_rows["pick_accuracy_pct"].apply(lambda x: "GREEN" if x>=PICK_THRESHOLD else ("AMBER" if x>=(PICK_THRESHOLD-0.5) else "RED"))
wh_rows["putaway_status"] = wh_rows["putaway_compliance_pct"].apply(lambda x: "GREEN" if x>=PUTAWAY_THRESHOLD else ("AMBER" if x>=(PUTAWAY_THRESHOLD-0.5) else "RED"))
wh_rows["cc_status"] = wh_rows["cc_accuracy_pct"].apply(lambda x: "GREEN" if x>=CC_THRESHOLD else ("AMBER" if x>=(CC_THRESHOLD-0.5) else "RED"))

summary_df = pd.concat([pd.DataFrame([net_row]), wh_rows], ignore_index=True)
for col in ["pick_accuracy_pct","putaway_compliance_pct","cc_accuracy_pct","overall_accuracy_pct","picks_per_labour_hour","error_rate_pct"]:
    if col in summary_df.columns:
        summary_df[col] = summary_df[col].round(4)
summary_df.to_csv(os.path.join(OUTS, "kpi_summary.csv"), index=False)
print(f"\n  Exported kpi_summary.csv ({len(summary_df)} rows)")

ws_kpi["Level"] = "Warehouse-Shift"
ws_kpi.to_csv(os.path.join(OUTS, "kpi_by_warehouse_shift.csv"), index=False)
print(f"  Exported kpi_by_warehouse_shift.csv ({len(ws_kpi)} rows)")

print("\n" + "="*72)
print("  KPI CALCULATION COMPLETE")
print(f"  Network pick accuracy:    {net['pick_accuracy_pct'].iloc[0]:.3f}%  (SLA: {PICK_THRESHOLD}%)")
print(f"  Network putaway comp:     {net['putaway_compliance_pct'].iloc[0]:.3f}%  (SLA: {PUTAWAY_THRESHOLD}%)")
print(f"  Network CC accuracy:      {net['cc_accuracy_pct'].iloc[0]:.3f}%  (SLA: {CC_THRESHOLD}%)")
print(f"  Picks per labour hour:    {net['picks_per_labour_hour'].iloc[0]:.2f}")
print(f"  Inventory Record Acc:     {ira['ira_pct'].mean():.2f}%")
print(f"  Stockout-Pick corr:       {corr:.4f}")
print(f"  Flagged WH-Shift combos:  {len(flagged)}")
print("="*72)
