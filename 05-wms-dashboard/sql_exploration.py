"""
sql_exploration.py — WMS Operational Dashboard: SQL Exploration
Project 5: WMS Operational Dashboard — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

10 DuckDB blocks covering all core WMS operational dimensions.
Prints results to stdout and saves key figures to figures/.
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import duckdb

warnings.filterwarnings("ignore")

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/05-wms-dashboard/")
FIGS    = os.path.join(PROJECT, "figures")
OUTS    = os.path.join(PROJECT, "outputs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUTS, exist_ok=True)

DHL_RED   = "#D40511"
DHL_YELLOW= "#FFCC00"
DHL_DARK  = "#1A1A1A"
DHL_MID   = "#555555"
DHL_LIGHT = "#F5F5F5"

SHIFT_COLS = {
    "Morning 06:00-14:00" : "#FFCC00",
    "Afternoon 14:00-22:00": "#FF6B35",
    "Night 22:00-06:00"   : "#4A90D9",
}
WH_COLS = {"DHL-WH-IL02": DHL_RED, "DHL-WH-NJ01": "#FF6B35", "DHL-WH-TX03": "#4A90D9"}

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
con.execute(f"CREATE VIEW dd  AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")
con.execute(f"CREATE VIEW inv AS SELECT * FROM read_csv_auto('{DATA}inventory_snapshot.csv')")

print("=" * 72)
print("  PROJECT 5 — WMS OPERATIONAL DASHBOARD: SQL EXPLORATION")
print("=" * 72)

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 1 — DAILY TASK VOLUME BY WAREHOUSE AND TASK TYPE (MONTHLY AGGREGATED)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 1 — MONTHLY TASK VOLUME BY WAREHOUSE AND TASK TYPE")
print("="*72)

monthly_vol = con.execute("""
    SELECT
        strftime(Task_Date, '%Y-%m')                               AS year_month,
        Warehouse_ID,
        Task_Type,
        COUNT(*)                                                   AS task_count,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms
    GROUP BY year_month, Warehouse_ID, Task_Type
    ORDER BY year_month, Warehouse_ID, task_count DESC
""").df()

summary = con.execute("""
    SELECT
        Warehouse_ID,
        Task_Type,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct,
        AVG(Duration_Min)                                          AS avg_duration_min
    FROM wms
    GROUP BY Warehouse_ID, Task_Type
    ORDER BY Warehouse_ID, total_tasks DESC
""").df()
print(summary.to_string(index=False))

# Figure 01 — Monthly task volume trend per warehouse
fig, axes = plt.subplots(1, 3, figsize=(16, 4), sharey=True)
fig.patch.set_facecolor("white")
for ax, wh in zip(axes, ["DHL-WH-IL02","DHL-WH-NJ01","DHL-WH-TX03"]):
    df = monthly_vol[monthly_vol["Warehouse_ID"]==wh].groupby("year_month")["task_count"].sum().reset_index()
    ax.plot(df["year_month"], df["task_count"], color=WH_COLS[wh], linewidth=2, marker="o", markersize=3)
    ax.fill_between(range(len(df)), df["task_count"], alpha=0.12, color=WH_COLS[wh])
    ax.set_xticks(range(0,len(df),6))
    ax.set_xticklabels(df["year_month"].iloc[::6], rotation=30, fontsize=7)
    style_ax(ax, wh.replace("DHL-WH-","WH-"), "Month", "Tasks")
fig.suptitle("Monthly Task Volume by Warehouse (Jan 2022 – Dec 2023)",
             fontsize=13, fontweight="bold", color=DHL_DARK)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "01_monthly_task_volume.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 01_monthly_task_volume.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 2 — PICK ACCURACY BY WAREHOUSE, SHIFT, AND MONTH
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 2 — PICK ACCURACY BY WAREHOUSE, SHIFT AND MONTH")
print("="*72)

pick_acc = con.execute("""
    SELECT
        Warehouse_ID,
        Shift,
        COUNT(*)                                                   AS total_picks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)          AS accurate_picks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)    AS error_count
    FROM wms WHERE Task_Type='Pick'
    GROUP BY Warehouse_ID, Shift
    ORDER BY Warehouse_ID, Shift
