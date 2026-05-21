"""
DHL Supply Chain | Demand Forecasting — SQL Exploration
BA/DA Portfolio | Project 2 | Step 1
Author: Vinyl Kiran Anipe

Executes exploratory SQL queries against DHL synthetic datasets using DuckDB.
Covers: monthly demand trends, seasonality, growth rates, stockout frequency,
warehouse comparison, and top SKU volumes.
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 130)
pd.set_option("display.float_format", "{:,.2f}".format)

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/02-demand-forecasting/")
FIGURES = os.path.join(PROJECT, "figures")
os.makedirs(FIGURES, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW sku_master   AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")
con.execute(f"CREATE VIEW daily_demand AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")

DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
PALETTE    = ["#D40511", "#FF8C00", "#4CAF50", "#1565C0", "#7B1FA2", "#00838F", "#E65100", "#2E7D32"]

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def run(label, sql):
    print(f"\n── {label}")
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    return df

# ── BLOCK 1: MONTHLY DEMAND TRENDS BY CATEGORY ────────────────────────────────
section("BLOCK 1 — MONTHLY DEMAND TRENDS BY CATEGORY (24 MONTHS)")

df_monthly_cat = run("1a. Monthly Demand (Units + Revenue) by Category", """
    SELECT
        strftime(Date, '%Y-%m')            AS year_month,
        Category,
        SUM(Quantity_Demanded)             AS total_units,
        ROUND(SUM(Revenue), 0)             AS total_revenue,
        COUNT(DISTINCT SKU_ID)             AS active_skus
    FROM daily_demand
    GROUP BY year_month, Category
    ORDER BY year_month, Category
""")

run("1b. Network-Wide Monthly Demand Summary", """
    SELECT
        strftime(Date, '%Y-%m')            AS year_month,
        SUM(Quantity_Demanded)             AS total_units,
        ROUND(SUM(Revenue), 0)             AS total_revenue,
        ROUND(AVG(Stockout_Flag)*100, 2)   AS stockout_rate_pct
    FROM daily_demand
    GROUP BY year_month
    ORDER BY year_month
""")

# Save figure 1: Monthly demand trend by category
fig, axes = plt.subplots(2, 1, figsize=(14, 9))
fig.suptitle("Monthly Demand Trends by Category (Jan 2022 – Dec 2023)",
             fontsize=14, fontweight="bold", color="#1A1A1A")

pivot_units = (df_monthly_cat.pivot(index="year_month", columns="Category", values="total_units")
               .fillna(0))
pivot_rev   = (df_monthly_cat.pivot(index="year_month", columns="Category", values="total_revenue")
               .fillna(0))

cats = pivot_units.columns.tolist()
for i, cat in enumerate(cats):
    axes[0].plot(pivot_units.index, pivot_units[cat], label=cat,
                 color=PALETTE[i % len(PALETTE)], linewidth=1.8, marker="o", markersize=3)
    axes[1].plot(pivot_rev.index, pivot_rev[cat] / 1e6, label=cat,
                 color=PALETTE[i % len(PALETTE)], linewidth=1.8, marker="o", markersize=3)

for ax, ylabel, title in zip(axes,
        ["Units Demanded", "Revenue ($M)"],
        ["Monthly Units by Category", "Monthly Revenue by Category ($M)"]):
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.legend(fontsize=7, ncol=4, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    tick_labels = pivot_units.index.tolist()
    show_ticks  = [t for t in tick_labels if t.endswith("-01") or t.endswith("-07")]
    ax.set_xticks([tick_labels.index(t) for t in show_ticks if t in tick_labels])
    ax.set_xticklabels(show_ticks, rotation=30, ha="right", fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "01_monthly_demand_by_category.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 01_monthly_demand_by_category.png")

# ── BLOCK 2: SEASONALITY INDEX ─────────────────────────────────────────────────
section("BLOCK 2 — SEASONALITY INDEX")

df_season = run("2a. Monthly Seasonality Index (demand vs annual average)", """
    WITH monthly AS (
        SELECT
            CAST(strftime(Date, '%m') AS INTEGER)  AS month_num,
            strftime(Date, '%m')                    AS month_label,
            SUM(Quantity_Demanded)                  AS total_units
        FROM daily_demand
        GROUP BY month_num, month_label
    ),
    annual_avg AS (
        SELECT AVG(total_units) AS avg_monthly FROM monthly
    )
    SELECT
        month_num,
        month_label,
        ROUND(total_units, 0)             AS total_units,
        ROUND(total_units / avg_monthly, 3) AS seasonality_index
    FROM monthly, annual_avg
    ORDER BY month_num
