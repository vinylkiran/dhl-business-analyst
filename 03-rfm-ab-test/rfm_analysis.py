"""
DHL Supply Chain | RFM Segmentation & A/B Test — RFM Analysis
BA/DA Portfolio | Project 3 | Step 2
Author: Vinyl Kiran Anipe

Computes RFM scores (1-5 quintiles, 5=best) for every customer.
Reference date: 2023-12-31. Assigns named segments and profiles each.
Exports: outputs/customer_rfm.csv, outputs/rfm_segments.csv
"""

import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import os

pd.set_option("display.width", 130)
pd.set_option("display.float_format", "{:,.2f}".format)

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/03-rfm-ab-test/")
FIGURES = os.path.join(PROJECT, "figures")
OUTPUTS = os.path.join(PROJECT, "outputs")
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
REFERENCE_DATE = pd.Timestamp("2023-12-31")

SEGMENT_COLORS = {
    "Champions":          "#D40511",
    "Loyal Customers":    "#FF8C00",
    "Potential Loyalists":"#FFCC00",
    "New Customers":      "#4CAF50",
    "At Risk":            "#7B1FA2",
    "About to Sleep":     "#1565C0",
    "Lost":               "#607D8B",
}

# ── Load data ──────────────────────────────────────────────────────────────────
con = duckdb.connect()
con.execute(f"CREATE VIEW orders    AS SELECT * FROM read_csv_auto('{DATA}outbound_orders.csv')")
con.execute(f"CREATE VIEW customers AS SELECT * FROM read_csv_auto('{DATA}customers.csv')")

print("Loading customer and order data...")
df_orders = con.execute("""
    SELECT o.Order_ID, o.Order_Date, o.Customer_ID, o.Channel,
           o.Revenue, o.OTIF_Flag, o.On_Time_Flag, o.In_Full_Flag,
           c.Customer_Type, c.Region, c.Annual_Rev_Band
    FROM orders o
    JOIN customers c ON o.Customer_ID = c.Customer_ID
""").df()
df_orders["Order_Date"] = pd.to_datetime(df_orders["Order_Date"])

print(f"  Loaded {len(df_orders):,} orders | "
      f"{df_orders['Customer_ID'].nunique()} unique customers")

# ── STEP 1: Compute RFM raw metrics per customer ───────────────────────────────
print("\n[1/5] Computing RFM metrics...")
rfm_raw = (df_orders.groupby("Customer_ID")
           .agg(
               last_order_date=("Order_Date", "max"),
               frequency=("Order_ID", "nunique"),
               monetary=("Revenue", "sum"),
               avg_order_value=("Revenue", "mean"),
               otif_rate=("OTIF_Flag", "mean"),
               primary_channel=("Channel", lambda x: x.value_counts().index[0]),
               customer_type=("Customer_Type", "first"),
               region=("Region", "first"),
               annual_rev_band=("Annual_Rev_Band", "first"),
               total_orders=("Order_ID", "nunique")
           )
           .reset_index())

rfm_raw["recency"] = (REFERENCE_DATE - rfm_raw["last_order_date"]).dt.days

print(f"  RFM metrics computed for {len(rfm_raw):,} customers")
print(f"  Recency range: {rfm_raw['recency'].min()} – {rfm_raw['recency'].max()} days")
print(f"  Frequency range: {rfm_raw['frequency'].min()} – {rfm_raw['frequency'].max()} orders")
print(f"  Monetary range: ${rfm_raw['monetary'].min():,.0f} – ${rfm_raw['monetary'].max():,.0f}")

# ── STEP 2: Score each dimension 1–5 using quintiles ──────────────────────────
print("\n[2/5] Scoring RFM dimensions (quintiles, 5 = best)...")

# Recency: lower is better → invert (5 = lowest recency = most recent)
# Use rank to avoid duplicate bin edges in tight B2B distributions
rfm_raw["R_Score"] = pd.qcut(rfm_raw["recency"].rank(method="first"),
                               q=5, labels=[5, 4, 3, 2, 1],
                               duplicates="drop").astype(int)
# Frequency: higher is better
rfm_raw["F_Score"] = pd.qcut(rfm_raw["frequency"].rank(method="first"),
                               q=5, labels=[1, 2, 3, 4, 5],
                               duplicates="drop").astype(int)