""").df()
print(pick_acc.to_string(index=False))

pick_monthly = con.execute("""
    SELECT
        strftime(Task_Date,'%Y-%m')                               AS year_month,
        Warehouse_ID,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms WHERE Task_Type='Pick'
    GROUP BY year_month, Warehouse_ID
    ORDER BY year_month, Warehouse_ID
""").df()

# Figure 02 — Pick accuracy monthly trend
fig, ax = plt.subplots(figsize=(14, 4))
fig.patch.set_facecolor("white")
for wh, col in WH_COLS.items():
    df = pick_monthly[pick_monthly["Warehouse_ID"]==wh].copy()
    ax.plot(df["year_month"], df["accuracy_pct"], color=col, linewidth=2, label=wh.replace("DHL-WH-","WH-"), marker="o", markersize=3)
ax.axhline(99.0, color=DHL_RED, linestyle="--", linewidth=1, alpha=0.7, label="SLA threshold 99.0%")
ax.set_xticks(range(0,24,3))
ax.set_xticklabels(pick_monthly["year_month"].unique()[::3], rotation=30, fontsize=8)
ax.legend(fontsize=9)
style_ax(ax, "Pick Accuracy % by Warehouse — Monthly Trend", "Month", "Accuracy %")
ax.set_ylim(98.5, 100.0)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "02_pick_accuracy_trend.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 02_pick_accuracy_trend.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 3 — PUTAWAY AND CYCLE COUNT ACCURACY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 3 — PUTAWAY AND CYCLE COUNT ACCURACY BY WAREHOUSE + SHIFT")
print("="*72)

task_acc = con.execute("""
    SELECT
        Task_Type,
        Warehouse_ID,
        Shift,
        COUNT(*)                                                   AS task_count,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms
    WHERE Task_Type IN ('Putaway','Cycle Count','Replenishment')
    GROUP BY Task_Type, Warehouse_ID, Shift
    ORDER BY Task_Type, Warehouse_ID, Shift
""").df()
print(task_acc.to_string(index=False))

# Figure 03 — Multi-task accuracy heatmap (warehouse × task type)
task_wh = con.execute("""
    SELECT
        Warehouse_ID,
        Task_Type,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms
    GROUP BY Warehouse_ID, Task_Type
""").df()
pivot = task_wh.pivot_table(index="Task_Type", columns="Warehouse_ID", values="accuracy_pct")
task_order = ["Pick","Putaway","Replenishment","Cycle Count","Transfer","Receiving"]
pivot = pivot.reindex([t for t in task_order if t in pivot.index])

fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor("white")
import matplotlib.colors as mcolors
cmap = plt.cm.RdYlGn
norm = mcolors.Normalize(vmin=97.5, vmax=100.5)
im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, norm=norm)
plt.colorbar(im, ax=ax, label="Accuracy %")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([c.replace("DHL-WH-","WH-") for c in pivot.columns], fontsize=9)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
for r in range(len(pivot.index)):
    for c in range(len(pivot.columns)):
        val = pivot.values[r,c]
        if not np.isnan(val):
            ax.text(c,r,f"{val:.2f}%",ha="center",va="center",fontsize=8,fontweight="bold",
                    color="white" if val < 99 else DHL_DARK)
ax.set_title("Task Accuracy % — Warehouse × Task Type", fontsize=12, fontweight="bold", color=DHL_DARK)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "03_task_accuracy_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 03_task_accuracy_heatmap.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 4 — OPERATOR PERFORMANCE RANKING
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 4 — OPERATOR PERFORMANCE RANKING")
print("="*72)

op_rank = con.execute("""
    SELECT
        Operator_ID,
        Warehouse_ID,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy,
        AVG(Duration_Min)                                          AS avg_duration_min,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)   AS total_errors
    FROM wms
    GROUP BY Operator_ID, Warehouse_ID
    ORDER BY overall_accuracy DESC