""")

# Save figure 2: Seasonality index bar chart
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
fig, ax = plt.subplots(figsize=(12, 5))
colors_bar = [DHL_RED if v >= 1.0 else "#90A4AE" for v in df_season["seasonality_index"]]
bars = ax.bar(range(len(df_season)), df_season["seasonality_index"], color=colors_bar,
              edgecolor="white", linewidth=0.8, width=0.7)
ax.axhline(1.0, color="#333333", linewidth=1.5, linestyle="--", label="Baseline (1.0)")
for bar, val in zip(bars, df_season["seasonality_index"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"{val:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_xticks(range(len(df_season)))
ax.set_xticklabels(month_names, fontsize=10)
ax.set_ylabel("Seasonality Index (1.0 = average month)", fontsize=10)
ax.set_title("Monthly Seasonality Index — Network-Wide Demand\n(Red = above average month)",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, df_season["seasonality_index"].max() * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "02_seasonality_index.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 02_seasonality_index.png")

# ── BLOCK 3: TOP 20 SKUs BY DEMAND VOLUME ─────────────────────────────────────
section("BLOCK 3 — TOP 20 SKUs BY DEMAND VOLUME")

df_top20 = run("3a. Top 20 SKUs — Total Units Demanded with Revenue and Stockout Rate", """
    SELECT
        d.SKU_ID,
        s.Category,
        s.ABC_Class,
        ROUND(SUM(d.Quantity_Demanded), 0)               AS total_units,
        ROUND(SUM(d.Revenue), 0)                         AS total_revenue,
        ROUND(SUM(d.Stockout_Flag)*100.0/COUNT(*), 2)    AS stockout_rate_pct,
        ROUND(AVG(d.Quantity_Demanded), 1)               AS avg_daily_demand
    FROM daily_demand d
    JOIN sku_master s ON d.SKU_ID = s.SKU_ID
    GROUP BY d.SKU_ID, s.Category, s.ABC_Class
    ORDER BY total_units DESC
    LIMIT 20
""")

# Save figure 3: Top 20 SKUs horizontal bar
fig, ax = plt.subplots(figsize=(12, 8))
colors_sku = [DHL_RED if c == "A" else ("#FF8C00" if c == "B" else "#4CAF50")
              for c in df_top20["ABC_Class"]]
y_pos = range(len(df_top20))
bars = ax.barh(y_pos, df_top20["total_units"], color=colors_sku, edgecolor="white", linewidth=0.5)
ax.set_yticks(y_pos)
ax.set_yticklabels([f"{r['SKU_ID']} ({r['Category'][:4]})" for _, r in df_top20.iterrows()],
                   fontsize=8)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
ax.set_xlabel("Total Units Demanded (thousands)", fontsize=10)
ax.set_title("Top 20 SKUs by Demand Volume — 24-Month Period\n"
             "Color: A=Red · B=Orange · C=Green",
             fontsize=12, fontweight="bold")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "03_top20_skus_by_volume.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 03_top20_skus_by_volume.png")

# ── BLOCK 4: DEMAND GROWTH RATE 2022 vs 2023 ─────────────────────────────────
section("BLOCK 4 — DEMAND GROWTH RATE: 2022 vs 2023")

df_growth = run("4a. Year-over-Year Demand Growth by Category", """
    WITH yearly AS (
        SELECT
            Category,
            CAST(strftime(Date, '%Y') AS INTEGER) AS yr,
            SUM(Quantity_Demanded)                AS total_units,
            ROUND(SUM(Revenue), 0)                AS total_revenue
        FROM daily_demand
        GROUP BY Category, yr
    )
    SELECT
        a.Category,
        a.total_units                              AS units_2022,
        b.total_units                              AS units_2023,
        ROUND((b.total_units - a.total_units)*100.0 / a.total_units, 2) AS unit_growth_pct,
        a.total_revenue                            AS rev_2022,
        b.total_revenue                            AS rev_2023,
        ROUND((b.total_revenue - a.total_revenue)*100.0 / a.total_revenue, 2) AS rev_growth_pct
    FROM yearly a
    JOIN yearly b ON a.Category = b.Category AND a.yr = 2022 AND b.yr = 2023
    ORDER BY unit_growth_pct DESC
