"""
DHL Supply Chain | Warehouse Optimization — SQL Exploration
BA/DA Portfolio | Project 4 | Step 1
Author: Vinyl Kiran Anipe

Explores warehouse operations using wms_tasks.csv and warehouse_locations.csv.
Covers: task volumes, pick accuracy, operator productivity, error rates,
zone utilization proxy, and monthly operational trends.
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

pd.set_option("display.width", 130)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", "{:,.2f}".format)

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/04-warehouse-optimization/")
FIGURES = os.path.join(PROJECT, "figures")
os.makedirs(FIGURES, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW wms      AS SELECT * FROM read_csv_auto('{DATA}wms_tasks.csv')")
con.execute(f"CREATE VIEW locs     AS SELECT * FROM read_csv_auto('{DATA}warehouse_locations.csv')")
con.execute(f"CREATE VIEW sku      AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
PALETTE    = ["#D40511","#FF8C00","#4CAF50","#1565C0","#7B1FA2","#00838F"]
SHIFT_COLORS = {
    "Morning 06:00-14:00":   "#FFCC00",
    "Afternoon 14:00-22:00": "#D40511",
    "Night 22:00-06:00":     "#1565C0",
}

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def run(label, sql):
    print(f"\n── {label}")
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    return df

# ── BLOCK 1: TOTAL TASKS BY TYPE PER WAREHOUSE ────────────────────────────────
section("BLOCK 1 — TASK VOLUME BY TYPE AND WAREHOUSE")

df_task_wh = run("1a. Task Volume by Type and Warehouse", """
    SELECT Warehouse_ID,
           Task_Type,
           COUNT(*)                                     AS task_count,
           ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(PARTITION BY Warehouse_ID), 2) AS pct_of_wh
    FROM wms
    GROUP BY Warehouse_ID, Task_Type
    ORDER BY Warehouse_ID, task_count DESC
""")

df_task_summary = run("1b. Network Task Summary by Type", """
    SELECT Task_Type,
           COUNT(*)                            AS total_tasks,
           ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM wms), 2) AS pct_of_total,
           ROUND(AVG(Duration_Min), 2)         AS avg_duration_min,
           ROUND(AVG(Quantity), 2)             AS avg_quantity
    FROM wms
    GROUP BY Task_Type
    ORDER BY total_tasks DESC
""")

# Figure 1: Task type stacked bar by warehouse
fig, ax = plt.subplots(figsize=(13, 5))
task_types = df_task_wh["Task_Type"].unique().tolist()
warehouses = df_task_wh["Warehouse_ID"].unique().tolist()
pivot = df_task_wh.pivot_table(index="Warehouse_ID", columns="Task_Type",
                                values="task_count", fill_value=0)
pivot.plot(kind="bar", stacked=True, ax=ax,
           color=PALETTE[:len(pivot.columns)], edgecolor="white", linewidth=0.5)
ax.set_xlabel("")
ax.set_ylabel("Number of Tasks", fontsize=10)
ax.set_title("Task Volume by Type per Warehouse — 24-Month Period", fontsize=12, fontweight="bold")
ax.legend(title="Task Type", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
ax.tick_params(axis="x", rotation=0)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "01_task_volume_by_warehouse.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 01_task_volume_by_warehouse.png")

# ── BLOCK 2: PICK ACCURACY BY WAREHOUSE AND SHIFT ─────────────────────────────
section("BLOCK 2 — PICK ACCURACY BY WAREHOUSE AND SHIFT")

df_acc_wh = run("2a. Pick Accuracy Rate by Warehouse", """
    SELECT Warehouse_ID,
           COUNT(*)                                  AS total_picks,
           SUM(Accuracy_Flag)                        AS accurate_picks,
           ROUND(AVG(Accuracy_Flag)*100, 3)          AS accuracy_pct,
           COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END) AS error_count
    FROM wms WHERE Task_Type = 'Pick'
    GROUP BY Warehouse_ID ORDER BY accuracy_pct DESC