""").df()
print("── Top 10 operators:")
print(op_rank.head(10).to_string(index=False))
print("\n── Bottom 10 operators:")
print(op_rank.tail(10).to_string(index=False))
print(f"\n   Total operators: {len(op_rank)}")
print(f"   Below 99% accuracy: {(op_rank['overall_accuracy']<99).sum()}")
print(f"   Below 98.5%: {(op_rank['overall_accuracy']<98.5).sum()}")

# Figure 04 — Operator accuracy distribution
fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor("white")
ax.hist(op_rank["overall_accuracy"], bins=25, color=DHL_RED, edgecolor="white", alpha=0.8)
ax.axvline(99.0, color="#FFCC00", linestyle="--", linewidth=2, label="SLA 99.0%")
ax.axvline(98.5, color="#FF6B35", linestyle="--", linewidth=2, label="Coaching threshold 98.5%")
ax.axvline(op_rank["overall_accuracy"].mean(), color=DHL_DARK, linestyle="-", linewidth=1.5, label=f"Mean {op_rank['overall_accuracy'].mean():.2f}%")
ax.legend(fontsize=9)
style_ax(ax, "Operator Accuracy Distribution (Network, All Task Types)", "Accuracy %", "Operator Count")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "04_operator_accuracy_dist.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 04_operator_accuracy_dist.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 5 — ERROR CODE FREQUENCY BY WAREHOUSE
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 5 — ERROR CODE FREQUENCY BY WAREHOUSE")
print("="*72)

error_wh = con.execute("""
    SELECT
        Warehouse_ID,
        COALESCE(Error_Code,'No Error')                            AS Error_Code,
        COUNT(*)                                                   AS count,
        COUNT(*)*100.0/SUM(COUNT(*)) OVER (PARTITION BY Warehouse_ID) AS pct
    FROM wms
    WHERE Error_Code IS NOT NULL
    GROUP BY Warehouse_ID, Error_Code
    ORDER BY Warehouse_ID, count DESC