""")

run("4b. Network-Wide Growth Summary", """
    WITH yearly AS (
        SELECT
            CAST(strftime(Date, '%Y') AS INTEGER) AS yr,
            SUM(Quantity_Demanded) AS total_units,
            ROUND(SUM(Revenue), 0) AS total_revenue
        FROM daily_demand
        GROUP BY yr
    )
    SELECT
        a.total_units  AS units_2022,
        b.total_units  AS units_2023,
        ROUND((b.total_units - a.total_units)*100.0 / a.total_units, 2) AS unit_growth_pct,
        a.total_revenue AS rev_2022,
        b.total_revenue AS rev_2023,
        ROUND((b.total_revenue - a.total_revenue)*100.0 / a.total_revenue, 2) AS rev_growth_pct
    FROM yearly a JOIN yearly b ON a.yr = 2022 AND b.yr = 2023
""")

# Save figure 4: Growth rate diverging bar chart
fig, ax = plt.subplots(figsize=(11, 6))
growth_vals = df_growth["unit_growth_pct"].tolist()
cats_g      = df_growth["Category"].tolist()
bar_colors  = [DHL_RED if v >= 0 else "#607D8B" for v in growth_vals]
ax.barh(cats_g, growth_vals, color=bar_colors, edgecolor="white", linewidth=0.6)
ax.axvline(0, color="#333333", linewidth=1.2)
for i, (cat, val) in enumerate(zip(cats_g, growth_vals)):
    ax.text(val + (0.3 if val >= 0 else -0.3), i, f"{val:+.1f}%",
            ha="left" if val >= 0 else "right", va="center", fontsize=9, fontweight="bold")
ax.set_xlabel("YoY Unit Demand Growth (%)", fontsize=10)
ax.set_title("Demand Growth Rate by Category: 2022 → 2023\nRed = positive growth",
             fontsize=12, fontweight="bold")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "04_demand_growth_yoy.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 04_demand_growth_yoy.png")

# ── BLOCK 5: STOCKOUT FREQUENCY MONTH-OVER-MONTH ─────────────────────────────
section("BLOCK 5 — STOCKOUT FREQUENCY (MONTH-OVER-MONTH)")

df_stockout_mom = run("5a. Monthly Stockout Rate and Unfulfilled Units (Network-Wide)", """
    SELECT
        strftime(Date, '%Y-%m')                          AS year_month,
        COUNT(*)                                          AS demand_days,
        SUM(Stockout_Flag)                               AS stockout_days,
        ROUND(SUM(Stockout_Flag)*100.0 / COUNT(*), 2)   AS stockout_rate_pct,
        ROUND(SUM(Quantity_Demanded - Quantity_Fulfilled), 0) AS unfulfilled_units
    FROM daily_demand
    GROUP BY year_month
    ORDER BY year_month
""")

run("5b. Monthly Stockout Rate by ABC Class", """
    SELECT
        strftime(Date, '%Y-%m')                          AS year_month,
        ABC_Class,
        ROUND(SUM(Stockout_Flag)*100.0 / COUNT(*), 2)   AS stockout_rate_pct
    FROM daily_demand
    GROUP BY year_month, ABC_Class
    ORDER BY year_month, ABC_Class