""")

df_acc_shift = run("2b. Pick Accuracy Rate by Shift", """
    SELECT Shift,
           COUNT(*)                          AS total_picks,
           ROUND(AVG(Accuracy_Flag)*100, 3)  AS accuracy_pct,
           COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END) AS error_count,
           ROUND(AVG(Duration_Min), 2)       AS avg_pick_duration_min
    FROM wms WHERE Task_Type = 'Pick'
    GROUP BY Shift ORDER BY accuracy_pct DESC
""")

df_acc_wh_shift = run("2c. Pick Accuracy — Warehouse × Shift Matrix", """
    SELECT Warehouse_ID,
           Shift,
           COUNT(*) AS total_picks,
           ROUND(AVG(Accuracy_Flag)*100, 2) AS accuracy_pct
    FROM wms WHERE Task_Type = 'Pick'
    GROUP BY Warehouse_ID, Shift ORDER BY Warehouse_ID, Shift
""")

# Figure 2: Accuracy heatmap — Warehouse × Shift
pivot_acc = df_acc_wh_shift.pivot(index="Shift", columns="Warehouse_ID", values="accuracy_pct")
fig, ax = plt.subplots(figsize=(9, 4))
im = ax.imshow(pivot_acc.values, cmap="RdYlGn", aspect="auto", vmin=98.5, vmax=100)
ax.set_xticks(range(len(pivot_acc.columns)))
ax.set_xticklabels(pivot_acc.columns, fontsize=9)
ax.set_yticks(range(len(pivot_acc.index)))
ax.set_yticklabels([s.split(" ")[0] for s in pivot_acc.index], fontsize=9)
for i in range(len(pivot_acc.index)):
    for j in range(len(pivot_acc.columns)):
        ax.text(j, i, f"{pivot_acc.iloc[i,j]:.2f}%", ha="center", va="center",
                fontsize=10, fontweight="bold", color="#333")
plt.colorbar(im, ax=ax, label="Accuracy %", shrink=0.8)
ax.set_title("Pick Accuracy (%) — Warehouse × Shift\nGreen = higher accuracy",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "02_pick_accuracy_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 02_pick_accuracy_heatmap.png")

# ── BLOCK 3: AVERAGE TASK DURATION BY TYPE AND SHIFT ─────────────────────────
section("BLOCK 3 — TASK DURATION BY TYPE AND SHIFT")

df_dur_type = run("3a. Average Task Duration by Task Type", """
    SELECT Task_Type,
           ROUND(AVG(Duration_Min), 2)   AS avg_min,
           ROUND(MIN(Duration_Min), 0)   AS min_min,
           ROUND(MAX(Duration_Min), 0)   AS max_min,
           ROUND(STDDEV(Duration_Min), 2) AS std_min,
           COUNT(*) AS task_count
    FROM wms GROUP BY Task_Type ORDER BY avg_min DESC
""")

df_dur_shift = run("3b. Average Pick Duration by Shift", """
    SELECT Shift,
           ROUND(AVG(Duration_Min), 2)    AS avg_pick_min,
           ROUND(STDDEV(Duration_Min), 2) AS std_pick_min,
           COUNT(*)                        AS pick_count
    FROM wms WHERE Task_Type = 'Pick'
    GROUP BY Shift ORDER BY avg_pick_min
