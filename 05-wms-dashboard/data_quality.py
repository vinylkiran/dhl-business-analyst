"""
data_quality.py — Data Quality Monitoring Layer
Project 5: WMS Operational Dashboard — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Identifies SKUs with consistently high error rates, location/zone patterns,
operator shift-specific anomalies, and error code clustering.
Exports: outputs/data_quality_flags.csv
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
con.execute(f"CREATE VIEW sku AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

print("=" * 72)
print("  DATA QUALITY MONITORING LAYER")
print("=" * 72)

all_flags = []

# ── DQ-1: SKUs with consistently high error rates ────────────────────────────
print("\n── DQ-1: SKUs with Consistently High Error Rates (≥2 months above 2%)")

sku_monthly_err = con.execute("""
    SELECT
        w.SKU_ID,
        s.Category,
        s.ABC_Class,
        s.Storage_Type,
        strftime(Task_Date,'%Y-%m')                                AS year_month,
        COUNT(*)                                                    AS task_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)    AS error_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms w
    JOIN sku s ON w.SKU_ID = s.SKU_ID
    GROUP BY w.SKU_ID, s.Category, s.ABC_Class, s.Storage_Type, year_month
    HAVING task_count >= 3
""").df()

# SKUs with error rate > 2% in 2 or more months
sku_high_months = (
    sku_monthly_err[sku_monthly_err["error_rate_pct"] > 2.0]
    .groupby(["SKU_ID","Category","ABC_Class","Storage_Type"])
    .agg(months_above_threshold=("year_month","count"),
         avg_error_rate=("error_rate_pct","mean"),
         max_error_rate=("error_rate_pct","max"))
    .reset_index()
    .query("months_above_threshold >= 2")
    .sort_values("months_above_threshold", ascending=False)
)

print(f"   SKUs with ≥2 months above 2% error rate: {len(sku_high_months)}")
print(sku_high_months.head(15).to_string(index=False))

for _, row in sku_high_months.head(20).iterrows():
    all_flags.append({
        "flag_type": "HIGH_ERROR_SKU",
        "entity_id": row["SKU_ID"],
        "entity_type": "SKU",
        "warehouse_id": "ALL",
        "shift": "ALL",
        "detail": f"{row['Category']} ABC-{row['ABC_Class']} — {row['months_above_threshold']} months above 2% error rate",
        "severity": "HIGH" if row["months_above_threshold"] >= 4 else "MEDIUM",
        "metric_value": round(row["avg_error_rate"], 2),
        "threshold": 2.0
    })

# ── DQ-2: Task type zones with above-average error rates ─────────────────────
print("\n── DQ-2: Zone Proxy Error Rate Patterns")

zone_err = con.execute("""
    SELECT
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END                                                         AS zone_proxy,
        Task_Type,
        Warehouse_ID,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct,
        COUNT(*)                                                    AS task_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)    AS error_count
    FROM wms
    GROUP BY Task_Type, Warehouse_ID
    ORDER BY error_rate_pct DESC
""").df()

net_err_rate = con.execute("SELECT AVG(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100 FROM wms").fetchone()[0]
high_error_zones = zone_err[zone_err["error_rate_pct"] > net_err_rate * 1.5]
print(f"   Network avg error rate: {net_err_rate:.3f}%")
print(f"   Zones >1.5× network avg: {len(high_error_zones)}")
print(high_error_zones.to_string(index=False))

for _, row in high_error_zones.iterrows():
    all_flags.append({
        "flag_type": "HIGH_ERROR_ZONE",
        "entity_id": row["zone_proxy"],
        "entity_type": "Zone",
        "warehouse_id": row["Warehouse_ID"],
        "shift": "ALL",
        "detail": f"{row['zone_proxy']} ({row['Task_Type']}) — {row['error_rate_pct']:.2f}% vs network avg {net_err_rate:.2f}%",
        "severity": "HIGH" if row["error_rate_pct"] > net_err_rate * 2 else "MEDIUM",
        "metric_value": round(row["error_rate_pct"], 3),
        "threshold": round(net_err_rate * 1.5, 3)
    })

# ── DQ-3: Operator shift-specific error spikes ────────────────────────────────
print("\n── DQ-3: Operator Error Rate by Shift (Spike Detection)")

op_shift_err = con.execute("""
    SELECT
        Operator_ID,
        Warehouse_ID,
        Shift,
        COUNT(*)                                                    AS task_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)    AS error_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms
    GROUP BY Operator_ID, Warehouse_ID, Shift
    HAVING task_count >= 50
    ORDER BY error_rate_pct DESC
