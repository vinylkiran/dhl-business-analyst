"""
DHL Supply Chain | RFM Segmentation & A/B Test — SQL Exploration
BA/DA Portfolio | Project 3 | Step 1
Author: Vinyl Kiran Anipe

Explores customer behaviour using outbound_orders.csv and customers.csv.
Covers: order/revenue by customer type, frequency distribution, top 20
customers, OTIF rate, channel revenue, monthly active customer trend.
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
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/03-rfm-ab-test/")
FIGURES = os.path.join(PROJECT, "figures")
os.makedirs(FIGURES, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW orders    AS SELECT * FROM read_csv_auto('{DATA}outbound_orders.csv')")
con.execute(f"CREATE VIEW customers AS SELECT * FROM read_csv_auto('{DATA}customers.csv')")

DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
PALETTE    = ["#D40511","#FF8C00","#4CAF50","#1565C0","#7B1FA2","#00838F"]

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def run(label, sql):
    print(f"\n── {label}")
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    return df

# ── BLOCK 1: TOTAL ORDERS AND REVENUE BY CUSTOMER TYPE ────────────────────────
section("BLOCK 1 — ORDERS & REVENUE BY CUSTOMER TYPE")

df_type = run("1a. Orders, Revenue and Customer Count by Customer Type", """
    SELECT c.Customer_Type,
           COUNT(DISTINCT o.Customer_ID)          AS customer_count,
           COUNT(DISTINCT o.Order_ID)             AS total_orders,
           ROUND(SUM(o.Revenue), 0)               AS total_revenue,
           ROUND(AVG(o.Revenue), 2)               AS avg_order_value,
           ROUND(SUM(o.Revenue)*100.0/SUM(SUM(o.Revenue)) OVER(), 2) AS revenue_pct
    FROM orders o
    JOIN customers c ON o.Customer_ID = c.Customer_ID
    GROUP BY c.Customer_Type
    ORDER BY total_revenue DESC
""")

# Figure 1: Revenue by customer type
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Revenue & Order Volume by Customer Type", fontsize=13, fontweight="bold")
colors_t = PALETTE[:len(df_type)]

axes[0].bar(df_type["Customer_Type"], df_type["total_revenue"]/1e6,
            color=colors_t, edgecolor="white")
axes[0].set_ylabel("Total Revenue ($M)", fontsize=10)
axes[0].set_title("Revenue by Customer Type", fontsize=11, fontweight="bold")
axes[0].tick_params(axis="x", rotation=20)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
axes[0].grid(axis="y", linestyle="--", alpha=0.4)

axes[1].bar(df_type["Customer_Type"], df_type["avg_order_value"],
            color=colors_t, edgecolor="white")
axes[1].set_ylabel("Avg Order Value ($)", fontsize=10)
axes[1].set_title("Average Order Value by Customer Type", fontsize=11, fontweight="bold")
axes[1].tick_params(axis="x", rotation=20)
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
axes[1].grid(axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "01_revenue_by_customer_type.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 01_revenue_by_customer_type.png")

# ── BLOCK 2: ORDER FREQUENCY AND VALUE BY TYPE AND REGION ─────────────────────
section("BLOCK 2 — ORDER FREQUENCY & VALUE BY TYPE AND REGION")

df_freq_type = run("2a. Avg Order Frequency and Value by Customer Type", """
    WITH cust_orders AS (
        SELECT Customer_ID,
               COUNT(DISTINCT Order_ID)  AS order_count,
               ROUND(SUM(Revenue)/COUNT(DISTINCT Order_ID), 2) AS avg_order_val,
               ROUND(SUM(Revenue), 2) AS total_rev
        FROM orders GROUP BY Customer_ID
    )
    SELECT c.Customer_Type,
           ROUND(AVG(co.order_count), 1)   AS avg_orders_per_customer,
           ROUND(AVG(co.avg_order_val), 2) AS avg_order_value,
           ROUND(AVG(co.total_rev), 2)     AS avg_lifetime_value
    FROM cust_orders co
    JOIN customers c ON co.Customer_ID = c.Customer_ID
    GROUP BY c.Customer_Type
    ORDER BY avg_lifetime_value DESC