# Monetary: higher is better
rfm_raw["M_Score"] = pd.qcut(rfm_raw["monetary"].rank(method="first"),
                               q=5, labels=[1, 2, 3, 4, 5],
                               duplicates="drop").astype(int)

rfm_raw["RFM_Score"] = rfm_raw["R_Score"] * 100 + rfm_raw["F_Score"] * 10 + rfm_raw["M_Score"]

# Print score distributions
print("\n  R_Score distribution:")
print(rfm_raw["R_Score"].value_counts().sort_index().to_string())
print("\n  F_Score distribution:")
print(rfm_raw["F_Score"].value_counts().sort_index().to_string())
print("\n  M_Score distribution:")
print(rfm_raw["M_Score"].value_counts().sort_index().to_string())

# ── STEP 3: Assign named segments ─────────────────────────────────────────────
print("\n[3/5] Assigning named segments...")

def assign_segment(row):
    r, f = row["R_Score"], row["F_Score"]
    if   (r == 5 and f >= 4):              return "Champions"
    elif (r >= 4 and f >= 4):              return "Loyal Customers"
    elif (r >= 3 and f >= 3):              return "Potential Loyalists"
    elif (r == 5 and f == 1):              return "New Customers"
    elif (r == 2 and f >= 3):              return "At Risk"
    elif (r == 2 and f <= 2):              return "About to Sleep"
    elif (r == 1):                         return "Lost"
    else:                                  return "Potential Loyalists"

rfm_raw["Segment"] = rfm_raw.apply(assign_segment, axis=1)

seg_counts = rfm_raw["Segment"].value_counts()
print("\n  Segment distribution:")
print(seg_counts.to_string())

# ── STEP 4: Profile each segment ──────────────────────────────────────────────
print("\n[4/5] Profiling segments...")

seg_profile = (rfm_raw.groupby("Segment")
               .agg(
                   customer_count=("Customer_ID", "count"),
                   avg_recency_days=("recency", "mean"),
                   avg_frequency=("frequency", "mean"),
                   total_revenue=("monetary", "sum"),
                   avg_monetary=("monetary", "mean"),
                   avg_order_value=("avg_order_value", "mean"),
                   avg_otif_rate=("otif_rate", "mean"),
               )
               .reset_index())

total_rev = rfm_raw["monetary"].sum()
seg_profile["revenue_pct"] = seg_profile["total_revenue"] / total_rev * 100
seg_profile["avg_recency_days"] = seg_profile["avg_recency_days"].round(0).astype(int)
seg_profile["avg_frequency"]    = seg_profile["avg_frequency"].round(1)
seg_profile["avg_monetary"]     = seg_profile["avg_monetary"].round(0)
seg_profile["avg_order_value"]  = seg_profile["avg_order_value"].round(0)
seg_profile["avg_otif_rate"]    = (seg_profile["avg_otif_rate"] * 100).round(2)
seg_profile["revenue_pct"]      = seg_profile["revenue_pct"].round(2)

# Add top region and primary channel per segment
seg_channel = (rfm_raw.groupby(["Segment","primary_channel"])["Customer_ID"]
               .count().reset_index()
               .sort_values("Customer_ID", ascending=False)
               .groupby("Segment").first()
               .rename(columns={"primary_channel":"top_channel","Customer_ID":"ch_count"})
               .reset_index())
seg_region = (rfm_raw.groupby(["Segment","region"])["Customer_ID"]
              .count().reset_index()
              .sort_values("Customer_ID", ascending=False)
              .groupby("Segment").first()
              .rename(columns={"region":"top_region","Customer_ID":"reg_count"})
              .reset_index())

seg_profile = (seg_profile
               .merge(seg_channel[["Segment","top_channel"]], on="Segment", how="left")
               .merge(seg_region[["Segment","top_region"]], on="Segment", how="left"))

seg_profile = seg_profile.sort_values("total_revenue", ascending=False)

print("\n  Segment Profile:")
cols_show = ["Segment","customer_count","avg_recency_days","avg_frequency",
             "avg_monetary","avg_order_value","avg_otif_rate","revenue_pct",
             "top_channel","top_region"]
print(seg_profile[cols_show].to_string(index=False))

# ── STEP 5: Save outputs ───────────────────────────────────────────────────────
print("\n[5/5] Saving outputs and figures...")