""")

# Figure 3: Task duration box plot proxy (mean ± std)
fig, ax = plt.subplots(figsize=(11, 5))
task_order = df_dur_type.sort_values("avg_min")
ax.barh(task_order["Task_Type"], task_order["avg_min"],
        color=PALETTE[:len(task_order)], edgecolor="white", alpha=0.85)
ax.errorbar(task_order["avg_min"], range(len(task_order)),
            xerr=task_order["std_min"], fmt="none", color="#333",
            capsize=5, linewidth=1.5)
for i, (_, row) in enumerate(task_order.iterrows()):
    ax.text(row["avg_min"] + row["std_min"] + 0.3, i,
            f"{row['avg_min']:.1f} min", va="center", fontsize=9, fontweight="bold")
ax.set_xlabel("Average Duration (minutes)", fontsize=10)
ax.set_title("Average Task Duration by Type — Error Bars Show ±1 Std Dev",
             fontsize=12, fontweight="bold")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "03_task_duration_by_type.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 03_task_duration_by_type.png")

# ── BLOCK 4: TOP 30 MOST-PICKED SKUs ──────────────────────────────────────────
section("BLOCK 4 — TOP 30 MOST-PICKED SKUs BY PICK FREQUENCY")

df_top30 = run("4a. Top 30 SKUs by Pick Frequency", """
    SELECT w.SKU_ID,
           w.Category,
           s.ABC_Class,
           s.Storage_Type,
           COUNT(*)                         AS pick_count,
           ROUND(AVG(w.Duration_Min), 2)    AS avg_pick_min,
           ROUND(AVG(w.Accuracy_Flag)*100, 2) AS accuracy_pct,
           SUM(w.Quantity)                  AS total_qty_picked
    FROM wms w
    JOIN sku s ON w.SKU_ID = s.SKU_ID
    WHERE w.Task_Type = 'Pick'
    GROUP BY w.SKU_ID, w.Category, s.ABC_Class, s.Storage_Type
    ORDER BY pick_count DESC
    LIMIT 30
""")

# Figure 4: Top 30 picks horizontal bar
fig, ax = plt.subplots(figsize=(12, 9))
abc_colors = {"A": DHL_RED, "B": "#FF8C00", "C": "#4CAF50"}
top30_sorted = df_top30.sort_values("pick_count", ascending=True).tail(20)
bar_colors = [abc_colors.get(c, "#888") for c in top30_sorted["ABC_Class"]]
ax.barh(range(len(top30_sorted)), top30_sorted["pick_count"], color=bar_colors, alpha=0.85)
ax.set_yticks(range(len(top30_sorted)))
ax.set_yticklabels([f"{r['SKU_ID']} ({r['ABC_Class']}-cls)" for _, r in top30_sorted.iterrows()], fontsize=8)
ax.set_xlabel("Pick Frequency (24 months)", fontsize=10)
ax.set_title("Top 20 Most-Picked SKUs (A=Red · B=Orange · C=Green)\n"
             "High pick frequency → priority candidate for Pick_Face slotting",
             fontsize=12, fontweight="bold")
ax.grid(axis="x", linestyle="--", alpha=0.4)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=v, label=k) for k, v in abc_colors.items()],
          title="ABC Class", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "04_top30_picked_skus.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 04_top30_picked_skus.png")

# ── BLOCK 5: OPERATOR PRODUCTIVITY ────────────────────────────────────────────
section("BLOCK 5 — OPERATOR PRODUCTIVITY")

df_ops = run("5a. Operator Productivity — Tasks per Shift", """
    WITH op_shift AS (
        SELECT Operator_ID, Warehouse_ID, Shift,
               strftime(Task_Date, '%Y-%m') AS ym,
               COUNT(*) AS tasks
        FROM wms
        GROUP BY Operator_ID, Warehouse_ID, Shift, ym
    )
    SELECT Operator_ID,
           Warehouse_ID,
           Shift,
           ROUND(AVG(tasks), 1) AS avg_tasks_per_shift,
           MAX(tasks)           AS max_tasks_per_shift,
           COUNT(DISTINCT ym)   AS months_active
    FROM op_shift
    GROUP BY Operator_ID, Warehouse_ID, Shift
    ORDER BY avg_tasks_per_shift DESC
    LIMIT 20
""")

df_ops_wh = run("5b. Warehouse-Level Operator Productivity by Shift", """
    WITH op_shift AS (
        SELECT Warehouse_ID, Shift,
               strftime(Task_Date, '%Y-%m') AS ym,
               Operator_ID,
               COUNT(*) AS tasks
        FROM wms GROUP BY Warehouse_ID, Shift, ym, Operator_ID
    )
    SELECT Warehouse_ID, Shift,
           COUNT(DISTINCT Operator_ID) AS operator_count,
           ROUND(AVG(tasks), 1)        AS avg_tasks_per_op_per_shift,
           ROUND(SUM(tasks)*1.0/COUNT(DISTINCT Operator_ID), 0) AS total_tasks_per_op
    FROM op_shift
    GROUP BY Warehouse_ID, Shift
    ORDER BY Warehouse_ID, Shift
