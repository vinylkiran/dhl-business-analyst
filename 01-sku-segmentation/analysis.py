"""
DHL Supply Chain | SKU Segmentation — ABC/XYZ Classification Analysis
BA/DA Portfolio | Project 1 | Step 3 of 4
Author: Vinyl Kiran Anipe

Computes ABC classification (revenue-based Pareto) and XYZ classification
(demand variability / CV) for 1,664 active DHL SKUs. Applies replenishment
policy framework and exports segmented SKU list for dashboard use.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings("ignore")

# ── PATHS ─────────────────────────────────────────────────────────────────
DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/01-sku-segmentation/")
FIGURES = PROJECT + "figures/"
os.makedirs(FIGURES, exist_ok=True)

# ── STYLE ─────────────────────────────────────────────────────────────────
plt.rcParams.update({"figure.facecolor":"white","axes.facecolor":"white",
                     "axes.grid":True,"grid.alpha":0.3,"font.size":11})
DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
C          = {"A":"#D40511","B":"#FF8C00","C":"#4CAF50"}
XC         = {"X":"#1565C0","Y":"#F57F17","Z":"#B71C1C"}

print("="*65)
print("  DHL SKU SEGMENTATION — ABC/XYZ CLASSIFICATION")
print("="*65)

# ── 1. LOAD DATA ──────────────────────────────────────────────────────────
print("\n[1/7] Loading data...")
skus   = pd.read_csv(DATA+"sku_master.csv")
demand = pd.read_csv(DATA+"daily_demand.csv", parse_dates=["Date"])
active = skus[skus.Active_Flag==1].copy()
print(f"  SKU master   : {len(skus):,} rows  |  {skus.Active_Flag.sum():,} active")
print(f"  Daily demand : {len(demand):,} rows  |  {demand.Date.min().date()} → {demand.Date.max().date()}")

# ── 2. ABC CLASSIFICATION (Revenue Pareto) ────────────────────────────────
print("\n[2/7] Computing ABC classification...")

sku_rev = (demand.groupby("SKU_ID")
           .agg(Total_Revenue    =("Revenue","sum"),
                Total_Units      =("Quantity_Fulfilled","sum"),
                Total_Demand_Days=("Date","count"))
           .reset_index()
           .sort_values("Total_Revenue", ascending=False))

gt = sku_rev.Total_Revenue.sum()
sku_rev["Revenue_Pct"]     = sku_rev.Total_Revenue / gt * 100
sku_rev["Cumulative_Pct"]  = sku_rev.Revenue_Pct.cumsum()
sku_rev["ABC_Class"]       = np.where(sku_rev.Cumulative_Pct<=80,"A",
                             np.where(sku_rev.Cumulative_Pct<=95,"B","C"))

abc_sum = sku_rev.groupby("ABC_Class").agg(
    SKU_Count    =("SKU_ID","count"),
    Total_Revenue=("Total_Revenue","sum"),
    Revenue_Pct  =("Revenue_Pct","sum")).reset_index()

print(f"\n  {'Class':<8}{'SKUs':>8}{'Revenue ($)':>18}{'Rev %':>8}")
print(f"  {'-'*45}")
for _,r in abc_sum.iterrows():
    print(f"  {r.ABC_Class:<8}{r.SKU_Count:>8,}{r.Total_Revenue:>18,.0f}{r.Revenue_Pct:>7.1f}%")

# ── 3. XYZ CLASSIFICATION (Coefficient of Variation) ─────────────────────
print("\n[3/7] Computing XYZ classification...")

sku_cv = (demand.groupby("SKU_ID")
          .agg(Mean_Demand=("Quantity_Demanded","mean"),
               Std_Demand =("Quantity_Demanded","std"))
          .reset_index())
sku_cv["CV"]        = sku_cv.Std_Demand / sku_cv.Mean_Demand.replace(0,np.nan)
sku_cv["XYZ_Class"] = np.where(sku_cv.CV<0.30,"X",
                      np.where(sku_cv.CV<0.70,"Y","Z"))

xyz_sum = sku_cv.groupby("XYZ_Class").agg(
    SKU_Count=("SKU_ID","count"),
    Avg_CV   =("CV","mean"),
    Min_CV   =("CV","min"),
    Max_CV   =("CV","max")).reset_index()

print(f"\n  {'Class':<8}{'SKUs':>8}{'Avg CV':>10}{'Min CV':>10}{'Max CV':>10}")
print(f"  {'-'*48}")
for _,r in xyz_sum.iterrows():
    print(f"  {r.XYZ_Class:<8}{r.SKU_Count:>8,}{r.Avg_CV:>10.3f}{r.Min_CV:>10.3f}{r.Max_CV:>10.3f}")

# ── 4. COMBINED ABC/XYZ SEGMENTS ─────────────────────────────────────────
print("\n[4/7] Building combined segment matrix...")

# Merge all assignments
segs = (sku_rev[["SKU_ID","Total_Revenue","Total_Units","Revenue_Pct","ABC_Class"]]
        .merge(sku_cv[["SKU_ID","CV","XYZ_Class"]], on="SKU_ID")
        .merge(active[["SKU_ID","Category","Unit_Price","Unit_Cost","Storage_Type",
                        "Lead_Time_Days","Safety_Stock_Qty","Reorder_Point_Qty",
                        "Primary_Warehouse"]], on="SKU_ID"))
segs["Segment"] = segs.ABC_Class + segs.XYZ_Class

# Stockout stats per SKU
sku_so = (demand.groupby("SKU_ID")
          .agg(Stockout_Days=("Stockout_Flag","sum"),
               Demand_Days  =("Date","count"))
          .reset_index())
sku_so["Stockout_Rate_Pct"] = (sku_so.Stockout_Days/sku_so.Demand_Days*100).round(2)
segs = segs.merge(sku_so, on="SKU_ID", how="left")

mat = (segs.groupby(["ABC_Class","XYZ_Class"])
       .agg(SKU_Count         =("SKU_ID","count"),
            Total_Revenue     =("Total_Revenue","sum"),
            Avg_CV            =("CV","mean"),
            Avg_Stockout_Rate =("Stockout_Rate_Pct","mean"))
       .reset_index())
mat["Segment"] = mat.ABC_Class + mat.XYZ_Class

print(f"\n  {'Segment':<10}{'SKUs':>8}{'Revenue ($)':>20}{'Avg CV':>10}{'Stockout%':>12}")
print(f"  {'-'*63}")
for _,r in mat.sort_values("Segment").iterrows():
    print(f"  {r.Segment:<10}{r.SKU_Count:>8,}{r.Total_Revenue:>20,.0f}{r.Avg_CV:>10.3f}{r.Avg_Stockout_Rate:>11.2f}%")

# ── 5. REPLENISHMENT POLICY ───────────────────────────────────────────────
print("\n[5/7] Applying replenishment policy framework...")

POLICY = {
    "AX":{"SS":1.5,"ROP":1.3,"Freq":"Weekly",         "Zone":"Prime Pick-Face","Flag":"Critical"},
    "AY":{"SS":2.0,"ROP":1.6,"Freq":"Twice Weekly",   "Zone":"Prime Pick-Face","Flag":"Critical"},
    "AZ":{"SS":2.5,"ROP":2.0,"Freq":"Manual Review",  "Zone":"Prime Pick-Face","Flag":"Critical"},
    "BX":{"SS":1.2,"ROP":1.1,"Freq":"Bi-Weekly",      "Zone":"Standard Pick", "Flag":"Standard"},
    "BY":{"SS":1.5,"ROP":1.3,"Freq":"Weekly",         "Zone":"Standard Pick", "Flag":"Standard"},
    "BZ":{"SS":1.8,"ROP":1.5,"Freq":"Weekly+Review",  "Zone":"Standard Pick", "Flag":"Monitor"},
    "CX":{"SS":0.8,"ROP":0.9,"Freq":"Monthly",        "Zone":"Reserve",       "Flag":"Reduce"},
    "CY":{"SS":1.0,"ROP":1.0,"Freq":"Monthly",        "Zone":"Reserve",       "Flag":"Review"},
    "CZ":{"SS":0.5,"ROP":0.7,"Freq":"On-Demand",      "Zone":"Reserve/Delist","Flag":"Delist"},
}
segs["SS_Multiplier"]        = segs.Segment.map({k:v["SS"]   for k,v in POLICY.items()})
segs["ROP_Multiplier"]       = segs.Segment.map({k:v["ROP"]  for k,v in POLICY.items()})
segs["Reorder_Frequency"]    = segs.Segment.map({k:v["Freq"] for k,v in POLICY.items()})
segs["Recommended_Zone"]     = segs.Segment.map({k:v["Zone"] for k,v in POLICY.items()})
segs["Priority_Flag"]        = segs.Segment.map({k:v["Flag"] for k,v in POLICY.items()})
segs["Adj_Safety_Stock"]     = (segs.Safety_Stock_Qty  * segs.SS_Multiplier).round(0).astype(int)
segs["Adj_Reorder_Point"]    = (segs.Reorder_Point_Qty * segs.ROP_Multiplier).round(0).astype(int)
print(f"  Policy applied to {len(segs):,} SKUs across {segs.Segment.nunique()} active segments")

# ── 6. VISUALISATIONS ─────────────────────────────────────────────────────
print("\n[6/7] Generating charts...")

# Fig 1 — Pareto Chart
top = min(300, len(sku_rev))
fig, ax1 = plt.subplots(figsize=(14,6))
bar_c = [C[c] for c in sku_rev.head(top).ABC_Class]
ax1.bar(range(1,top+1), sku_rev.head(top).Revenue_Pct,
        color=bar_c, alpha=0.8, width=1.0)
ax1.set_xlabel("SKU Rank (by Revenue, Descending)",fontsize=12)
ax1.set_ylabel("Individual SKU Revenue %",fontsize=11,color="grey")
ax2 = ax1.twinx()
ax2.plot(range(1,top+1), sku_rev.head(top).Cumulative_Pct,
         color=DHL_RED, linewidth=2.5, label="Cumulative Revenue %")
ax2.axhline(80,color="orange",linestyle="--",linewidth=1.5,alpha=0.9,label="80% — A/B boundary")
ax2.axhline(95,color="green", linestyle="--",linewidth=1.5,alpha=0.9,label="95% — B/C boundary")
ax2.set_ylabel("Cumulative Revenue %",fontsize=11)
ax2.set_ylim(0,105)
patches = [mpatches.Patch(color=C[k],label=f"Class {k}") for k in ["A","B","C"]]
ax2.legend(handles=patches+ax2.get_lines(), loc="center right",fontsize=10)
plt.title("DHL SKU Revenue Pareto — ABC Classification",fontsize=14,fontweight="bold",pad=15)
plt.tight_layout()
plt.savefig(FIGURES+"01_pareto_chart.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 01_pareto_chart.png")

# Fig 2 — ABC Distribution
fig, axes = plt.subplots(1,2,figsize=(13,5))
abc_i = abc_sum.set_index("ABC_Class")
for ax, col, ylabel, suffix in [
    (axes[0],"SKU_Count","Number of SKUs",""),
    (axes[1],"Revenue_Pct","% of Total Revenue","%")]:
    bars = ax.bar(abc_i.index, abc_i[col],
                  color=[C[c] for c in abc_i.index], edgecolor="white",linewidth=1.5)
    ax.set_title(f"{'SKU Count' if col=='SKU_Count' else 'Revenue Share'} by ABC Class",fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    for b,v in zip(bars,abc_i[col]):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                f"{v:,.0f}{suffix}",ha="center",va="bottom",fontweight="bold",fontsize=10)
plt.suptitle("ABC Classification — SKUs vs Revenue Impact",fontsize=13,fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURES+"02_abc_distribution.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 02_abc_distribution.png")

# Fig 3 — CV Histogram
fig, ax = plt.subplots(figsize=(12,5))
for xyz,col in XC.items():
    sub = sku_cv[sku_cv.XYZ_Class==xyz]["CV"].dropna()
    if len(sub):
        ax.hist(sub,bins=40,color=col,alpha=0.7,
                label=f"Class {xyz}  (n={len(sub):,})",edgecolor="white")
ax.axvline(0.30,color="black",linestyle="--",linewidth=1.5,label="X/Y boundary (CV=0.30)")
ax.axvline(0.70,color="grey", linestyle="--",linewidth=1.5,label="Y/Z boundary (CV=0.70)")
ax.set_xlabel("Coefficient of Variation (CV)",fontsize=12)
ax.set_ylabel("Number of SKUs",fontsize=12)
ax.set_title("Demand Variability Distribution — XYZ Classification",fontsize=13,fontweight="bold")
ax.legend(fontsize=11)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(FIGURES+"03_xyz_cv_distribution.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 03_xyz_cv_distribution.png")

# Fig 4 — ABC/XYZ Heatmap
fig, axes = plt.subplots(1,2,figsize=(14,5))
for ax,metric,title,fmt in [
    (axes[0],"SKU_Count",  "SKU Count per Segment",    ".0f"),
    (axes[1],"Total_Revenue","Revenue per Segment ($)",",.0f")]:
    piv = mat.pivot(index="ABC_Class",columns="XYZ_Class",values=metric).fillna(0)
    piv = piv.reindex(index=[r for r in ["A","B","C"] if r in piv.index],
                      columns=[c for c in ["X","Y","Z"] if c in piv.columns])
    sns.heatmap(piv,annot=True,fmt=".0f" if metric=="SKU_Count" else ".2e",
                cmap="YlOrRd",ax=ax,linewidths=0.5,cbar_kws={"shrink":0.8},
                annot_kws={"size":13,"weight":"bold"})
    ax.set_title(title,fontweight="bold",pad=10)
    ax.set_xlabel("XYZ Class (Demand Variability)")
    ax.set_ylabel("ABC Class (Revenue Value)")
plt.suptitle("DHL ABC/XYZ Segment Matrix",fontsize=13,fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURES+"04_abcxyz_heatmap.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 04_abcxyz_heatmap.png")

# Fig 5 — Stockout Asymmetry
so_abc = segs.groupby("ABC_Class").agg(
    Avg_Rate =("Stockout_Rate_Pct","mean"),
    Unfulfilled=("Stockout_Days","sum")).reset_index()
fig, axes = plt.subplots(1,2,figsize=(13,5))
for ax, col, ylabel, div, sfx in [
    (axes[0],"Avg_Rate",    "Stockout Rate %",      1,   ""),
    (axes[1],"Unfulfilled", "Unfulfilled Units (k)",1000,"k")]:
    bars = ax.bar(so_abc.ABC_Class, so_abc[col]/div,
                  color=[C[c] for c in so_abc.ABC_Class],edgecolor="white")
    ax.set_ylabel(ylabel); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    for b,v in zip(bars,so_abc[col]/div):
        ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.01*b.get_height(),
                f"{v:,.1f}{sfx}",ha="center",va="bottom",fontweight="bold")
axes[0].set_title("Average Stockout Rate by ABC Class",fontweight="bold")
axes[0].axhline(so_abc.Avg_Rate.mean(),color="grey",linestyle="--",
                linewidth=1.5,label=f"Network Avg")
axes[0].legend()
axes[1].set_title("Total Unfulfilled Units by ABC Class",fontweight="bold")
plt.suptitle("Stockout Asymmetry — Same Rate, Different Consequences",
             fontsize=13,fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURES+"05_stockout_asymmetry.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 05_stockout_asymmetry.png")

# Fig 6 — Category Revenue
cat_rev = segs.groupby("Category").Total_Revenue.sum().sort_values()
fig, ax  = plt.subplots(figsize=(11,6))
bars = ax.barh(cat_rev.index, cat_rev.values/1e9,
               color=[DHL_RED if v>cat_rev.median() else "#FF8C00" for v in cat_rev.values],
               edgecolor="white")
for b,v in zip(bars,cat_rev.values):
    ax.text(b.get_width()+0.05,b.get_y()+b.get_height()/2,
            f"${v/1e9:.1f}B",va="center",fontsize=10)
ax.set_xlabel("Total Revenue ($B)",fontsize=12)
ax.set_title("Revenue by Product Category — 24-Month Period",
             fontsize=13,fontweight="bold")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(FIGURES+"06_category_revenue.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 06_category_revenue.png")

# Fig 7 — Top 20 SKUs Revenue + Stockout
top20 = segs.nlargest(20,"Total_Revenue").reset_index(drop=True)
fig, ax1 = plt.subplots(figsize=(14,6))
bars = ax1.bar(range(len(top20)), top20.Total_Revenue/1e6,
               color=[C[c] for c in top20.ABC_Class],alpha=0.85,edgecolor="white")
ax1.set_ylabel("Total Revenue ($M)",fontsize=12)
ax1.set_xticks(range(len(top20)))
ax1.set_xticklabels([s[-9:] for s in top20.SKU_ID],rotation=45,ha="right",fontsize=8)
ax2 = ax1.twinx()
ax2.plot(range(len(top20)),top20.Stockout_Rate_Pct,
         color=DHL_YELLOW,linewidth=2.5,marker="o",markersize=7,
         markeredgecolor=DHL_RED,label="Stockout Rate %")
ax2.axhline(3.0,color="grey",linestyle="--",linewidth=1.5,alpha=0.8,label="Network Avg (3.0%)")
ax2.set_ylabel("Stockout Rate %",fontsize=12)
ax2.legend(loc="upper right",fontsize=10)
plt.title("Top 20 SKUs by Revenue — Stockout Rate Overlay",
          fontsize=13,fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURES+"07_top20_revenue_stockout.png",dpi=150,bbox_inches="tight")
plt.close()
print("  ✓ 07_top20_revenue_stockout.png")

# ── 7. EXPORT OUTPUTS ─────────────────────────────────────────────────────
print("\n[7/7] Exporting outputs...")

out_cols = ["SKU_ID","Category","Segment","ABC_Class","XYZ_Class","CV",
            "Total_Revenue","Total_Units","Revenue_Pct","Stockout_Rate_Pct",
            "Safety_Stock_Qty","Adj_Safety_Stock",
            "Reorder_Point_Qty","Adj_Reorder_Point",
            "SS_Multiplier","ROP_Multiplier","Reorder_Frequency",
            "Recommended_Zone","Priority_Flag",
            "Unit_Price","Unit_Cost","Lead_Time_Days","Primary_Warehouse"]
segs[out_cols].to_csv(PROJECT+"sku_segments.csv",index=False)
print(f"  ✓ sku_segments.csv         {len(segs):,} rows")

summ = (segs.groupby("Segment")
        .agg(SKU_Count          =("SKU_ID","count"),
             Total_Revenue      =("Total_Revenue","sum"),
             Avg_Stockout_Rate  =("Stockout_Rate_Pct","mean"),
             Avg_CV             =("CV","mean"),
             Avg_Adj_SafetyStock=("Adj_Safety_Stock","mean"))
        .round(2).reset_index())
summ["Revenue_Pct"] = (summ.Total_Revenue/summ.Total_Revenue.sum()*100).round(2)
summ.to_csv(PROJECT+"segment_summary.csv",index=False)
print(f"  ✓ segment_summary.csv      {len(summ)} segments")

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("  ANALYSIS COMPLETE")
print(f"{'='*65}")
print(f"  Active segments : {segs.Segment.nunique()}")
print(f"  SKUs classified : {len(segs):,}")
print(f"  Charts saved    : 7  →  figures/")
print(f"  Outputs saved   : sku_segments.csv  |  segment_summary.csv")
print(f"\n  Segment breakdown:")
for _,r in summ.sort_values("Segment").iterrows():
    print(f"    {r.Segment}  {r.SKU_Count:>6,} SKUs  "
          f"{r.Revenue_Pct:>6.1f}% rev  "
          f"Avg stockout {r.Avg_Stockout_Rate:.2f}%")
print(f"\n  Next → Step 4: Power BI Dashboard")
print(f"{'='*65}")