out_rfm = rfm_raw[["Customer_ID","customer_type","region","primary_channel",
                    "annual_rev_band","recency","frequency","monetary",
                    "avg_order_value","otif_rate","R_Score","F_Score","M_Score",
                    "RFM_Score","Segment","total_orders",
                    "last_order_date"]].copy()
out_rfm.to_csv(os.path.join(OUTPUTS, "customer_rfm.csv"), index=False)
print(f"  → Saved customer_rfm.csv — {len(out_rfm):,} rows")

seg_profile.to_csv(os.path.join(OUTPUTS, "rfm_segments.csv"), index=False)
print(f"  → Saved rfm_segments.csv — {len(seg_profile)} segments")

# ── FIGURES ────────────────────────────────────────────────────────────────────

# Figure 7: Segment size vs revenue bubble chart
fig, ax = plt.subplots(figsize=(12, 7))
for _, row in seg_profile.iterrows():
    color = SEGMENT_COLORS.get(row["Segment"], "#888")
    ax.scatter(row["avg_recency_days"], row["avg_frequency"],
               s=row["revenue_pct"] * 80, color=color, alpha=0.75, edgecolors="white", linewidth=1.5)
    ax.annotate(f"{row['Segment']}\n({row['customer_count']} customers, {row['revenue_pct']:.1f}% rev)",
                xy=(row["avg_recency_days"], row["avg_frequency"]),
                fontsize=8, ha="center", va="bottom",
                xytext=(0, 12), textcoords="offset points", fontweight="bold",
                color=SEGMENT_COLORS.get(row["Segment"], "#333"))
ax.set_xlabel("Average Recency (days — lower is more recent)", fontsize=10)
ax.set_ylabel("Average Order Frequency", fontsize=10)
ax.set_title("RFM Segment Map — Recency vs Frequency\n(Bubble size = % of total revenue)",
             fontsize=12, fontweight="bold")
ax.invert_xaxis()
ax.grid(linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "07_rfm_segment_map.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 07_rfm_segment_map.png")

# Figure 8: Revenue contribution bar
seg_sorted = seg_profile.sort_values("total_revenue", ascending=True)
fig, ax = plt.subplots(figsize=(11, 6))
colors_seg = [SEGMENT_COLORS.get(s, "#888") for s in seg_sorted["Segment"]]
bars = ax.barh(seg_sorted["Segment"], seg_sorted["total_revenue"]/1e6,
               color=colors_seg, edgecolor="white", alpha=0.85)
for bar, (_, row) in zip(bars, seg_sorted.iterrows()):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
            f"${row['total_revenue']/1e6:.1f}M ({row['revenue_pct']:.1f}%)",
            ha="left", va="center", fontsize=9, fontweight="bold")
ax.set_xlabel("Total Revenue ($M)", fontsize=10)
ax.set_title("Revenue Contribution by RFM Segment — 24-Month Period",
             fontsize=12, fontweight="bold")
ax.set_xlim(0, seg_sorted["total_revenue"].max()/1e6 * 1.25)
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "08_rfm_revenue_by_segment.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 08_rfm_revenue_by_segment.png")

# Figure 9: R score vs F score scatter (coloured by segment)
fig, ax = plt.subplots(figsize=(11, 8))
for seg, grp in rfm_raw.groupby("Segment"):
    ax.scatter(grp["R_Score"] + np.random.uniform(-0.2, 0.2, len(grp)),
               grp["F_Score"] + np.random.uniform(-0.2, 0.2, len(grp)),
               label=seg, color=SEGMENT_COLORS.get(seg, "#888"),
               alpha=0.6, s=60, edgecolors="white", linewidth=0.5)
ax.set_xlabel("Recency Score (5 = most recent)", fontsize=10)
ax.set_ylabel("Frequency Score (5 = highest frequency)", fontsize=10)
ax.set_title("Customer RFM Score Distribution — Recency vs Frequency\n(Jittered for visibility)",
             fontsize=12, fontweight="bold")
ax.set_xticks([1, 2, 3, 4, 5])
ax.set_yticks([1, 2, 3, 4, 5])
ax.legend(fontsize=9, loc="upper left")
ax.grid(linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "09_rfm_score_scatter.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 09_rfm_score_scatter.png")