""").df()
print(error_wh.to_string(index=False))

error_total = con.execute("""
    SELECT Error_Code, COUNT(*) cnt,
           COUNT(*)*100.0/SUM(COUNT(*)) OVER () AS pct_total
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY Error_Code ORDER BY cnt DESC
""").df()
print("\n── Network-wide error code distribution:")
print(error_total.to_string(index=False))

# Figure 05 — Error code distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
fig.patch.set_facecolor("white")
colors_err = [DHL_RED,"#FF6B35","#FFCC00","#4A90D9","#7CB342"]
axes[0].pie(error_total["cnt"], labels=error_total["Error_Code"],
            autopct="%1.0f%%", colors=colors_err,
            startangle=90, wedgeprops={"edgecolor":"white","linewidth":1.5})
axes[0].set_title("Network Error Code Distribution", fontsize=12, fontweight="bold", color=DHL_DARK)

wh_names = ["DHL-WH-IL02","DHL-WH-NJ01","DHL-WH-TX03"]
codes = error_total["Error_Code"].tolist()
x = np.arange(len(codes))
w = 0.25
for i, wh in enumerate(wh_names):
    df_wh = error_wh[error_wh["Warehouse_ID"]==wh].set_index("Error_Code")["count"]
    vals = [df_wh.get(c,0) for c in codes]
    axes[1].bar(x+i*w, vals, w, label=wh.replace("DHL-WH-","WH-"), color=list(WH_COLS.values())[i], edgecolor="white")
axes[1].set_xticks(x+w)
axes[1].set_xticklabels(codes, rotation=15, fontsize=8)
axes[1].legend(fontsize=8)
style_ax(axes[1], "Error Count by Code and Warehouse", "Error Code", "Count")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "05_error_code_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 05_error_code_distribution.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 6 — TOP 20 SKUs BY ERROR FREQUENCY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 6 — TOP 20 SKUs BY ERROR FREQUENCY")
print("="*72)

sku_errors = con.execute("""
    SELECT
        w.SKU_ID,
        s.Category,
        s.ABC_Class,
        s.Storage_Type,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN w.Error_Code IS NOT NULL THEN 1 ELSE 0 END) AS error_count,
        SUM(CASE WHEN w.Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms w
    JOIN sku s ON w.SKU_ID = s.SKU_ID
    GROUP BY w.SKU_ID, s.Category, s.ABC_Class, s.Storage_Type
    HAVING error_count > 0
    ORDER BY error_count DESC
    LIMIT 20
""").df()
print(sku_errors.to_string(index=False))

# Figure 06 — Top 20 SKU error horizontal bar
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor("white")
sku_errors_plot = sku_errors.sort_values("error_count")
bar_colors = [{"A":DHL_RED,"B":"#FF6B35","C":"#FFCC00"}.get(c,"#4A90D9") for c in sku_errors_plot["ABC_Class"]]
bars = ax.barh(range(len(sku_errors_plot)), sku_errors_plot["error_count"], color=bar_colors, height=0.65, edgecolor="white")
ax.set_yticks(range(len(sku_errors_plot)))
ax.set_yticklabels([f"{row['SKU_ID']} ({row['Category'][:4]})" for _, row in sku_errors_plot.iterrows()], fontsize=8)
for i,val in enumerate(sku_errors_plot["error_count"]):
    ax.text(val+0.1, i, str(val), va="center", fontsize=8, color=DHL_DARK)
style_ax(ax, "Top 20 SKUs by Error Count (All Task Types, 24 Months)", "Error Count", "SKU")
from matplotlib.patches import Patch
leg = [Patch(facecolor=DHL_RED,label="ABC-A"), Patch(facecolor="#FF6B35",label="ABC-B"), Patch(facecolor="#FFCC00",label="ABC-C")]
ax.legend(handles=leg, fontsize=8, loc="lower right")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "06_top20_sku_errors.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 06_top20_sku_errors.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 7 — SHIFT COMPARISON ACROSS ALL KPIs
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 7 — SHIFT COMPARISON ACROSS ALL KPIs")
print("="*72)

shift_kpi = con.execute("""
    SELECT
        Shift,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_accuracy,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy,
        AVG(Duration_Min)                                          AS avg_duration_min,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            (SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0) AS picks_per_hour
    FROM wms
    GROUP BY Shift
    ORDER BY Shift
""").df()
print(shift_kpi.to_string(index=False))

# Figure 07 — Shift KPI radar-style grouped bar
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.patch.set_facecolor("white")
shifts = shift_kpi["Shift"].tolist()
short_shifts = ["Morning","Afternoon","Night"]
metrics = ["pick_accuracy","putaway_accuracy","cc_accuracy"]
labels  = ["Pick Acc%","Putaway Acc%","CC Acc%"]
x = np.arange(len(metrics))
w = 0.25
for i, (sh, sn) in enumerate(zip(shifts, short_shifts)):
    row = shift_kpi[shift_kpi["Shift"]==sh].iloc[0]
    vals = [row[m] for m in metrics]
    axes[0].bar(x+i*w, vals, w, label=sn, color=list(SHIFT_COLS.values())[i], edgecolor="white")
axes[0].set_xticks(x+w)
axes[0].set_xticklabels(labels, fontsize=9)
axes[0].set_ylim(97.5,100.5)
axes[0].legend(fontsize=8)
style_ax(axes[0],"Accuracy KPIs by Shift","Metric","Accuracy %")

picks_hr = shift_kpi["picks_per_hour"].tolist()
axes[1].bar(short_shifts, picks_hr, color=list(SHIFT_COLS.values()), edgecolor="white", width=0.5)
for i, val in enumerate(picks_hr):
    axes[1].text(i, val+0.1, f"{val:.1f}", ha="center", fontsize=10, fontweight="bold", color=DHL_DARK)
style_ax(axes[1],"Picks per Labour Hour by Shift","Shift","Picks/Hour")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "07_shift_kpi_comparison.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 07_shift_kpi_comparison.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 8 — WEEKEND vs WEEKDAY PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 8 — WEEKEND vs WEEKDAY PERFORMANCE")
print("="*72)

wkd = con.execute("""
    SELECT
        CASE WHEN dayofweek(Task_Date) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy,
        AVG(Duration_Min)                                          AS avg_duration_min,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)   AS error_count,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate_pct
    FROM wms
    GROUP BY day_type
    ORDER BY day_type