""").df()

# Flag operators whose worst-shift error rate is >2× their best-shift rate
op_shift_range = (
    op_shift_err.groupby(["Operator_ID","Warehouse_ID"])
    .agg(max_err=("error_rate_pct","max"), min_err=("error_rate_pct","min"), shifts=("Shift","count"))
    .reset_index()
)
op_shift_range["err_ratio"] = op_shift_range.apply(
    lambda r: r["max_err"] / r["min_err"] if r["min_err"] > 0 else 0, axis=1)
spike_ops = op_shift_range[op_shift_range["err_ratio"] > 2.0].sort_values("err_ratio", ascending=False)
print(f"   Operators with >2× worst/best shift error ratio: {len(spike_ops)}")
print(spike_ops.head(15).to_string(index=False))

for _, row in spike_ops.head(10).iterrows():
    all_flags.append({
        "flag_type": "SHIFT_ERROR_SPIKE",
        "entity_id": row["Operator_ID"],
        "entity_type": "Operator",
        "warehouse_id": row["Warehouse_ID"],
        "shift": "Variable",
        "detail": f"Max error rate {row['max_err']:.2f}% vs min {row['min_err']:.2f}% — ratio {row['err_ratio']:.1f}×",
        "severity": "MEDIUM" if row["err_ratio"] < 4 else "HIGH",
        "metric_value": round(row["err_ratio"], 2),
        "threshold": 2.0
    })

# ── DQ-4: WRONG_SKU error clustering by task type ────────────────────────────
print("\n── DQ-4: Error Code Clustering by Task Type and Category")

wrong_sku_by_task = con.execute("""
    SELECT Task_Type,
           SUM(CASE WHEN Error_Code='WRONG_SKU' THEN 1 ELSE 0 END) AS wrong_sku,
           SUM(CASE WHEN Error_Code='DAMAGED' THEN 1 ELSE 0 END)    AS damaged,
           SUM(CASE WHEN Error_Code='WRONG_QTY' THEN 1 ELSE 0 END)  AS wrong_qty,
           COUNT(*)                                                  AS total_tasks,
           SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms GROUP BY Task_Type ORDER BY error_rate_pct DESC
""").df()
print("Error clustering by Task Type:")
print(wrong_sku_by_task.to_string(index=False))

damaged_by_cat = con.execute("""
    SELECT w.Category,
           SUM(CASE WHEN Error_Code='DAMAGED' THEN 1 ELSE 0 END)*100.0/COUNT(*) AS damaged_rate_pct,
           SUM(CASE WHEN Error_Code='DAMAGED' THEN 1 ELSE 0 END)                AS damaged_count,
           COUNT(*)                                                              AS total_tasks
    FROM wms w GROUP BY w.Category ORDER BY damaged_rate_pct DESC
""").df()
print("\nDAMAGED error rate by product category:")
print(damaged_by_cat.to_string(index=False))

# Highest damaged rate category
if len(damaged_by_cat) > 0:
    top_cat = damaged_by_cat.iloc[0]
    all_flags.append({
        "flag_type": "DAMAGED_CATEGORY_CLUSTER",
        "entity_id": top_cat["Category"],
        "entity_type": "Category",
        "warehouse_id": "ALL",
        "shift": "ALL",
        "detail": f"Highest DAMAGED error rate: {top_cat['damaged_rate_pct']:.3f}% ({top_cat['damaged_count']} errors / {top_cat['total_tasks']} tasks)",
        "severity": "LOW",
        "metric_value": round(top_cat["damaged_rate_pct"], 3),
        "threshold": round(damaged_by_cat["damaged_rate_pct"].mean(), 3)
    })

# ── DQ-5: SKUs never picked in last 6 months (potential ghost inventory) ─────
print("\n── DQ-5: Slow-Moving / Ghost Inventory Check (No picks in last 6 months)")

ghost_skus = con.execute("""
    SELECT s.SKU_ID, s.Category, s.ABC_Class, s.Active_Flag,
           MAX(w.Task_Date) AS last_pick_date,
           DATEDIFF('day', MAX(w.Task_Date), '2023-12-31') AS days_since_last_pick
    FROM sku s
    LEFT JOIN wms w ON s.SKU_ID = w.SKU_ID AND w.Task_Type = 'Pick'
    WHERE s.Active_Flag = 1
    GROUP BY s.SKU_ID, s.Category, s.ABC_Class, s.Active_Flag
    HAVING days_since_last_pick > 180 OR last_pick_date IS NULL
    ORDER BY days_since_last_pick DESC NULLS FIRST
