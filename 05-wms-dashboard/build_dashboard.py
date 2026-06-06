"""
build_dashboard.py — WMS Operational Dashboard (5 sections)
Project 5: WMS Operational Dashboard — DHL BA/DA Portfolio
"""

import os, warnings
import pandas as pd
import numpy as np
import duckdb
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

DATA    = '/sessions/serene-wonderful-carson/mnt/DHL/shared/data/dhl-synthetic/'
PROJECT = '/sessions/serene-wonderful-carson/mnt/DHL/dhl-business-analyst/05-wms-dashboard/'
OUTS    = os.path.join(PROJECT, "outputs")
DASH    = os.path.join(PROJECT, "dashboard")
os.makedirs(DASH, exist_ok=True)

DHL_RED   = "#D40511"
DHL_YELLOW= "#FFCC00"
DHL_DARK  = "#1A1A1A"
GREEN     = "#2E7D32"
AMBER     = "#F57C00"

# ─── load data ────────────────────────────────────────────────────────────────
con = duckdb.connect()
con.execute(f"CREATE VIEW wms  AS SELECT * FROM read_csv_auto('{DATA}wms_tasks.csv')")
con.execute(f"CREATE VIEW inv  AS SELECT * FROM read_csv_auto('{DATA}inventory_snapshot.csv')")
con.execute(f"CREATE VIEW dem  AS SELECT * FROM read_csv_auto('{DATA}daily_demand.csv')")
con.execute(f"CREATE VIEW sku  AS SELECT * FROM read_csv_auto('{DATA}sku_master.csv')")

kpi     = pd.read_csv(os.path.join(OUTS, "kpi_summary.csv"))
kpi_ws  = pd.read_csv(os.path.join(OUTS, "kpi_by_warehouse_shift.csv"))
ops     = pd.read_csv(os.path.join(OUTS, "operator_scorecard.csv"))
dq      = pd.read_csv(os.path.join(OUTS, "data_quality_flags.csv"))

# ─── monthly trend ────────────────────────────────────────────────────────────
monthly = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS month, Warehouse_ID,
           COUNT(*) AS total_tasks,
           SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_acc,
           SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_acc,
           SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_acc,
           SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_acc,
           SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate
    FROM wms GROUP BY month, Warehouse_ID ORDER BY month, Warehouse_ID
""").df()

monthly_net = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS month,
           COUNT(*) AS total_tasks,
           SUM(CASE WHEN Task_Type='Pick' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_acc,
           SUM(CASE WHEN Task_Type='Putaway' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Putaway' THEN 1 ELSE 0 END),0) AS putaway_acc,
           SUM(CASE WHEN Task_Type='Cycle Count' AND Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN Task_Type='Cycle Count' THEN 1 ELSE 0 END),0) AS cc_acc,
           SUM(CASE WHEN Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) AS overall_acc,
           SUM(CASE WHEN Error_Code IS NOT NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) AS error_rate
    FROM wms GROUP BY month ORDER BY month
""").df()

# daily task volume
daily = con.execute("""
    SELECT Task_Date, Warehouse_ID, Task_Type, COUNT(*) AS cnt
    FROM wms GROUP BY Task_Date, Warehouse_ID, Task_Type ORDER BY Task_Date
""").df()
daily["Task_Date"] = pd.to_datetime(daily["Task_Date"])

# daily net
daily_net = daily.groupby("Task_Date")["cnt"].sum().reset_index()
daily_net["ma7"] = daily_net["cnt"].rolling(7, min_periods=1).mean()

# error distribution
err_dist = con.execute("""
    SELECT Error_Code, COUNT(*) AS cnt
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY Error_Code ORDER BY cnt DESC
""").df()

err_monthly = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS month, Error_Code, COUNT(*) AS cnt
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY month, Error_Code ORDER BY month
""").df()

top20_sku = con.execute("""
    SELECT w.SKU_ID, COUNT(*) AS errors,
           s.Category, s.ABC_Class
    FROM wms w LEFT JOIN sku s ON w.SKU_ID=s.SKU_ID
    WHERE w.Error_Code IS NOT NULL
    GROUP BY w.SKU_ID, s.Category, s.ABC_Class
    ORDER BY errors DESC LIMIT 20