""").df()
print(wkd.to_string(index=False))

# Figure 08 — Weekend vs Weekday comparison
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
fig.patch.set_facecolor("white")
fig.suptitle("Weekend vs Weekday Performance Comparison", fontsize=12, fontweight="bold", color=DHL_DARK)
day_types = wkd["day_type"].tolist()
colors_wk = ["#4A90D9","#D40511"]
for ax, metric, lbl in zip(axes,
    ["overall_accuracy","pick_accuracy","avg_duration_min"],
    ["Overall Accuracy %","Pick Accuracy %","Avg Task Duration (min)"]):
    vals = wkd[metric].tolist()
    bars = ax.bar(day_types, vals, color=colors_wk, edgecolor="white", width=0.45)
    mn = min(vals); mx = max(vals)
    ax.set_ylim(mn - (mx-mn)*0.5 if mx-mn > 0.1 else mn-0.5, mx+(mx-mn)*0.5 if mx-mn > 0.1 else mx+0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height(), f"{val:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    style_ax(ax, lbl, "Day Type", lbl)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "08_weekend_vs_weekday.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 08_weekend_vs_weekday.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 9 — MONTHLY TREND OF ALL CORE KPIs
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 9 — MONTHLY KPI TREND (NETWORK LEVEL)")
print("="*72)

monthly_kpi = con.execute("""
    SELECT
        strftime(Task_Date,'%Y-%m')                               AS year_month,
        COUNT(*)                                                   AS total_tasks,
        SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_accuracy,
        SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_accuracy,
        SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_accuracy,
        SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
            NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_accuracy,
        SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
            NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0, 0) AS picks_per_hour
    FROM wms
    GROUP BY year_month
    ORDER BY year_month
""").df()
print(monthly_kpi.to_string(index=False))

# Figure 09 — Monthly KPI trends
fig, axes = plt.subplots(2, 2, figsize=(14, 7))
fig.patch.set_facecolor("white")
fig.suptitle("Monthly KPI Trends — Network Level (Jan 2022 – Dec 2023)",
             fontsize=13, fontweight="bold", color=DHL_DARK)
kpi_plots = [
    ("pick_accuracy",   "Pick Accuracy %",     DHL_RED,   99.0),
    ("putaway_accuracy","Putaway Accuracy %",   "#FF6B35", 99.5),
    ("cc_accuracy",     "Cycle Count Acc %",   "#4A90D9", 98.5),
    ("picks_per_hour",  "Picks per Hour",      "#7CB342", None),
]
for ax, (col, lbl, color, threshold) in zip(axes.flat, kpi_plots):
    ax.plot(monthly_kpi["year_month"], monthly_kpi[col], color=color, linewidth=2, marker="o", markersize=3)
    if threshold:
        ax.axhline(threshold, color=DHL_RED, linestyle="--", linewidth=1, alpha=0.7, label=f"SLA {threshold}%")
        ax.legend(fontsize=8)
    ax.set_xticks(range(0,24,4))
    ax.set_xticklabels(monthly_kpi["year_month"].iloc[::4], rotation=25, fontsize=7)
    style_ax(ax, lbl, "Month", lbl)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "09_monthly_kpi_trends.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 09_monthly_kpi_trends.png")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 10 — INVENTORY ACCURACY AND STOCKOUT CORRELATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*72)
print("  BLOCK 10 — INVENTORY ACCURACY AND STOCKOUT CORRELATION")
print("="*72)

inv_acc = con.execute("""
    SELECT
        Snapshot_Date,
        Warehouse_ID,
        Category,
        COUNT(*)                                                   AS sku_count,
        SUM(Available_Qty)                                         AS total_available,
        SUM(On_Hand_Qty)                                           AS total_on_hand,
        SUM(Committed_Qty)                                         AS total_committed,
        AVG(ABS(On_Hand_Qty - Available_Qty - Committed_Qty))      AS avg_qty_variance,
        SUM(Inventory_Value)                                        AS total_inv_value,
        SUM(CASE WHEN Available_Qty < 0 THEN 1 ELSE 0 END)         AS negative_available_count
    FROM inv
    GROUP BY Snapshot_Date, Warehouse_ID, Category
    ORDER BY Snapshot_Date, Warehouse_ID