""")

# Figure 5: Productivity by shift and warehouse
pivot_prod = df_ops_wh.pivot_table(
    index="Shift", columns="Warehouse_ID",
    values="avg_tasks_per_op_per_shift", aggfunc="mean")
fig, ax = plt.subplots(figsize=(11, 5))
x = range(len(pivot_prod.index))
w = 0.25
for i, (wh, color) in enumerate(zip(pivot_prod.columns,
                                      [DHL_RED, "#1565C0", "#4CAF50"])):
    ax.bar([p + i*w for p in x], pivot_prod[wh],
           width=w, label=wh, color=color, alpha=0.85, edgecolor="white")
ax.set_xticks([p + w for p in x])
ax.set_xticklabels([s.split(" ")[0] for s in pivot_prod.index], fontsize=10)
ax.set_ylabel("Avg Tasks per Operator per Shift", fontsize=10)
ax.set_title("Operator Productivity — Avg Tasks per Shift by Warehouse & Shift",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "05_operator_productivity.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 05_operator_productivity.png")

# ── BLOCK 6: ERROR RATE BY ERROR CODE ─────────────────────────────────────────
section("BLOCK 6 — ERROR RATE BY ERROR CODE TYPE")

df_errors = run("6a. Error Rate by Error Code", """
    SELECT Error_Code,
           COUNT(*)                              AS error_count,
           ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM wms WHERE Error_Code IS NOT NULL), 2) AS pct_of_errors,
           ROUND(AVG(Duration_Min), 2)           AS avg_task_duration_min
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY Error_Code ORDER BY error_count DESC
""")

run("6b. Error Rate by Warehouse", """
    SELECT Warehouse_ID,
           COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END) AS total_errors,
           COUNT(*) AS total_tasks,
           ROUND(COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END)*100.0/COUNT(*), 3) AS error_rate_pct
    FROM wms GROUP BY Warehouse_ID ORDER BY error_rate_pct DESC
""")

run("6c. Error Rate by Task Type", """
    SELECT Task_Type,
           COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END) AS error_count,
           COUNT(*) AS total_tasks,
           ROUND(COUNT(CASE WHEN Error_Code IS NOT NULL THEN 1 END)*100.0/COUNT(*), 3) AS error_rate_pct
    FROM wms GROUP BY Task_Type ORDER BY error_rate_pct DESC
""")

# Figure 6: Error distribution pie
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Warehouse Error Analysis", fontsize=13, fontweight="bold")
wedge_colors = [DHL_RED, "#FF8C00", "#4CAF50", "#1565C0", "#7B1FA2"]
axes[0].pie(df_errors["error_count"], labels=df_errors["Error_Code"],
            colors=wedge_colors[:len(df_errors)], autopct="%1.1f%%",
            startangle=140, textprops={"fontsize": 9})
axes[0].set_title("Error Type Distribution", fontsize=11, fontweight="bold")
axes[1].bar(df_errors["Error_Code"], df_errors["avg_task_duration_min"],
            color=wedge_colors[:len(df_errors)], edgecolor="white")
axes[1].axhline(con.execute("SELECT AVG(Duration_Min) FROM wms").fetchone()[0],
                color="#333", linewidth=1.5, linestyle="--", label="Network avg task duration")
axes[1].set_ylabel("Avg Task Duration (min)", fontsize=10)
axes[1].set_title("Avg Task Duration When Error Occurs", fontsize=11, fontweight="bold")
axes[1].legend(fontsize=9)
axes[1].grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "06_error_analysis.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 06_error_analysis.png")

# ── BLOCK 7: ZONE UTILIZATION PROXY (via Task_Type → Zone mapping) ────────────
section("BLOCK 7 — ZONE UTILIZATION (TASK_TYPE → ZONE PROXY)")

# Map task types to primary zones they operate in
zone_map_note = """
  Zone proxy mapping (wms_tasks has no Location_ID column):
    Pick          → Pick_Face
    Putaway       → Reserve (incoming stock)
    Replenishment → Reserve → Pick_Face (between zones)
    Receiving     → Receiving
    Transfer      → Bulk
    Cycle Count   → all zones (distributed)
