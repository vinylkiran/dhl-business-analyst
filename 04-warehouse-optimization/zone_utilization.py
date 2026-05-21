"""
zone_utilization.py — Zone Performance & Utilisation Analysis
Project 4: Warehouse Optimization — DHL BA/DA Portfolio
Author: Vinyl Kiran Anipe
Date: 2024

Analyses zone-level performance using Task_Type→Zone proxy mapping,
accuracy by zone/shift/warehouse, peak hour patterns (shift-based),
and identifies high-error zones. Exports outputs/zone_summary.csv.

Zone proxy: Pick→Pick_Face, Putaway→Reserve, Replenishment→Reserve-to-Pick_Face,
            Receiving→Receiving, Transfer→Bulk, Cycle Count→All Zones
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

ZONE_COLORS = {
    "Pick_Face"          : "#D40511",
    "Reserve"            : "#FF6B35",
    "Reserve-to-Pick_Face": "#FFCC00",
    "Bulk"               : "#4A90D9",
    "Receiving"          : "#7CB342",
    "All Zones"          : "#9E9E9E",
}

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
con.execute(f"CREATE VIEW locs AS SELECT * FROM read_csv_auto('{DATA}warehouse_locations.csv')")

print("=" * 70)
print("  ZONE UTILISATION ANALYSIS")
print("=" * 70)

# ── Block A: Zone-level task volume and accuracy via proxy ─────────────────
print("\n── A. Zone Performance via Task_Type Proxy")

zone_perf = con.execute("""
    SELECT
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END                                                            AS Zone_Proxy,
        Task_Type,
        COUNT(*)                                                       AS task_count,
        AVG(Duration_Min)                                              AS avg_duration_min,
        SUM(CASE WHEN Accuracy_Flag = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)       AS error_count,
        AVG(Quantity)                                                  AS avg_qty
    FROM wms
    GROUP BY Task_Type
    ORDER BY task_count DESC
""").df()

print(zone_perf.to_string(index=False))

# ── Block B: Zone accuracy by warehouse ────────────────────────────────────
print("\n── B. Zone Accuracy by Warehouse")

zone_wh = con.execute("""
    SELECT
        Warehouse_ID,
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END                                                            AS Zone_Proxy,
        COUNT(*)                                                       AS task_count,
        SUM(CASE WHEN Accuracy_Flag = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct,
        SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)       AS error_count
    FROM wms
    GROUP BY Warehouse_ID, Task_Type
    ORDER BY Warehouse_ID, task_count DESC
""").df()

print(zone_wh.to_string(index=False))

# ── Block C: Zone activity by shift (peak pattern) ─────────────────────────
print("\n── C. Zone Activity by Shift")

zone_shift = con.execute("""
    SELECT
        Shift,
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END                                                            AS Zone_Proxy,
        COUNT(*)                                                       AS task_count,
        SUM(CASE WHEN Accuracy_Flag = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS accuracy_pct
    FROM wms
    GROUP BY Shift, Task_Type
    ORDER BY Shift, task_count DESC
""").df()

print(zone_shift.to_string(index=False))

# ── Block D: High-error zone identification ────────────────────────────────
print("\n── D. High-Error Zone Identification (Error Code Analysis)")

error_zone = con.execute("""
    SELECT
        CASE Task_Type
            WHEN 'Pick'          THEN 'Pick_Face'
            WHEN 'Putaway'       THEN 'Reserve'
            WHEN 'Replenishment' THEN 'Reserve-to-Pick_Face'
            WHEN 'Receiving'     THEN 'Receiving'
            WHEN 'Transfer'      THEN 'Bulk'
            WHEN 'Cycle Count'   THEN 'All Zones'
        END                                                            AS Zone_Proxy,
        Error_Code,
        COUNT(*)                                                       AS error_count
    FROM wms
    WHERE Error_Code IS NOT NULL
    GROUP BY Task_Type, Error_Code
    ORDER BY Zone_Proxy, error_count DESC
""").df()

print(error_zone.to_string(index=False))

# ── Block E: Warehouse location zone composition (from locations table) ────
print("\n── E. Physical Zone Composition from warehouse_locations")

loc_comp = con.execute("""
    SELECT
        Warehouse_ID,
        Zone,
        COUNT(*) AS slot_count,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY Warehouse_ID) AS pct_of_wh,
        AVG(Capacity_Units) AS avg_capacity_units,
        COUNT(CASE WHEN Active_Flag=1 THEN 1 END) * 100.0 / COUNT(*) AS active_pct
    FROM locs
    GROUP BY Warehouse_ID, Zone
    ORDER BY Warehouse_ID, slot_count DESC