""").df()

# shift heatmap data
shift_heat = kpi_ws.pivot_table(
    index="Warehouse_ID", columns="Shift", values="pick_accuracy_pct"
).reset_index()

# inventory
inv_monthly = con.execute("""
    SELECT strftime(Snapshot_Date,'%Y-%m') AS month, Warehouse_ID,
           AVG((On_Hand_Qty-Available_Qty)*1.0/NULLIF(On_Hand_Qty,0)*100) AS gap_pct,
           AVG(Available_Qty*1.0/NULLIF(On_Hand_Qty,0)*100) AS ira_pct
    FROM inv GROUP BY month, Warehouse_ID ORDER BY month
""").df()

inv_cat = con.execute("""
    SELECT Category, Warehouse_ID,
           AVG(On_Hand_Qty) AS avg_onhand, AVG(Available_Qty) AS avg_avail,
           AVG((On_Hand_Qty-Available_Qty)*1.0/NULLIF(On_Hand_Qty,0)*100) AS gap_pct
    FROM inv GROUP BY Category, Warehouse_ID ORDER BY gap_pct DESC
""").df()

inv_net_monthly = inv_monthly.groupby("month")["ira_pct"].mean().reset_index()

# picks per hour monthly
pph_monthly = con.execute("""
    SELECT strftime(Task_Date,'%Y-%m') AS month, Warehouse_ID,
           SUM(CASE WHEN Task_Type='Pick' THEN 1 ELSE 0 END)*1.0/
               NULLIF(SUM(CASE WHEN Task_Type='Pick' THEN Duration_Min ELSE 0 END)/60.0,0) AS pph
    FROM wms GROUP BY month, Warehouse_ID ORDER BY month
""").df()

# error by category (used as proxy for zone/area)
err_zone = con.execute("""
    SELECT Category AS Zone, Warehouse_ID, COUNT(*) AS errors,
           COUNT(*)*100.0/SUM(COUNT(*)) OVER(PARTITION BY Warehouse_ID) AS pct
    FROM wms WHERE Error_Code IS NOT NULL
    GROUP BY Category, Warehouse_ID ORDER BY errors DESC