"""
print(zone_map_note)

df_zone = run("7a. Task Volume by Mapped Zone (Task_Type proxy)", """
    SELECT
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END AS Zone_Proxy,
        Warehouse_ID,
        COUNT(*) AS task_count,
        ROUND(AVG(Duration_Min), 2) AS avg_duration_min,
        ROUND(AVG(Accuracy_Flag)*100, 2) AS accuracy_pct
    FROM wms
    GROUP BY Zone_Proxy, Warehouse_ID
    ORDER BY task_count DESC
""")

# Figure 7: Zone activity heatmap
pivot_zone = df_zone.pivot_table(index="Zone_Proxy", columns="Warehouse_ID",
                                  values="task_count", aggfunc="sum", fill_value=0)
fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(pivot_zone.values / 1000, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(pivot_zone.columns)))
ax.set_xticklabels(pivot_zone.columns, fontsize=9)
ax.set_yticks(range(len(pivot_zone.index)))
ax.set_yticklabels(pivot_zone.index, fontsize=9)
for i in range(len(pivot_zone.index)):
    for j in range(len(pivot_zone.columns)):
        ax.text(j, i, f"{pivot_zone.iloc[i,j]/1000:.1f}K",
                ha="center", va="center", fontsize=9, fontweight="bold",
                color="white" if pivot_zone.iloc[i,j] > pivot_zone.values.max()*0.5 else "#333")
plt.colorbar(im, ax=ax, label="Task Count (thousands)", shrink=0.8)
ax.set_title("Zone Utilization by Warehouse (Task_Type Proxy)\n"
             "Pick_Face zone carries ~45% of all task volume",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "07_zone_utilization_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 07_zone_utilization_heatmap.png")

# ── BLOCK 8: MONTHLY TASK VOLUME TREND ────────────────────────────────────────
section("BLOCK 8 — MONTHLY TASK VOLUME TREND (OPERATIONAL PEAKS)")

df_monthly = run("8a. Monthly Task Volume by Warehouse", """
    SELECT strftime(Task_Date, '%Y-%m') AS year_month,
           Warehouse_ID,
           COUNT(*) AS task_count,
           COUNT(DISTINCT Operator_ID) AS active_operators,
           ROUND(AVG(Duration_Min), 2) AS avg_duration_min
    FROM wms
    GROUP BY year_month, Warehouse_ID
    ORDER BY year_month, Warehouse_ID
""")

# Figure 8: Monthly trend
pivot_monthly = df_monthly.pivot(index="year_month", columns="Warehouse_ID",
                                  values="task_count").fillna(0)
fig, ax = plt.subplots(figsize=(14, 5))
wh_colors = {"DHL-WH-NJ01": DHL_RED, "DHL-WH-IL02": "#1565C0", "DHL-WH-TX03": "#4CAF50"}
for wh in pivot_monthly.columns:
    ax.plot(range(len(pivot_monthly)), pivot_monthly[wh]/1000, label=wh,
            color=wh_colors.get(wh, "#888"), linewidth=2, marker="o", markersize=4)
ax.set_xticks(range(len(pivot_monthly)))
ax.set_xticklabels(pivot_monthly.index.tolist(), rotation=45, ha="right", fontsize=7)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
ax.set_ylabel("Task Count (thousands)", fontsize=10)
ax.set_title("Monthly WMS Task Volume by Warehouse — 24-Month Operational Trend",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "08_monthly_task_trend.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 08_monthly_task_trend.png")

print(f"\n{'='*70}")
print("  SQL EXPLORATION COMPLETE — 8 blocks, 8 figures saved")
print(f"  Figures: {FIGURES}")
print("  Next: slotting_analysis.py → zone_utilization.py → affinity_analysis.py → impact_calculator.py")
print(f"{'='*70}\n")
