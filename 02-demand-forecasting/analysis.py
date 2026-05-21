"""
DHL Supply Chain | Demand Forecasting — Analysis Script
BA/DA Portfolio | Project 2 | Step 2
Author: Vinyl Kiran Anipe

Produces:
  - 7/14/28-day moving average charts for A-class SKUs
  - Seasonal decomposition (additive) on network-wide daily demand
  - Demand variability heatmap by month × category
  - Business impact: stockout days → estimated lost revenue
  - Forecast accuracy baseline: 14-day MA MAPE per ABC class
  - outputs/demand_summary.csv
"""

import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/02-demand-forecasting/")
FIGURES = os.path.join(PROJECT, "figures")
OUTPUTS = os.path.join(PROJECT, "outputs")
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
CLASS_COLOR = {"A": "#D40511", "B": "#FF8C00", "C": "#4CAF50"}

pd.set_option("display.float_format", "{:,.4f}".format)

# ── Data load ──────────────────────────────────────────────────────────────────
con = duckdb.connect()
con.execute(f"CREATE VIEW sku_master   AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")
con.execute(f"CREATE VIEW daily_demand AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")

print("Loading demand data...")
df_raw = con.execute("""
    SELECT d.Date, d.SKU_ID, d.Warehouse_ID, d.ABC_Class, s.Category,
           d.Quantity_Demanded, d.Quantity_Fulfilled, d.Revenue,
           d.Stockout_Flag, s.Unit_Price
    FROM daily_demand d
    JOIN sku_master s ON d.SKU_ID = s.SKU_ID
    ORDER BY d.SKU_ID, d.Date
""").df()
df_raw["Date"] = pd.to_datetime(df_raw["Date"])
print(f"  Loaded {len(df_raw):,} records | {df_raw['SKU_ID'].nunique()} SKUs | "
      f"{df_raw['Date'].min().date()} → {df_raw['Date'].max().date()}")

# ── Network-wide daily aggregation ────────────────────────────────────────────
net_daily = (df_raw.groupby("Date")
             .agg(total_units=("Quantity_Demanded","sum"),
                  total_revenue=("Revenue","sum"),
                  stockout_days=("Stockout_Flag","sum"))
             .reset_index()
             .sort_values("Date"))
net_daily.set_index("Date", inplace=True)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1: MOVING AVERAGES — NETWORK-WIDE DAILY DEMAND
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/5] Moving averages — network-wide daily demand...")
net_daily["MA7"]  = net_daily["total_units"].rolling(7,  min_periods=1).mean()
net_daily["MA14"] = net_daily["total_units"].rolling(14, min_periods=1).mean()
net_daily["MA28"] = net_daily["total_units"].rolling(28, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(15, 5))
ax.plot(net_daily.index, net_daily["total_units"], color="#BDBDBD", linewidth=0.6,
        alpha=0.7, label="Daily Demand")
ax.plot(net_daily.index, net_daily["MA7"],  color="#FF8C00", linewidth=1.4, label="7-Day MA")
ax.plot(net_daily.index, net_daily["MA14"], color=DHL_RED,   linewidth=1.8, label="14-Day MA")
ax.plot(net_daily.index, net_daily["MA28"], color="#1565C0", linewidth=2.0,
        linestyle="--", label="28-Day MA")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
ax.set_ylabel("Units Demanded (thousands)", fontsize=10)
ax.set_title("Network-Wide Daily Demand — 7 / 14 / 28-Day Moving Averages\n"
             "Jan 2022 – Dec 2023", fontsize=12, fontweight="bold")