""").df()

print(loc_comp.to_string(index=False))
total_slots = loc_comp["slot_count"].sum()
print(f"\n   Total warehouse slots across network: {total_slots:,}")

# ── Export zone_summary.csv ────────────────────────────────────────────────
print("\n── Exporting outputs/zone_summary.csv")

zone_summary_export = zone_perf.copy()
zone_summary_export.to_csv(os.path.join(OUTS, "zone_summary.csv"), index=False)
print(f"   Exported {len(zone_summary_export)} rows to zone_summary.csv")

# ── Figure 12: Zone accuracy heatmap (Zone × Warehouse) ───────────────────
pivot_acc = zone_wh.pivot_table(
    index="Zone_Proxy", columns="Warehouse_ID", values="accuracy_pct"
)
zone_order = ["Pick_Face","Reserve","Reserve-to-Pick_Face","Bulk","Receiving","All Zones"]
pivot_acc = pivot_acc.reindex([z for z in zone_order if z in pivot_acc.index])

fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("white")
cmap = plt.cm.RdYlGn
norm = mcolors.Normalize(vmin=97.5, vmax=100.5)
im = ax.imshow(pivot_acc.values, aspect="auto", cmap=cmap, norm=norm)
plt.colorbar(im, ax=ax, label="Accuracy %")
ax.set_xticks(range(len(pivot_acc.columns)))
ax.set_xticklabels(pivot_acc.columns, fontsize=9, color=DHL_MID)
ax.set_yticks(range(len(pivot_acc.index)))
ax.set_yticklabels(pivot_acc.index, fontsize=9, color=DHL_MID)
for r in range(len(pivot_acc.index)):
    for c in range(len(pivot_acc.columns)):
        val = pivot_acc.values[r, c]
        if not np.isnan(val):
            ax.text(c, r, f"{val:.2f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if val < 99 else DHL_DARK)
ax.set_title("Zone Accuracy Rate — Warehouse × Zone", fontsize=13,
             fontweight="bold", color=DHL_DARK, pad=10)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "12_zone_accuracy_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 12_zone_accuracy_heatmap.png")

# ── Figure 13: Zone task mix by shift (stacked bar) ───────────────────────
shift_order = ["Morning 06:00-14:00","Afternoon 14:00-22:00","Night 22:00-06:00"]
pivot_shift = zone_shift.pivot_table(
    index="Shift", columns="Zone_Proxy", values="task_count", fill_value=0
)
pivot_shift = pivot_shift.reindex([s for s in shift_order if s in pivot_shift.index])
zones_in = [z for z in zone_order if z in pivot_shift.columns]
pivot_shift = pivot_shift[zones_in]

fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor("white")
bottom = np.zeros(len(pivot_shift))
for zone in zones_in:
    vals = pivot_shift[zone].values
    bars = ax.bar(pivot_shift.index, vals, bottom=bottom,
                  color=ZONE_COLORS.get(zone, "#AAAAAA"), label=zone, edgecolor="white", linewidth=0.6)
    bottom += vals

ax.set_xticklabels(pivot_shift.index, fontsize=9, rotation=0)
style_ax(ax, "Task Mix by Zone Proxy and Shift", "Shift", "Task Count")
ax.legend(title="Zone", fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "13_zone_shift_mix.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 13_zone_shift_mix.png")

print("\n" + "=" * 70)
print("  ZONE UTILISATION ANALYSIS COMPLETE")
print(f"  Highest-error zone: {error_zone.groupby('Zone_Proxy')['error_count'].sum().idxmax()}")
print(f"  Total warehouse slots: {total_slots:,}")
print("=" * 70)