""")

# Save figure 5: Stockout trend
fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()
months = df_stockout_mom["year_month"].tolist()
x = range(len(months))
ax1.bar(x, df_stockout_mom["unfulfilled_units"] / 1000, color=DHL_YELLOW,
        alpha=0.7, width=0.6, label="Unfulfilled Units (K)")
ax2.plot(x, df_stockout_mom["stockout_rate_pct"], color=DHL_RED,
         linewidth=2, marker="o", markersize=4, label="Stockout Rate %")
ax1.set_ylabel("Unfulfilled Units (thousands)", fontsize=10)
ax2.set_ylabel("Stockout Rate (%)", fontsize=10, color=DHL_RED)
ax2.tick_params(colors=DHL_RED)
ax1.set_xticks(list(x))
ax1.set_xticklabels(months, rotation=45, ha="right", fontsize=7)
ax1.set_title("Monthly Stockout Frequency — Network-Wide (Jan 2022 – Dec 2023)\n"
              "Bars = Unfulfilled Units · Line = Stockout Rate %",
              fontsize=12, fontweight="bold")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
ax1.grid(axis="y", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "05_stockout_trend_monthly.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 05_stockout_trend_monthly.png")

# ── BLOCK 6: WAREHOUSE DEMAND COMPARISON ─────────────────────────────────────
section("BLOCK 6 — WAREHOUSE DEMAND COMPARISON")

df_wh = run("6a. Monthly Demand by Warehouse", """
    SELECT
        strftime(Date, '%Y-%m')          AS year_month,
        Warehouse_ID,
        SUM(Quantity_Demanded)           AS total_units,
        ROUND(SUM(Revenue), 0)           AS total_revenue,
        COUNT(DISTINCT SKU_ID)           AS active_skus,
        ROUND(SUM(Stockout_Flag)*100.0/COUNT(*), 2) AS stockout_rate_pct
    FROM daily_demand
    GROUP BY year_month, Warehouse_ID
    ORDER BY year_month, Warehouse_ID
""")

run("6b. Warehouse Annual Summary", """
    SELECT
        Warehouse_ID,
        ROUND(SUM(Quantity_Demanded), 0)  AS total_units_24mo,
        ROUND(SUM(Revenue), 0)            AS total_revenue_24mo,
        COUNT(DISTINCT SKU_ID)            AS unique_skus,
        ROUND(SUM(Stockout_Flag)*100.0/COUNT(*), 2) AS avg_stockout_rate
    FROM daily_demand
    GROUP BY Warehouse_ID
    ORDER BY total_revenue_24mo DESC
""")

# Save figure 6: Warehouse comparison
pivot_wh = df_wh.pivot(index="year_month", columns="Warehouse_ID", values="total_units").fillna(0)
wh_colors = {wh: c for wh, c in zip(pivot_wh.columns, [DHL_RED, "#1565C0", "#2E7D32"])}
fig, ax = plt.subplots(figsize=(14, 5))
for wh in pivot_wh.columns:
    ax.plot(range(len(pivot_wh)), pivot_wh[wh], label=wh,
            color=wh_colors.get(wh, "#888888"), linewidth=2.0, marker="o", markersize=3)
ax.set_xticks(range(len(pivot_wh)))
ax.set_xticklabels(pivot_wh.index.tolist(), rotation=45, ha="right", fontsize=7)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
ax.set_ylabel("Units Demanded (thousands)", fontsize=10)
ax.set_title("Monthly Demand Volume by Warehouse — 24-Month Period",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "06_warehouse_demand_comparison.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 06_warehouse_demand_comparison.png")

print(f"\n{'='*70}")
print("  SQL EXPLORATION COMPLETE — 6 blocks, 6 figures saved")
print(f"  Figures: {FIGURES}")
print("  Next step: analysis.py — moving averages, decomposition, MAPE baseline")
print(f"{'='*70}\n")