""")

df_freq_region = run("2b. Avg Order Frequency and Value by Region", """
    WITH cust_orders AS (
        SELECT Customer_ID,
               COUNT(DISTINCT Order_ID)  AS order_count,
               ROUND(SUM(Revenue), 2) AS total_rev
        FROM orders GROUP BY Customer_ID
    )
    SELECT c.Region,
           COUNT(DISTINCT co.Customer_ID) AS customer_count,
           ROUND(AVG(co.order_count), 1)  AS avg_orders_per_customer,
           ROUND(SUM(co.total_rev), 0)    AS total_revenue,
           ROUND(AVG(co.total_rev), 2)    AS avg_lifetime_value
    FROM cust_orders co
    JOIN customers c ON co.Customer_ID = c.Customer_ID
    GROUP BY c.Region
    ORDER BY total_revenue DESC
""")

# ── BLOCK 3: CUSTOMER ORDER COUNT DISTRIBUTION ────────────────────────────────
section("BLOCK 3 — CUSTOMER ORDER COUNT DISTRIBUTION")

df_dist = run("3a. Distribution of Customers by Annual Order Count Band", """
    WITH cust_counts AS (
        SELECT Customer_ID, COUNT(DISTINCT Order_ID) AS order_count
        FROM orders GROUP BY Customer_ID
    )
    SELECT
        CASE
            WHEN order_count < 150 THEN '<150 orders/yr'
            WHEN order_count < 170 THEN '150–169 orders'
            WHEN order_count < 185 THEN '170–184 orders'
            ELSE '185+ orders'
        END AS order_band,
        COUNT(*) AS customer_count,
        ROUND(COUNT(*)*100.0 / SUM(COUNT(*)) OVER(), 1) AS pct_of_customers,
        ROUND(AVG(order_count), 1) AS avg_orders_in_band
    FROM cust_counts
    GROUP BY 1
    ORDER BY MIN(order_count)
""")

run("3b. Order Count Percentile Distribution", """
    WITH cust_counts AS (
        SELECT Customer_ID, COUNT(DISTINCT Order_ID) AS order_count
        FROM orders GROUP BY Customer_ID
    )
    SELECT
        MIN(order_count)  AS min_orders,
        MAX(order_count)  AS max_orders,
        ROUND(AVG(order_count), 1) AS avg_orders,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY order_count) AS p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY order_count) AS median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY order_count) AS p75,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY order_count) AS p90
    FROM cust_counts
""")

# Figure 2: Order count distribution
fig, ax = plt.subplots(figsize=(10, 5))
band_order = ["<150 orders/yr", "150–169 orders", "170–184 orders", "185+ orders"]
df_dist_sorted = df_dist.set_index("order_band").reindex(band_order).dropna(how="all").reset_index()
bar_colors = [DHL_RED, DHL_YELLOW, "#4CAF50", "#1565C0"]
bars = ax.bar(df_dist_sorted["order_band"],
              df_dist_sorted["customer_count"].fillna(0).astype(int),
              color=bar_colors[:len(df_dist_sorted)], edgecolor="white", width=0.6)
for bar, (_, row) in zip(bars, df_dist_sorted.iterrows()):
    if row["customer_count"] > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{int(row['customer_count'])} ({row['pct_of_customers']:.0f}%)",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Number of Customers", fontsize=10)
ax.set_title("Customer Distribution by Annual Order Volume Band\n"
             "DHL B2B customers are high-frequency buyers (134–215 orders/yr)",
             fontsize=12, fontweight="bold")
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, df_dist_sorted["customer_count"].max() * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "02_customer_order_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 02_customer_order_distribution.png")

# ── BLOCK 4: TOP 20 CUSTOMERS BY REVENUE ──────────────────────────────────────
section("BLOCK 4 — TOP 20 CUSTOMERS BY REVENUE")

df_top20 = run("4a. Top 20 Customers — Revenue, Orders, OTIF", """
    SELECT o.Customer_ID,
           c.Customer_Type,
           c.Region,
           COUNT(DISTINCT o.Order_ID)           AS total_orders,
           ROUND(SUM(o.Revenue), 0)             AS total_revenue,
           ROUND(AVG(o.Revenue), 2)             AS avg_order_value,
           ROUND(AVG(o.OTIF_Flag)*100, 2)       AS otif_rate_pct,
           o.Channel                            AS primary_channel
    FROM orders o
    JOIN customers c ON o.Customer_ID = c.Customer_ID
    GROUP BY o.Customer_ID, c.Customer_Type, c.Region, o.Channel
    QUALIFY ROW_NUMBER() OVER (PARTITION BY o.Customer_ID ORDER BY SUM(o.Revenue) DESC) = 1
    ORDER BY total_revenue DESC
    LIMIT 20