# Figure 10: Segment profile heatmap — normalised metrics
metrics_hmap = seg_profile.set_index("Segment")[
    ["avg_recency_days","avg_frequency","avg_monetary","avg_order_value","avg_otif_rate"]
].copy()
metrics_hmap.columns = ["Avg Recency\n(days)","Avg Frequency","Avg Monetary\n($K)",
                         "Avg Order\nValue ($K)","OTIF\nRate (%)"]
metrics_hmap["Avg Monetary\n($K)"] /= 1000
metrics_hmap["Avg Order\nValue ($K)"] /= 1000
normed = (metrics_hmap - metrics_hmap.min()) / (metrics_hmap.max() - metrics_hmap.min() + 1e-9)
# Invert recency so lower days = greener
normed["Avg Recency\n(days)"] = 1 - normed["Avg Recency\n(days)"]

fig, ax = plt.subplots(figsize=(12, 6))
import matplotlib.colors as mcolors
cmap = plt.cm.RdYlGn
im = ax.imshow(normed.values, cmap=cmap, aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(normed.columns)))
ax.set_xticklabels(normed.columns, fontsize=9)
ax.set_yticks(range(len(normed.index)))
ax.set_yticklabels(normed.index, fontsize=9)
for i in range(len(normed.index)):
    for j, col in enumerate(metrics_hmap.columns):
        val = metrics_hmap.iloc[i, j]
        fmt = f"{val:.0f}" if val >= 1 else f"{val:.1f}"
        ax.text(j, i, fmt, ha="center", va="center", fontsize=8, fontweight="bold",
                color="white" if normed.iloc[i,j] < 0.3 or normed.iloc[i,j] > 0.7 else "#333")
plt.colorbar(im, ax=ax, label="Normalised score (green = better)", shrink=0.7)
ax.set_title("RFM Segment Profile Heatmap — Key Metrics Comparison\n"
             "Green = better performance on each metric",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "10_rfm_segment_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 10_rfm_segment_heatmap.png")

# Figure 11: At Risk segment deep dive
at_risk = rfm_raw[rfm_raw["Segment"] == "At Risk"].copy()
ar_by_type = at_risk.groupby("customer_type")["monetary"].sum().sort_values(ascending=False)
ar_by_region = at_risk.groupby("region")["monetary"].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle(f"At Risk Segment Deep Dive — {len(at_risk)} Customers, "
             f"${at_risk['monetary'].sum()/1e6:.1f}M Revenue at Risk",
             fontsize=12, fontweight="bold")
colors_ar = ["#7B1FA2", "#9C27B0", "#BA68C8", "#CE93D8", "#E1BEE7", "#F3E5F5"]
axes[0].bar(ar_by_type.index, ar_by_type.values/1e6,
            color=colors_ar[:len(ar_by_type)], edgecolor="white")
axes[0].set_ylabel("Revenue ($M)", fontsize=10)
axes[0].set_title("At Risk Revenue by Customer Type", fontsize=11, fontweight="bold")
axes[0].tick_params(axis="x", rotation=20)
axes[0].grid(axis="y", linestyle="--", alpha=0.4)
axes[1].bar(ar_by_region.index, ar_by_region.values/1e6,
            color=colors_ar[:len(ar_by_region)], edgecolor="white")
axes[1].set_ylabel("Revenue ($M)", fontsize=10)
axes[1].set_title("At Risk Revenue by Region", fontsize=11, fontweight="bold")
axes[1].tick_params(axis="x", rotation=20)
axes[1].grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "11_at_risk_deep_dive.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 11_at_risk_deep_dive.png")

print(f"\n{'='*70}")
print("  RFM ANALYSIS COMPLETE")
print(f"  Segments identified: {rfm_raw['Segment'].nunique()}")
print(f"  Customers scored:    {len(rfm_raw):,}")
print(f"  Figures saved:       07–11 (5 PNG files)")
print(f"  Exports:             customer_rfm.csv · rfm_segments.csv")
print()
print("  SEGMENT SUMMARY:")
for _, row in seg_profile.iterrows():
    print(f"    {row['Segment']:<22}: {int(row['customer_count']):>3} customers | "
          f"${row['total_revenue']/1e6:>6.1f}M ({row['revenue_pct']:.1f}% of total)")
print(f"\n  Next: ab_test.py — A/B test simulation for At Risk segment")
print(f"{'='*70}\n")