""").df()

inv_monthly = con.execute("""
    SELECT
        Snapshot_Date,
        COUNT(*)                                                   AS sku_count,
        AVG(ABS(On_Hand_Qty - Available_Qty - Committed_Qty))      AS avg_variance,
        SUM(Inventory_Value)                                        AS total_value,
        SUM(Available_Qty)                                          AS total_available
    FROM inv
    GROUP BY Snapshot_Date
    ORDER BY Snapshot_Date
""").df()

stockout_monthly = con.execute("""
    SELECT
        strftime(Date,'%Y-%m')                                     AS year_month,
        AVG(Stockout_Flag)*100                                     AS stockout_rate_pct,
        SUM(Quantity_Demanded)                                      AS total_demand,
        SUM(Quantity_Fulfilled)                                     AS total_fulfilled
    FROM dd
    GROUP BY year_month
    ORDER BY year_month
""").df()

print("── Inventory monthly summary:")
print(inv_monthly.head(6).to_string(index=False))
print(f"\n   Avg network variance (On_Hand - Available - Committed): {inv_monthly['avg_variance'].mean():.1f} units")
print(f"   Negative available count (any month): {con.execute('SELECT SUM(CASE WHEN Available_Qty<0 THEN 1 ELSE 0 END) FROM inv').fetchone()[0]}")

print("\n── Stockout monthly summary:")
print(stockout_monthly.head(6).to_string(index=False))
print(f"\n   Avg network stockout rate: {stockout_monthly['stockout_rate_pct'].mean():.2f}%")

# Figure 10 — Inventory value trend + stockout rate
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.patch.set_facecolor("white")

# Left: inventory value trend by warehouse
inv_wh_monthly = con.execute("""
    SELECT Snapshot_Date, Warehouse_ID, SUM(Inventory_Value) AS inv_value
    FROM inv GROUP BY Snapshot_Date, Warehouse_ID ORDER BY Snapshot_Date, Warehouse_ID
""").df()
for wh, col in WH_COLS.items():
    df = inv_wh_monthly[inv_wh_monthly["Warehouse_ID"]==wh]
    axes[0].plot(range(len(df)), df["inv_value"]/1e6, color=col, linewidth=2, label=wh.replace("DHL-WH-","WH-"), marker="o", markersize=3)
axes[0].set_xticks(range(0,24,6))
axes[0].set_xticklabels(inv_wh_monthly["Snapshot_Date"].unique()[::6], rotation=20, fontsize=8)
axes[0].legend(fontsize=8)
style_ax(axes[0],"Inventory Value by Warehouse ($M)","Month","Value ($M)")

# Right: stockout rate trend
axes[1].plot(range(len(stockout_monthly)), stockout_monthly["stockout_rate_pct"], color=DHL_RED, linewidth=2, marker="o", markersize=3)
axes[1].fill_between(range(len(stockout_monthly)), stockout_monthly["stockout_rate_pct"], alpha=0.15, color=DHL_RED)
axes[1].set_xticks(range(0,24,4))
axes[1].set_xticklabels(stockout_monthly["year_month"].iloc[::4], rotation=20, fontsize=8)
style_ax(axes[1],"Monthly Stockout Rate (%)","Month","Stockout Rate %")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "10_inventory_stockout_trend.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 10_inventory_stockout_trend.png")

print("\n" + "="*72)
print("  SQL EXPLORATION COMPLETE — 10 blocks, 10 figures saved")
print(f"  Figures: {FIGS}")
print("="*72)