""").df()

warehouses = ["DHL-WH-IL02","DHL-WH-NJ01","DHL-WH-TX03"]
wh_labels  = {"DHL-WH-IL02":"WH-IL02","DHL-WH-NJ01":"WH-NJ01","DHL-WH-TX03":"WH-TX03"}
colors_wh  = {"DHL-WH-IL02": DHL_RED, "DHL-WH-NJ01": "#1565C0", "DHL-WH-TX03": "#2E7D32"}

def status_color(val, green_thresh, amber_thresh):
    if val >= green_thresh: return GREEN
    if val >= amber_thresh: return AMBER
    return DHL_RED

def make_indicator(val, title, green_thresh, amber_thresh, suffix="%"):
    color = status_color(val, green_thresh, amber_thresh)
    return go.Indicator(
        mode="number+delta",
        value=round(val,2),
        number={"suffix": suffix, "font":{"size":28,"color":color}},
        title={"text": title, "font":{"size":11,"color":"#555"}},
    )

# ══════════════════════════════════════════════════════════════════════════════
# BUILD HTML
# ══════════════════════════════════════════════════════════════════════════════
sections_html = []

# ─── SECTION 1 — Network Overview ────────────────────────────────────────────
net = kpi[kpi["Level"]=="Network"].iloc[0]
wh_kpi = kpi[kpi["Level"]=="Warehouse"]

# KPI scorecards
fig_kpi = make_subplots(
    rows=1, cols=4,
    specs=[[{"type":"indicator"}]*4],
    subplot_titles=["Pick Accuracy","Putaway Compliance","Cycle Count Accuracy","Overall Task Accuracy"]
)
metrics = [
    ("pick_accuracy_pct",    "Pick Accuracy",     99.0, 98.5),
    ("putaway_compliance_pct","Putaway Compliance",99.5, 99.0),
    ("cc_accuracy_pct",      "CC Accuracy",       98.5, 98.0),
    ("overall_accuracy_pct", "Overall Accuracy",  99.0, 98.5),
]
for col,(col_name,title,g,a) in enumerate(metrics,1):
    val = net[col_name]
    color = status_color(val, g, a)
    badge = "🟢" if color==GREEN else ("🟡" if color==AMBER else "🔴")
    fig_kpi.add_trace(go.Indicator(
        mode="number",
        value=round(val,2),
        number={"suffix":"%","font":{"size":36,"color":color},"valueformat":".2f"},
        title={"text":f"{badge} {title}<br><span style='font-size:10px;color:#888'>Network-Wide</span>"},
    ), row=1, col=col)

fig_kpi.update_layout(
    height=180, margin=dict(t=40,b=10,l=20,r=20),
    paper_bgcolor="white", font=dict(family="Arial")
)

# 24-month trend
fig_trend = go.Figure()
kpi_cols = [("pick_acc","Pick Accuracy",99.0),("putaway_acc","Putaway Compliance",99.5),("overall_acc","Overall Accuracy",99.0)]
line_colors = [DHL_RED, "#1565C0", GREEN]
for (col,label,thresh), lc in zip(kpi_cols, line_colors):
    fig_trend.add_trace(go.Scatter(
        x=monthly_net["month"], y=monthly_net[col].round(3),
        name=label, line=dict(color=lc, width=2), mode="lines"
    ))
    fig_trend.add_hline(y=thresh, line_dash="dot", line_color=lc, line_width=1, opacity=0.4)

fig_trend.update_layout(
    title=dict(text="24-Month KPI Trend — Network", font=dict(size=13)),
    height=300, yaxis=dict(title="Accuracy %", range=[98.5,100.5]),
    xaxis=dict(title="Month"), legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# warehouse comparison
fig_wh_bar = make_subplots(rows=1, cols=4, subplot_titles=[
    "Pick Accuracy","Putaway Compliance","CC Accuracy","Overall Accuracy"])
bar_metrics = ["pick_accuracy_pct","putaway_compliance_pct","cc_accuracy_pct","overall_accuracy_pct"]
thresholds  = [99.0, 99.5, 98.5, 99.0]
for col_i,(m,thresh) in enumerate(zip(bar_metrics,thresholds),1):
    bar_colors = [status_color(v,thresh,thresh-0.5) for v in wh_kpi[m]]
    fig_wh_bar.add_trace(go.Bar(
        x=[wh_labels[w] for w in wh_kpi["Warehouse_ID"]],
        y=wh_kpi[m].round(3),
        marker_color=bar_colors, showlegend=False,
        text=wh_kpi[m].round(2).astype(str)+"%",
        textposition="outside", textfont=dict(size=10)
    ), row=1, col=col_i)
    fig_wh_bar.add_hline(y=thresh, line_dash="dot", line_color="#999", line_width=1, row=1, col=col_i)

fig_wh_bar.update_layout(
    height=300, title=dict(text="Warehouse KPI Comparison", font=dict(size=13)),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=50,b=40,l=50,r=20)
)
for i in range(1,5):
    fig_wh_bar.update_yaxes(range=[98.0,100.3], row=1, col=i)

s1 = f"""
<div class="section" id="s1">
  <div class="section-header"><span class="section-num">01</span> Network Overview</div>
  <div class="kpi-row">
    {''.join([f'<div class="kpi-card {("green" if status_color(net[m],g,a)==GREEN else "amber" if status_color(net[m],g,a)==AMBER else "red")}"><div class="kpi-value">{net[m]:.2f}%</div><div class="kpi-label">{t}</div><div class="kpi-sub">{"✓ Above SLA" if status_color(net[m],g,a)==GREEN else ("⚠ Near threshold" if status_color(net[m],g,a)==AMBER else "✗ Below SLA")}</div></div>' for m,t,g,a in metrics])}
  </div>
  <div class="chart-row">
    <div class="chart-half">{fig_trend.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_wh_bar.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
</div>
"""

# ─── SECTION 2 — Floor Operations ────────────────────────────────────────────
# daily volume with MA7
fig_daily = go.Figure()
fig_daily.add_trace(go.Scatter(
    x=daily_net["Task_Date"], y=daily_net["cnt"],
    name="Daily Tasks", line=dict(color="#BBBBBB", width=1),
    mode="lines", fill="tozeroy", fillcolor="rgba(212,5,17,0.07)"
))
fig_daily.add_trace(go.Scatter(
    x=daily_net["Task_Date"], y=daily_net["ma7"].round(0),
    name="7-Day MA", line=dict(color=DHL_RED, width=2.5), mode="lines"
))
fig_daily.update_layout(
    title="Daily Task Volume — Network (with 7-Day Moving Average)",
    height=280, xaxis_title="Date", yaxis_title="Tasks",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# task type breakdown by warehouse
task_type_wh = con.execute("""
    SELECT Warehouse_ID, Task_Type, COUNT(*) AS cnt
    FROM wms GROUP BY Warehouse_ID, Task_Type ORDER BY Warehouse_ID, Task_Type
""").df()
fig_task_type = go.Figure()
tt_colors = {"Pick": DHL_RED, "Putaway": "#1565C0", "Cycle Count": GREEN}
for tt in ["Pick","Putaway","Cycle Count"]:
    sub = task_type_wh[task_type_wh["Task_Type"]==tt]
    fig_task_type.add_trace(go.Bar(
        x=[wh_labels[w] for w in sub["Warehouse_ID"]],
        y=sub["cnt"], name=tt,
        marker_color=tt_colors[tt]
    ))
fig_task_type.update_layout(
    title="Task Type Breakdown by Warehouse", barmode="group",
    height=280, xaxis_title="Warehouse", yaxis_title="Total Tasks",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# shift performance heatmap
shift_order = ["Morning 06:00-14:00","Afternoon 14:00-22:00","Night 22:00-06:00"]
heat_z = []
for shift in shift_order:
    row = []
    for wh in warehouses:
        val = kpi_ws[(kpi_ws["Warehouse_ID"]==wh)&(kpi_ws["Shift"]==shift)]["pick_accuracy_pct"]
        row.append(round(float(val.iloc[0]),3) if len(val)>0 else None)
    heat_z.append(row)

fig_heat = go.Figure(go.Heatmap(
    z=heat_z, x=[wh_labels[w] for w in warehouses], y=shift_order,
    colorscale=[[0,"#D40511"],[0.5,"#FFCC00"],[1,"#2E7D32"]],
    zmin=98.8, zmax=99.6, text=[[f"{v:.3f}%" for v in row] for row in heat_z],
    texttemplate="%{text}", textfont={"size":11},
    colorbar=dict(title="Pick Acc %")
))
fig_heat.update_layout(
    title="Shift Performance Heatmap — Pick Accuracy %",
    height=260, paper_bgcolor="white",
    margin=dict(t=40,b=40,l=150,r=20)
)

# picks per hour trend
fig_pph = go.Figure()
for wh in warehouses:
    sub = pph_monthly[pph_monthly["Warehouse_ID"]==wh]
    fig_pph.add_trace(go.Scatter(
        x=sub["month"], y=sub["pph"].round(2),
        name=wh_labels[wh], line=dict(color=colors_wh[wh], width=2), mode="lines"
    ))
fig_pph.update_layout(
    title="Picks per Labour Hour — Monthly Trend",
    height=280, xaxis_title="Month", yaxis_title="Picks/hr",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# top 5 / bottom 5 operators table
top5 = ops.nlargest(5,"overall_accuracy_pct")[["accuracy_rank","Operator_ID","Warehouse_ID","overall_accuracy_pct","performance_flag"]]
bot5 = ops.nsmallest(5,"overall_accuracy_pct")[["accuracy_rank","Operator_ID","Warehouse_ID","overall_accuracy_pct","performance_flag"]]

def op_table_html(df, title, header_class):
    rows = ""
    for _,r in df.iterrows():
        flag_badge = '<span class="badge-hp">⭐ HIGH PERF</span>' if r["performance_flag"]=="HIGH_PERFORMER" else '<span class="badge-nc">⚠ COACHING</span>' if r["performance_flag"]=="NEEDS_COACHING" else '<span class="badge-std">STANDARD</span>'
        rows += f"<tr><td>#{r['accuracy_rank']}</td><td>{r['Operator_ID']}</td><td>{wh_labels.get(r['Warehouse_ID'],r['Warehouse_ID'])}</td><td>{r['overall_accuracy_pct']:.3f}%</td><td>{flag_badge}</td></tr>"
    return f"""<div class="op-table-wrap"><div class="op-table-title {header_class}">{title}</div>
<table class="dhl-table"><thead><tr><th>Rank</th><th>Operator</th><th>Warehouse</th><th>Accuracy</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>"""

s2 = f"""
<div class="section" id="s2">
  <div class="section-header"><span class="section-num">02</span> Floor Operations</div>
  <div class="chart-row">
    <div class="chart-half">{fig_daily.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_task_type.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
  <div class="chart-row">
    <div class="chart-half">{fig_heat.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_pph.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
  <div class="chart-row">
    <div class="chart-half">{op_table_html(top5,"🏆 Top 5 Operators — All-Time Accuracy","header-green")}</div>
    <div class="chart-half">{op_table_html(bot5,"📉 Bottom 5 Operators — All-Time Accuracy","header-red")}</div>
  </div>
</div>
"""

# ─── SECTION 3 — Error Analysis ──────────────────────────────────────────────
# pie chart
fig_pie = go.Figure(go.Pie(
    labels=err_dist["Error_Code"], values=err_dist["cnt"],
    marker=dict(colors=[DHL_RED,"#1565C0",GREEN,AMBER,"#6A1B9A"]),
    hole=0.4, textinfo="label+percent", textfont=dict(size=11)
))
fig_pie.update_layout(
    title="Error Code Distribution — Network-Wide",
    height=300, paper_bgcolor="white",
    margin=dict(t=40,b=20,l=20,r=20),
    legend=dict(orientation="v", x=1.0)
)

# error trend by code
fig_err_trend = go.Figure()
err_colors_map = {"WRONG_SKU":DHL_RED,"WRONG_QTY":"#1565C0","WRONG_LOCATION":GREEN,
                  "MISSING_LABEL":AMBER,"DAMAGED":"#6A1B9A"}
for code in err_monthly["Error_Code"].unique():
    sub = err_monthly[err_monthly["Error_Code"]==code]
    fig_err_trend.add_trace(go.Scatter(
        x=sub["month"], y=sub["cnt"],
        name=code, line=dict(color=err_colors_map.get(code,"#999"), width=2), mode="lines"
    ))
fig_err_trend.update_layout(
    title="Error Trend by Code — 24 Months",
    height=300, xaxis_title="Month", yaxis_title="Error Count",
    legend=dict(orientation="h",y=-0.3),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=70,l=60,r=20)
)

# top 20 SKU error bar
fig_sku_err = go.Figure(go.Bar(
    x=top20_sku["errors"], y=top20_sku["SKU_ID"] + " (" + top20_sku["Category"].fillna("?") + ")",
    orientation="h",
    marker_color=[DHL_RED if c=="ABC-A" else (AMBER if c=="ABC-B" else "#1565C0") for c in top20_sku["ABC_Class"].fillna("ABC-C")],
    text=top20_sku["errors"], textposition="outside"
))
fig_sku_err.update_layout(
    title="Top 20 SKUs by Error Frequency",
    height=460, xaxis_title="Total Errors", yaxis_title="",
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=40,l=250,r=60)
)
fig_sku_err.update_yaxes(autorange="reversed")

# error by zone and warehouse
fig_zone_err = go.Figure()
for wh in warehouses:
    sub = err_zone[err_zone["Warehouse_ID"]==wh].sort_values("errors",ascending=False)
    fig_zone_err.add_trace(go.Bar(
        x=sub["Zone"], y=sub["errors"],
        name=wh_labels[wh], marker_color=colors_wh[wh]
    ))
fig_zone_err.update_layout(
    title="Error Count by Zone and Warehouse", barmode="group",
    height=300, xaxis_title="Zone", yaxis_title="Errors",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# monthly error rate vs network avg
net_avg_err = monthly_net["error_rate"].mean()
fig_err_rate = go.Figure()
for wh in warehouses:
    sub = monthly[monthly["Warehouse_ID"]==wh]
    fig_err_rate.add_trace(go.Scatter(
        x=sub["month"], y=sub["error_rate"].round(4),
        name=wh_labels[wh], line=dict(color=colors_wh[wh], width=2), mode="lines"
    ))
fig_err_rate.add_hline(y=net_avg_err, line_dash="dot", line_color="#999",
                       annotation_text=f"Network avg {net_avg_err:.2f}%",
                       annotation_position="top right")
fig_err_rate.update_layout(
    title="Monthly Error Rate by Warehouse vs Network Average",
    height=300, xaxis_title="Month", yaxis_title="Error Rate %",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

s3 = f"""
<div class="section" id="s3">
  <div class="section-header"><span class="section-num">03</span> Error Analysis</div>
  <div class="chart-row">
    <div class="chart-half">{fig_pie.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_err_trend.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
  <div class="chart-full">{fig_sku_err.to_html(full_html=False, include_plotlyjs=False)}</div>
  <div class="chart-row">
    <div class="chart-half">{fig_zone_err.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_err_rate.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
</div>
"""

# ─── SECTION 4 — Inventory Health ────────────────────────────────────────────
# IRA trend
fig_ira = go.Figure()
for wh in warehouses:
    sub = inv_monthly[inv_monthly["Warehouse_ID"]==wh]
    fig_ira.add_trace(go.Scatter(
        x=sub["month"], y=sub["ira_pct"].round(2),
        name=wh_labels[wh], line=dict(color=colors_wh[wh], width=2), mode="lines"
    ))
fig_ira.add_hline(y=80.0, line_dash="dot", line_color=DHL_RED, opacity=0.5,
                  annotation_text="80% threshold", annotation_position="top right")
fig_ira.update_layout(
    title="Inventory Record Accuracy (Available/On-Hand) — Monthly Trend",
    height=300, xaxis_title="Month", yaxis_title="IRA %",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# on-hand vs available by category
inv_cat_net = inv_cat.groupby("Category")[["avg_onhand","avg_avail","gap_pct"]].mean().reset_index().sort_values("gap_pct",ascending=False)
fig_inv_cat = go.Figure()
fig_inv_cat.add_trace(go.Bar(x=inv_cat_net["Category"], y=inv_cat_net["avg_onhand"].round(0),
                              name="Avg On-Hand", marker_color="#BBBBBB"))
fig_inv_cat.add_trace(go.Bar(x=inv_cat_net["Category"], y=inv_cat_net["avg_avail"].round(0),
                              name="Avg Available", marker_color=DHL_RED))
fig_inv_cat.update_layout(
    title="On-Hand vs Available Quantity by Category (Network Average)",
    barmode="overlay", height=300,
    xaxis_title="Category", yaxis_title="Avg Units",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=80,l=60,r=20), xaxis_tickangle=-20
)

# stockout vs pick accuracy scatter
corr_data = con.execute("""
    SELECT strftime(d.Date,'%Y-%m') AS month, d.Warehouse_ID,
           AVG(d.Stockout_Flag)*100 AS stockout_rate,
           SUM(CASE WHEN w.Task_Type='Pick' AND w.Accuracy_Flag=1 THEN 1 ELSE 0 END)*100.0/
               NULLIF(SUM(CASE WHEN w.Task_Type='Pick' THEN 1 ELSE 0 END),0) AS pick_acc
    FROM dem d
    JOIN wms w ON d.Warehouse_ID=w.Warehouse_ID AND strftime(d.Date,'%Y-%m')=strftime(w.Task_Date,'%Y-%m')
    GROUP BY month, d.Warehouse_ID
""").df()

fig_scatter = go.Figure()
for wh in warehouses:
    sub = corr_data[corr_data["Warehouse_ID"]==wh]
    fig_scatter.add_trace(go.Scatter(
        x=sub["pick_acc"], y=sub["stockout_rate"],
        name=wh_labels[wh], mode="markers",
        marker=dict(color=colors_wh[wh], size=8, opacity=0.7)
    ))
fig_scatter.update_layout(
    title="Pick Accuracy vs Stockout Rate — Monthly Correlation",
    height=300, xaxis_title="Pick Accuracy %", yaxis_title="Stockout Rate %",
    legend=dict(orientation="h",y=-0.25),
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=60,l=60,r=20)
)

# inventory value at risk
inv_risk = con.execute("""
    SELECT i.Category, i.Warehouse_ID,
           COUNT(DISTINCT i.SKU_ID) AS skus,
           SUM(i.On_Hand_Qty * s.Unit_Cost) AS inventory_value,
           AVG((i.On_Hand_Qty-i.Available_Qty)*1.0/NULLIF(i.On_Hand_Qty,0)*100) AS gap_pct
    FROM inv i JOIN sku s ON i.SKU_ID=s.SKU_ID
    GROUP BY i.Category, i.Warehouse_ID
    HAVING gap_pct > 20
    ORDER BY inventory_value DESC LIMIT 10
""").df()

fig_risk = go.Figure(go.Bar(
    x=inv_risk["Category"] + " / " + inv_risk["Warehouse_ID"].str.replace("DHL-WH-",""),
    y=(inv_risk["inventory_value"]/1000).round(1),
    marker_color=[DHL_RED if g>22 else AMBER for g in inv_risk["gap_pct"]],
    text=["$"+str(round(v/1000,1))+"k" for v in inv_risk["inventory_value"]],
    textposition="outside"
))
fig_risk.update_layout(
    title="Inventory at Risk — SKUs with >20% On-Hand/Available Gap (Top 10)",
    height=300, xaxis_title="Category / Warehouse", yaxis_title="Inventory Value ($k)",
    paper_bgcolor="white", plot_bgcolor="#F8F8F8",
    margin=dict(t=40,b=100,l=60,r=20), xaxis_tickangle=-30
)

s4 = f"""
<div class="section" id="s4">
  <div class="section-header"><span class="section-num">04</span> Inventory Health</div>
  <div class="chart-row">
    <div class="chart-half">{fig_ira.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_inv_cat.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
  <div class="chart-row">
    <div class="chart-half">{fig_scatter.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-half">{fig_risk.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
</div>
"""

# ─── SECTION 5 — Data Quality Alerts ─────────────────────────────────────────
coaching_ops = ops[ops["performance_flag"]=="NEEDS_COACHING"]
high_err_skus = dq[dq["flag_type"]=="HIGH_ERROR_SKU"].head(15)
prob_zones = dq[dq["flag_type"]=="HIGH_ERROR_ZONE"]
shift_spikes = dq[dq["flag_type"]=="SHIFT_ERROR_SPIKE"].head(10)

total_flags = len(dq)
high_flags  = len(dq[dq["severity"]=="HIGH"])
med_flags   = len(dq[dq["severity"]=="MEDIUM"])

def dq_table(df, cols, col_headers):
    if len(df)==0:
        return '<p style="color:#888;padding:12px">No active flags in this category.</p>'
    header = "<tr>" + "".join(f"<th>{h}</th>" for h in col_headers) + "</tr>"
    rows = ""
    for _,r in df.iterrows():
        sev = r.get("severity","")
        badge = f'<span class="badge-hp">HIGH</span>' if sev=="HIGH" else (f'<span class="badge-nc">MEDIUM</span>' if sev=="MEDIUM" else "")
        row_vals = []
        for c in cols:
            val = r.get(c,"")
            if c=="severity": val = badge
            elif c=="metric_value": val = f"{val:.2f}%" if isinstance(val,(int,float)) else val
            row_vals.append(f"<td>{val}</td>")
        rows += "<tr>" + "".join(row_vals) + "</tr>"
    return f'<table class="dhl-table"><thead>{header}</thead><tbody>{rows}</tbody></table>'

s5 = f"""
<div class="section" id="s5">
  <div class="section-header"><span class="section-num">05</span> Data Quality Alerts</div>
  <div class="alert-summary">
    <div class="alert-badge red-badge">🔴 {high_flags} HIGH severity flags</div>
    <div class="alert-badge amber-badge">🟡 {med_flags} MEDIUM severity flags</div>
    <div class="alert-badge grey-badge">📋 {total_flags} Total active flags</div>
  </div>

  <div class="dq-block">
    <div class="dq-block-title">👤 Operators Needing Coaching (Accuracy &lt; 98.5%)</div>
    {dq_table(coaching_ops, ["accuracy_rank","Operator_ID","Warehouse_ID","overall_accuracy_pct","total_errors","trend_direction"],
              ["Rank","Operator","Warehouse","Accuracy %","Total Errors","Trend"])}
    {"<p style='color:#2E7D32;padding:8px 12px'>✅ No operators below coaching threshold — all 180 operators meet the 98.5% minimum.</p>" if len(coaching_ops)==0 else ""}
  </div>

  <div class="dq-block">
    <div class="dq-block-title">📦 High-Error SKUs (≥3 months above 2% error rate)</div>
    {dq_table(high_err_skus, ["entity_id","detail","severity","metric_value"],
              ["SKU ID","Detail","Severity","Avg Error Rate %"])}
  </div>

  <div class="dq-block">
    <div class="dq-block-title">🗂 Problem Zones (Above-Average Error Rate)</div>
    {dq_table(prob_zones, ["entity_id","warehouse_id","detail","severity","metric_value"],
              ["Zone","Warehouse","Detail","Severity","Error Rate %"])}
  </div>

  <div class="dq-block">
    <div class="dq-block-title">⏱ Shift Error Spikes (Operator-Shift Combinations)</div>
    {dq_table(shift_spikes, ["entity_id","warehouse_id","shift","detail","metric_value"],
              ["Operator","Warehouse","Shift","Detail","Error Rate %"])}
  </div>
</div>
"""

# ─── NAV + CSS + FINAL ASSEMBLY ───────────────────────────────────────────────
nav = """
<nav class="top-nav">
  <div class="nav-brand">
    <span class="nav-logo">DHL</span>
    <span class="nav-title">WMS Operational Dashboard</span>
    <span class="nav-sub">BA/DA Portfolio · Project 5 · Vinyl Kiran Anipe · 2024</span>
  </div>
  <div class="nav-links">
    <a href="#s1">Network Overview</a>
    <a href="#s2">Floor Operations</a>
    <a href="#s3">Error Analysis</a>
    <a href="#s4">Inventory Health</a>
    <a href="#s5">Data Quality</a>
  </div>
</nav>
"""

css = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, Helvetica, sans-serif; background: #F0F0F0; color: #1A1A1A; }
.top-nav { background: #D40511; color: white; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 56px; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }
.nav-brand { display: flex; align-items: baseline; gap: 12px; }
.nav-logo { background: #FFCC00; color: #D40511; font-weight: 900; font-size: 16px; padding: 2px 8px; border-radius: 3px; }
.nav-title { font-size: 15px; font-weight: 700; }
.nav-sub { font-size: 11px; opacity: 0.8; }
.nav-links { display: flex; gap: 20px; }
.nav-links a { color: white; text-decoration: none; font-size: 12px; opacity: 0.85; transition: opacity 0.2s; }
.nav-links a:hover { opacity: 1; text-decoration: underline; }
.section { background: white; margin: 16px 20px; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.section-header { font-size: 15px; font-weight: 700; color: #1A1A1A; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #D40511; display: flex; align-items: center; gap: 10px; }
.section-num { background: #D40511; color: white; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; }
.kpi-row { display: flex; gap: 14px; margin-bottom: 18px; }
.kpi-card { flex: 1; border-radius: 8px; padding: 16px; text-align: center; border-left: 4px solid; }
.kpi-card.green { background: #E8F5E9; border-color: #2E7D32; }
.kpi-card.amber { background: #FFF3E0; border-color: #F57C00; }
.kpi-card.red   { background: #FFEBEE; border-color: #D40511; }
.kpi-value { font-size: 26px; font-weight: 700; }
.kpi-card.green .kpi-value { color: #2E7D32; }
.kpi-card.amber .kpi-value { color: #F57C00; }
.kpi-card.red   .kpi-value { color: #D40511; }
.kpi-label { font-size: 11px; color: #555; margin-top: 4px; font-weight: 600; }
.kpi-sub { font-size: 10px; color: #888; margin-top: 2px; }
.chart-row { display: flex; gap: 14px; margin-bottom: 14px; }
.chart-half { flex: 1; min-width: 0; }
.chart-full { margin-bottom: 14px; }
.alert-summary { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.alert-badge { padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.red-badge   { background: #FFEBEE; color: #D40511; }
.amber-badge { background: #FFF3E0; color: #F57C00; }
.grey-badge  { background: #F5F5F5; color: #555; }
.dq-block { margin-bottom: 22px; }
.dq-block-title { font-size: 13px; font-weight: 700; color: #1A1A1A; margin-bottom: 8px; padding: 6px 10px; background: #F8F8F8; border-left: 3px solid #D40511; }
.dhl-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.dhl-table thead { background: #1A1A1A; color: white; }
.dhl-table th { padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; }
.dhl-table td { padding: 7px 10px; border-bottom: 1px solid #EEE; }
.dhl-table tbody tr:hover { background: #F8F8F8; }
.badge-hp  { background: #1565C0; color: white; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; }
.badge-nc  { background: #D40511; color: white; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; }
.badge-std { background: #E0E0E0; color: #555; padding: 2px 7px; border-radius: 3px; font-size: 10px; }
.op-table-wrap { background: #FAFAFA; border-radius: 6px; padding: 12px; }
.op-table-title { font-size: 12px; font-weight: 700; margin-bottom: 10px; padding: 4px 8px; border-radius: 4px; }
.header-green { background: #E8F5E9; color: #2E7D32; }
.header-red   { background: #FFEBEE; color: #D40511; }
</style>
"""

import plotly.io as pio
plotly_js = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WMS Operational Dashboard — DHL BA/DA Portfolio</title>
{plotly_js}
{css}
</head>
<body>
{nav}
{s1}
{s2}
{s3}
{s4}
{s5}
<div style="text-align:center;padding:24px;font-size:11px;color:#AAA;">
  WMS Operational Dashboard · DHL BA/DA Portfolio · Project 5 · Vinyl Kiran Anipe · 2024 · 219,000 tasks · 3 warehouses · 180 operators
</div>
</body>
</html>"""

out_path = os.path.join(DASH, "wms_dashboard.html")
with open(out_path,"w") as f:
    f.write(html)

print(f"Dashboard written: {out_path}")
print(f"File size: {os.path.getsize(out_path)/1024/1024:.1f} MB")