""")

# Figure 3: Top 20 customers horizontal bar
fig, ax = plt.subplots(figsize=(12, 8))
type_colors = {"Retailer": DHL_RED, "Distributor": "#FF8C00", "E-Commerce": "#4CAF50",
               "Manufacturer": "#1565C0", "Healthcare": "#7B1FA2", "Government": "#00838F"}
bar_colors_t = [type_colors.get(t, "#888") for t in df_top20["Customer_Type"]]
y_sorted = df_top20.sort_values("total_revenue", ascending=True)
bar_colors_sorted = [type_colors.get(t, "#888") for t in y_sorted["Customer_Type"]]
ax.barh(range(len(y_sorted)), y_sorted["total_revenue"]/1e6,
        color=bar_colors_sorted, edgecolor="white", alpha=0.85)
ax.set_yticks(range(len(y_sorted)))
ax.set_yticklabels([f"{r['Customer_ID']} ({r['Customer_Type'][:4]}, {r['Region'][:3]})"
                    for _, r in y_sorted.iterrows()], fontsize=8)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.1f}M"))
ax.set_xlabel("Total Revenue ($M)", fontsize=10)
ax.set_title("Top 20 Customers by Revenue (24-Month Period)\nColor by Customer Type",
             fontsize=12, fontweight="bold")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "03_top20_customers_revenue.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 03_top20_customers_revenue.png")

# ── BLOCK 5: OTIF RATE BY CUSTOMER TYPE ───────────────────────────────────────
section("BLOCK 5 — OTIF RATE BY CUSTOMER TYPE AND REGION")

df_otif_type = run("5a. OTIF Rate by Customer Type", """
    SELECT c.Customer_Type,
           COUNT(DISTINCT o.Order_ID)           AS total_orders,
           ROUND(AVG(o.On_Time_Flag)*100, 2)    AS on_time_pct,
           ROUND(AVG(o.In_Full_Flag)*100, 2)    AS in_full_pct,
           ROUND(AVG(o.OTIF_Flag)*100, 2)       AS otif_pct
    FROM orders o
    JOIN customers c ON o.Customer_ID = c.Customer_ID
    GROUP BY c.Customer_Type
    ORDER BY otif_pct DESC
""")

df_otif_region = run("5b. OTIF Rate by Region", """
    SELECT c.Region,
           COUNT(DISTINCT o.Order_ID)           AS total_orders,
           ROUND(AVG(o.On_Time_Flag)*100, 2)    AS on_time_pct,
           ROUND(AVG(o.In_Full_Flag)*100, 2)    AS in_full_pct,
           ROUND(AVG(o.OTIF_Flag)*100, 2)       AS otif_pct
    FROM orders o
    JOIN customers c ON o.Customer_ID = c.Customer_ID
    GROUP BY c.Region
    ORDER BY otif_pct DESC
""")

# Figure 4: OTIF by customer type
fig, ax = plt.subplots(figsize=(11, 5))
x = range(len(df_otif_type))
width = 0.25
ax.bar([i - width for i in x], df_otif_type["on_time_pct"], width=width,
       label="On-Time %", color="#1565C0", alpha=0.85)
ax.bar(x, df_otif_type["in_full_pct"], width=width,
       label="In-Full %", color="#4CAF50", alpha=0.85)
ax.bar([i + width for i in x], df_otif_type["otif_pct"], width=width,
       label="OTIF %", color=DHL_RED, alpha=0.85)
ax.axhline(df_otif_type["otif_pct"].mean(), color="#333", linewidth=1.5,
           linestyle="--", label=f"Network OTIF avg {df_otif_type['otif_pct'].mean():.1f}%")
ax.set_xticks(list(x))
ax.set_xticklabels(df_otif_type["Customer_Type"], fontsize=9)
ax.set_ylabel("Rate (%)", fontsize=10)
ax.set_ylim(85, 100)
ax.set_title("OTIF Performance by Customer Type\nOn-Time · In-Full · Combined OTIF",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "04_otif_by_customer_type.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 04_otif_by_customer_type.png")

# ── BLOCK 6: REVENUE BY CHANNEL ───────────────────────────────────────────────
section("BLOCK 6 — REVENUE BY CHANNEL")

df_channel = run("6a. Revenue, Orders and OTIF by Channel", """
    SELECT Channel,
           COUNT(DISTINCT Customer_ID)          AS unique_customers,
           COUNT(DISTINCT Order_ID)             AS total_orders,
           ROUND(SUM(Revenue), 0)               AS total_revenue,
           ROUND(AVG(Revenue), 2)               AS avg_order_value,
           ROUND(SUM(Revenue)*100.0/SUM(SUM(Revenue)) OVER(), 2) AS revenue_pct,
           ROUND(AVG(OTIF_Flag)*100, 2)         AS otif_pct
    FROM orders
    GROUP BY Channel
    ORDER BY total_revenue DESC