""").df()

print(f"   Active SKUs with no pick in last 180 days: {len(ghost_skus)}")
print(ghost_skus.head(10).to_string(index=False))

for _, row in ghost_skus.head(10).iterrows():
    all_flags.append({
        "flag_type": "SLOW_MOVING_SKU",
        "entity_id": row["SKU_ID"],
        "entity_type": "SKU",
        "warehouse_id": "ALL",
        "shift": "ALL",
        "detail": f"{row['Category']} ABC-{row['ABC_Class']} — last pick {row['last_pick_date']} ({row['days_since_last_pick']} days ago)",
        "severity": "LOW",
        "metric_value": row["days_since_last_pick"],
        "threshold": 180
    })

# ── Figure 15: Error pattern heatmap (task type × error code) ────────────────
err_pivot = con.execute("""
    SELECT Task_Type, Error_Code, COUNT(*) AS cnt
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY Task_Type, Error_Code
""").df()
pivot_err = err_pivot.pivot_table(index="Task_Type", columns="Error_Code", values="cnt", fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor("white")
import matplotlib.colors as mcolors
cmap = plt.cm.YlOrRd
im = ax.imshow(pivot_err.values, aspect="auto", cmap=cmap)
plt.colorbar(im, ax=ax, label="Error Count")
ax.set_xticks(range(len(pivot_err.columns)))
ax.set_xticklabels(pivot_err.columns, fontsize=9)
ax.set_yticks(range(len(pivot_err.index)))
ax.set_yticklabels(pivot_err.index, fontsize=9)
for r in range(len(pivot_err.index)):
    for c in range(len(pivot_err.columns)):
        val = int(pivot_err.values[r,c])
        if val > 0:
            ax.text(c,r,str(val),ha="center",va="center",fontsize=8.5,fontweight="bold",
                    color="white" if val > pivot_err.values.max()*0.6 else DHL_DARK)
ax.set_title("Error Count Heatmap — Task Type × Error Code", fontsize=12, fontweight="bold", color=DHL_DARK)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "15_error_pattern_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 15_error_pattern_heatmap.png")

# ── Figure 16: Monthly error rate trend by warehouse ─────────────────────────
monthly_err = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS year_month, Warehouse_ID,
           SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms GROUP BY year_month, Warehouse_ID ORDER BY year_month, Warehouse_ID
""").df()

fig, ax = plt.subplots(figsize=(12, 4))
fig.patch.set_facecolor("white")
WH_COLS = {"DHL-WH-IL02":DHL_RED,"DHL-WH-NJ01":"#FF6B35","DHL-WH-TX03":"#4A90D9"}
for wh, col in WH_COLS.items():
    df = monthly_err[monthly_err["Warehouse_ID"]==wh]
    ax.plot(range(len(df)), df["error_rate_pct"], color=col, linewidth=1.8, label=wh.replace("DHL-WH-","WH-"), marker="o", markersize=3)
ax.set_xticks(range(0,24,4))
ax.set_xticklabels(monthly_err["year_month"].unique()[::4], rotation=20, fontsize=8)
ax.legend(fontsize=9)
style_ax(ax, "Monthly Error Rate by Warehouse (%)", "Month", "Error Rate %")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "16_monthly_error_rate.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 16_monthly_error_rate.png")

# ── Export data_quality_flags.csv ────────────────────────────────────────────
flags_df = pd.DataFrame(all_flags)
flags_df["flagged_at"] = pd.Timestamp.now().strftime("%Y-%m-%d")
flags_df.to_csv(os.path.join(OUTS, "data_quality_flags.csv"), index=False)
print(f"\n  Exported data_quality_flags.csv ({len(flags_df)} flags)")

flag_summary = flags_df.groupby(["flag_type","severity"])["entity_id"].count().reset_index()
print(flag_summary.to_string(index=False))

print("\n" + "="*72)
print("  DATA QUALITY MONITORING COMPLETE")
print(f"  Total flags:              {len(flags_df)}")
print(f"  HIGH severity:            {(flags_df['severity']=='HIGH').sum()}")
print(f"  MEDIUM severity:          {(flags_df['severity']=='MEDIUM').sum()}")
print(f"  LOW severity:             {(flags_df['severity']=='LOW').sum()}")
print(f"  High-error SKUs flagged:  {len(sku_high_months)}")
print(f"  Slow-moving SKUs:         {len(ghost_skus)}")
print(f"  Operator shift spikes:    {len(spike_ops)}")
print("="*72)