ax.legend(fontsize=9, loc="upper left")
ax.grid(axis="y", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "07_moving_averages_network.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 07_moving_averages_network.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2: SEASONAL DECOMPOSITION (additive, period=365)
# ─────────────────────────────────────────────────────────────────────────────
print("[2/5] Seasonal decomposition...")
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    # Use weekly data for cleaner decomposition
    weekly = net_daily["total_units"].resample("W").sum()
    decomp = seasonal_decompose(weekly, model="additive", period=52)

    fig, axes = plt.subplots(4, 1, figsize=(14, 10))
    for ax, data, label in zip(
        axes,
        [weekly, decomp.trend, decomp.seasonal, decomp.resid],
        ["Observed", "Trend", "Seasonal", "Residual"]
    ):
        ax.plot(data.index, data.values, color=DHL_RED, linewidth=1.3)
        ax.set_ylabel(label, fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.axhline(0, color="#AAAAAA", linewidth=0.8, linestyle=":")
    axes[0].set_title("Additive Seasonal Decomposition — Weekly Network Demand",
                      fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "08_seasonal_decomposition.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  → Saved 08_seasonal_decomposition.png")
except ImportError:
    # statsmodels not available — generate a manual seasonal pattern chart
    monthly_avg = net_daily["total_units"].resample("ME").mean()
    overall_avg = monthly_avg.mean()
    seasonal_idx = monthly_avg / overall_avg

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(monthly_avg.index, monthly_avg.values, color=DHL_RED,
            linewidth=2, marker="o", markersize=5, label="Monthly Avg Demand")
    ax.axhline(overall_avg, color="#333333", linewidth=1.5, linestyle="--",
               label=f"24-Month Avg ({overall_avg:,.0f} units/day)")
    ax.fill_between(monthly_avg.index, overall_avg, monthly_avg.values,
                    where=monthly_avg.values >= overall_avg,
                    color=DHL_RED, alpha=0.15, label="Above average")
    ax.fill_between(monthly_avg.index, overall_avg, monthly_avg.values,
                    where=monthly_avg.values < overall_avg,
                    color="#90A4AE", alpha=0.15, label="Below average")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
    ax.set_ylabel("Avg Daily Units", fontsize=10)
    ax.set_title("Monthly Average Demand vs 24-Month Baseline\n"
                 "Proxy for Seasonal Pattern", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, "08_seasonal_decomposition.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  → Saved 08_seasonal_decomposition.png (proxy — install statsmodels for full decomp)")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3: DEMAND VARIABILITY HEATMAP — MONTH × CATEGORY
# ─────────────────────────────────────────────────────────────────────────────
print("[3/5] Demand variability heatmap (CV by month × category)...")
df_raw["month"] = df_raw["Date"].dt.month
df_raw["year_month"] = df_raw["Date"].dt.to_period("M").astype(str)

cv_data = (df_raw.groupby(["year_month", "Category"])["Quantity_Demanded"]
           .agg(["mean", "std"])
           .reset_index())
cv_data["CV"] = cv_data["std"] / cv_data["mean"]
cv_pivot = cv_data.pivot(index="Category", columns="year_month", values="CV").fillna(0)

fig, ax = plt.subplots(figsize=(16, 5))
cmap = plt.cm.RdYlGn_r
im = ax.imshow(cv_pivot.values, cmap=cmap, aspect="auto", vmin=0.1, vmax=0.8)
ax.set_yticks(range(len(cv_pivot.index)))
ax.set_yticklabels(cv_pivot.index.tolist(), fontsize=9)
col_labels = cv_pivot.columns.tolist()
show_cols  = [c for c in col_labels if c.endswith("-01") or c.endswith("-07")]
ax.set_xticks([col_labels.index(c) for c in show_cols if c in col_labels])
ax.set_xticklabels(show_cols, rotation=45, ha="right", fontsize=8)
plt.colorbar(im, ax=ax, label="Coefficient of Variation (CV)", shrink=0.8)
ax.set_title("Demand Variability Heatmap — CV by Month × Category\n"
             "Red = high variability (harder to forecast) · Green = stable",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "09_demand_variability_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 09_demand_variability_heatmap.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4: BUSINESS IMPACT — STOCKOUT DAYS → LOST REVENUE BY SEGMENT
# ─────────────────────────────────────────────────────────────────────────────
print("[4/5] Business impact — stockout lost revenue...")
impact = (df_raw[df_raw["Stockout_Flag"] == 1]
          .groupby(["ABC_Class", "Category"])
          .agg(
              stockout_days=("Stockout_Flag", "sum"),
              unfulfilled_units=("Quantity_Demanded", lambda x:
                  (df_raw.loc[x.index, "Quantity_Demanded"] -
                   df_raw.loc[x.index, "Quantity_Fulfilled"]).sum()),
              avg_unit_price=("Unit_Price", "mean")
          )
          .reset_index())
impact["est_lost_revenue"] = impact["unfulfilled_units"] * impact["avg_unit_price"]

impact_abc = (impact.groupby("ABC_Class")
              .agg(stockout_days=("stockout_days","sum"),
                   unfulfilled_units=("unfulfilled_units","sum"),
                   est_lost_revenue=("est_lost_revenue","sum"))
              .reset_index()
              .sort_values("ABC_Class"))

print("\n  Business Impact by ABC Class:")
print(impact_abc.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
colors_abc = [CLASS_COLOR.get(c, "#888") for c in impact_abc["ABC_Class"]]

axes[0].bar(impact_abc["ABC_Class"], impact_abc["unfulfilled_units"] / 1000,
            color=colors_abc, edgecolor="white", linewidth=0.8)
for bar, val in zip(axes[0].patches, impact_abc["unfulfilled_units"]):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f"{val/1000:.1f}K", ha="center", va="bottom", fontsize=10, fontweight="bold")
axes[0].set_ylabel("Unfulfilled Units (thousands)", fontsize=10)
axes[0].set_title("Unfulfilled Units by ABC Class", fontsize=11, fontweight="bold")
axes[0].grid(axis="y", linestyle="--", alpha=0.4)

axes[1].bar(impact_abc["ABC_Class"], impact_abc["est_lost_revenue"] / 1e6,
            color=colors_abc, edgecolor="white", linewidth=0.8)
for bar, val in zip(axes[1].patches, impact_abc["est_lost_revenue"]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                 f"${val/1e6:.1f}M", ha="center", va="bottom", fontsize=10, fontweight="bold")
axes[1].set_ylabel("Estimated Lost Revenue ($M)", fontsize=10)
axes[1].set_title("Estimated Lost Revenue by ABC Class", fontsize=11, fontweight="bold")
axes[1].grid(axis="y", linestyle="--", alpha=0.4)

fig.suptitle("Business Impact of Stockouts — Unfulfilled Units & Estimated Lost Revenue\n"
             "A-class stockouts carry disproportionate financial consequence",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "10_stockout_business_impact.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 10_stockout_business_impact.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 5 + 6 + 7: FORECAST ACCURACY — 14-DAY MA MAPE BY ABC CLASS
# ─────────────────────────────────────────────────────────────────────────────
print("[5/5] Forecast accuracy baseline (14-day MA MAPE)...")

sku_daily = (df_raw.groupby(["SKU_ID", "Date", "ABC_Class"])
             ["Quantity_Demanded"].sum()
             .reset_index()
             .sort_values(["SKU_ID","Date"]))

mape_results = []
for sku_id, grp in sku_daily.groupby("SKU_ID"):
    grp = grp.set_index("Date").sort_index()
    if len(grp) < 30:
        continue
    abc = grp["ABC_Class"].iloc[0]
    grp["MA14"] = grp["Quantity_Demanded"].rolling(14, min_periods=14).mean()
    valid = grp.dropna(subset=["MA14"])
    if len(valid) < 10:
        continue
    actual  = valid["Quantity_Demanded"].values
    forecast = valid["MA14"].values
    nonzero  = actual > 0
    if nonzero.sum() < 5:
        continue
    mape = np.mean(np.abs((actual[nonzero] - forecast[nonzero]) / actual[nonzero])) * 100
    mape_results.append({"SKU_ID": sku_id, "ABC_Class": abc, "MAPE": mape})

df_mape = pd.DataFrame(mape_results)
mape_by_class = df_mape.groupby("ABC_Class")["MAPE"].agg(["mean","median","std"]).reset_index()
mape_by_class.columns = ["ABC_Class","mean_mape","median_mape","std_mape"]
print("\n  14-Day MA Forecast Accuracy (MAPE %) by ABC Class:")
print(mape_by_class.to_string(index=False))

# Figure 5: MAPE distribution box plot
fig, ax = plt.subplots(figsize=(10, 5))
data_by_class = [df_mape[df_mape["ABC_Class"]==c]["MAPE"].values
                 for c in ["A","B","C"]]
bp = ax.boxplot(data_by_class, labels=["A-Class","B-Class","C-Class"],
                patch_artist=True, widths=0.45,
                medianprops=dict(color="white", linewidth=2))
for patch, color in zip(bp["boxes"], [CLASS_COLOR["A"], CLASS_COLOR["B"], CLASS_COLOR["C"]]):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
ax.set_ylabel("MAPE (%) — 14-Day Moving Average", fontsize=10)
ax.set_title("Forecast Accuracy Baseline — 14-Day MA MAPE by ABC Class\n"
             "Lower MAPE = easier to forecast (more predictable demand)",
             fontsize=12, fontweight="bold")
ax.grid(axis="y", linestyle="--", alpha=0.4)
for i, (cls, row) in enumerate(mape_by_class.iterrows()):
    ax.text(i + 1, mape_by_class.iloc[i]["mean_mape"] + 1.5,
            f"Mean: {mape_by_class.iloc[i]['mean_mape']:.1f}%",
            ha="center", fontsize=8, color="#333333")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "11_mape_baseline_by_abc.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 11_mape_baseline_by_abc.png")

# Figure 6: Top 5 A-class SKUs: actual vs MA14
top_a_skus = (df_mape[df_mape["ABC_Class"]=="A"]
              .nsmallest(5, "MAPE")["SKU_ID"].tolist())

fig, axes = plt.subplots(1, 5, figsize=(18, 4))
fig.suptitle("Top 5 A-Class SKUs — Actual Demand vs 14-Day MA Forecast\n"
             "(Best MAPE performers in A-class)", fontsize=11, fontweight="bold")
for ax, sku in zip(axes, top_a_skus):
    grp = (sku_daily[sku_daily["SKU_ID"]==sku]
           .set_index("Date").sort_index())
    grp["MA14"] = grp["Quantity_Demanded"].rolling(14, min_periods=3).mean()
    ax.plot(grp.index, grp["Quantity_Demanded"], color="#BDBDBD", linewidth=0.7, label="Actual")
    ax.plot(grp.index, grp["MA14"], color=DHL_RED, linewidth=1.5, label="14-Day MA")
    mape_val = df_mape[df_mape["SKU_ID"]==sku]["MAPE"].values[0]
    ax.set_title(f"{sku}\nMAPE={mape_val:.1f}%", fontsize=8, fontweight="bold")
    ax.tick_params(labelsize=6)
    ax.xaxis.set_tick_params(rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    if ax == axes[0]:
        ax.legend(fontsize=7)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "12_aclass_forecast_examples.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 12_aclass_forecast_examples.png")

# Figure 7: Monthly demand variability by ABC class
monthly_abc = (df_raw.groupby(["year_month", "ABC_Class"])["Quantity_Demanded"]
               .sum().reset_index())
pivot_abc = monthly_abc.pivot(index="year_month", columns="ABC_Class",
                               values="Quantity_Demanded").fillna(0)

fig, ax = plt.subplots(figsize=(14, 5))
for cls in ["A","B","C"]:
    if cls in pivot_abc.columns:
        ax.plot(range(len(pivot_abc)), pivot_abc[cls], color=CLASS_COLOR[cls],
                linewidth=2.0, label=f"{cls}-Class", marker="o", markersize=3)
ax.set_xticks(range(len(pivot_abc)))
ax.set_xticklabels(pivot_abc.index.tolist(), rotation=45, ha="right", fontsize=7)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
ax.set_ylabel("Units Demanded (thousands)", fontsize=10)
ax.set_title("Monthly Demand by ABC Class — 24-Month Period\n"
             "A-class drives volume concentration; C-class tail is large",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "13_monthly_demand_by_abc.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 13_monthly_demand_by_abc.png")

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT: outputs/demand_summary.csv
# ─────────────────────────────────────────────────────────────────────────────
print("\nBuilding demand_summary.csv...")

sku_summary = (df_raw.groupby(["SKU_ID","ABC_Class","Category"])
               .agg(
                   total_units=("Quantity_Demanded","sum"),
                   total_revenue=("Revenue","sum"),
                   avg_daily_demand=("Quantity_Demanded","mean"),
                   std_daily_demand=("Quantity_Demanded","std"),
                   stockout_days=("Stockout_Flag","sum"),
                   total_days=("Stockout_Flag","count"),
                   avg_unit_price=("Unit_Price","mean")
               )
               .reset_index())

sku_summary["CV"] = sku_summary["std_daily_demand"] / sku_summary["avg_daily_demand"]
sku_summary["stockout_rate_pct"] = (sku_summary["stockout_days"] /
                                     sku_summary["total_days"] * 100)
sku_summary["est_lost_revenue"] = (
    sku_summary["stockout_days"] *
    sku_summary["avg_daily_demand"] *
    sku_summary["avg_unit_price"]
)

# Add MAPE from forecast baseline
mape_map = df_mape.set_index("SKU_ID")["MAPE"].to_dict()
sku_summary["mape_14day_ma"] = sku_summary["SKU_ID"].map(mape_map)

# Add 14-day and 28-day MA for last available month
last_30 = df_raw[df_raw["Date"] >= df_raw["Date"].max() - pd.Timedelta(days=30)]
ma_recent = (last_30.groupby("SKU_ID")["Quantity_Demanded"]
             .mean().reset_index()
             .rename(columns={"Quantity_Demanded":"avg_daily_demand_last30d"}))
sku_summary = sku_summary.merge(ma_recent, on="SKU_ID", how="left")

# XYZ class assignment
sku_summary["XYZ_Class"] = pd.cut(
    sku_summary["CV"],
    bins=[-np.inf, 0.30, 0.70, np.inf],
    labels=["X","Y","Z"]
)
sku_summary["Segment"] = sku_summary["ABC_Class"] + sku_summary["XYZ_Class"].astype(str)

cols_order = [
    "SKU_ID","ABC_Class","XYZ_Class","Segment","Category",
    "total_units","total_revenue","avg_daily_demand","std_daily_demand","CV",
    "avg_daily_demand_last30d","stockout_days","total_days","stockout_rate_pct",
    "est_lost_revenue","avg_unit_price","mape_14day_ma"
]
sku_summary = sku_summary[[c for c in cols_order if c in sku_summary.columns]]
sku_summary.sort_values(["ABC_Class","XYZ_Class","total_revenue"],
                         ascending=[True,True,False], inplace=True)

out_path = os.path.join(OUTPUTS, "demand_summary.csv")
sku_summary.to_csv(out_path, index=False)
print(f"  → Saved demand_summary.csv — {len(sku_summary):,} rows, {len(sku_summary.columns)} columns")
print(f"     Path: {out_path}")

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("  ANALYSIS COMPLETE")
print(f"  Figures saved: {FIGURES}")
print(f"  Outputs saved: {OUTPUTS}")
print(f"  Figures: 07–13 (7 PNG files)")
print(f"  Export:  demand_summary.csv ({len(sku_summary):,} SKU-level rows)")
print()

print("  MAPE Summary:")
print(mape_by_class.to_string(index=False))

print()
print("  Business Impact (Estimated Lost Revenue by ABC Class):")
for _, row in impact_abc.iterrows():
    print(f"    {row['ABC_Class']}-class: ${row['est_lost_revenue']/1e6:.1f}M lost across "
          f"{int(row['unfulfilled_units']):,} unfulfilled units")

print(f"\n  Next: dashboard/forecast_dashboard.html — Plotly interactive build")
print(f"{'='*70}\n")