""")

# Figure 5: Channel pie + bar
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Revenue & Average Order Value by Channel", fontsize=13, fontweight="bold")
ch_colors = [DHL_RED, DHL_YELLOW, "#4CAF50", "#1565C0"]
axes[0].pie(df_channel["total_revenue"], labels=df_channel["Channel"],
            colors=ch_colors, autopct="%1.1f%%", startangle=140,
            textprops={"fontsize": 10})
axes[0].set_title("Revenue Share by Channel", fontsize=11, fontweight="bold")
axes[1].bar(df_channel["Channel"], df_channel["avg_order_value"],
            color=ch_colors, edgecolor="white")
axes[1].set_ylabel("Avg Order Value ($)", fontsize=10)
axes[1].set_title("Avg Order Value by Channel", fontsize=11, fontweight="bold")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
axes[1].grid(axis="y", linestyle="--", alpha=0.4)
for bar, (_, row) in zip(axes[1].patches, df_channel.iterrows()):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                 f"${row['avg_order_value']:,.0f}",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "05_revenue_by_channel.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 05_revenue_by_channel.png")

# ── BLOCK 7: MONTHLY ACTIVE CUSTOMER TREND ────────────────────────────────────
section("BLOCK 7 — MONTHLY ACTIVE CUSTOMER TREND (24 MONTHS)")

df_monthly_active = run("7a. Monthly Active Customers and Revenue", """
    SELECT strftime(Order_Date, '%Y-%m')         AS year_month,
           COUNT(DISTINCT Customer_ID)            AS active_customers,
           COUNT(DISTINCT Order_ID)              AS total_orders,
           ROUND(SUM(Revenue), 0)                AS total_revenue,
           ROUND(SUM(Revenue)/COUNT(DISTINCT Customer_ID), 2) AS rev_per_customer
    FROM orders
    GROUP BY year_month
    ORDER BY year_month
""")

run("7b. New vs Returning Customers by Month (first order proxy)", """
    WITH first_orders AS (
        SELECT Customer_ID, MIN(Order_Date) AS first_order_date
        FROM orders GROUP BY Customer_ID
    )
    SELECT strftime(o.Order_Date, '%Y-%m') AS year_month,
           COUNT(DISTINCT CASE WHEN strftime(o.Order_Date,'%Y-%m') = strftime(fo.first_order_date,'%Y-%m')
                 THEN o.Customer_ID END) AS new_customers,
           COUNT(DISTINCT CASE WHEN strftime(o.Order_Date,'%Y-%m') != strftime(fo.first_order_date,'%Y-%m')
                 THEN o.Customer_ID END) AS returning_customers
    FROM orders o
    JOIN first_orders fo ON o.Customer_ID = fo.Customer_ID
    GROUP BY year_month
    ORDER BY year_month
""")

# Figure 6: Monthly active customer trend
fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()
months_act = df_monthly_active["year_month"].tolist()
x = range(len(months_act))
ax1.bar(x, df_monthly_active["active_customers"], color=DHL_YELLOW, alpha=0.7,
        label="Active Customers")
ax2.plot(x, df_monthly_active["total_revenue"]/1e6, color=DHL_RED, linewidth=2,
         marker="o", markersize=5, label="Monthly Revenue ($M)")
ax1.set_ylabel("Active Customers", fontsize=10)
ax2.set_ylabel("Revenue ($M)", fontsize=10, color=DHL_RED)
ax2.tick_params(colors=DHL_RED)
ax1.set_xticks(list(x))
ax1.set_xticklabels(months_act, rotation=45, ha="right", fontsize=7)
ax1.set_title("Monthly Active Customers & Revenue — 24-Month Trend",
              fontsize=12, fontweight="bold")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
ax1.grid(axis="y", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "06_monthly_active_customers.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\n  → Saved 06_monthly_active_customers.png")

print(f"\n{'='*70}")
print("  SQL EXPLORATION COMPLETE — 7 blocks, 6 figures saved")
print(f"  Figures: {FIGURES}")
print("  Next step: rfm_analysis.py — RFM scoring and segmentation")
print(f"{'='*70}\n")
