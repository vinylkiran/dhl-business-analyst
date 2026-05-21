# Demand Forecasting — Inventory Planner Guide
**For:** Inventory Planners — DHL-WH-NJ01, IL02, TX03  
**Prepared by:** Vinyl Kiran Anipe (Business Analyst)  
**Date:** June 2024  
**Version:** 1.0 — Pre-automation (manual process guide)

---

## What This Guide Covers

This one-page guide helps you use the demand forecasting outputs in your daily planning.
It explains what the numbers mean, how to use the reorder signals, and when to override
the system recommendation.

---

## Your Daily Checklist

**Each morning (takes ~20 minutes, not 2–3 hours):**

- [ ] Open the forecast dashboard (link: TBC — IT will share)
- [ ] Filter to **your warehouse**
- [ ] Review any SKUs flagged with **Reorder Signal = YES** (red highlight)
- [ ] Check the **MAPE alert** column — if a SKU shows ⚠️, the forecast may be less reliable
- [ ] Place orders for flagged SKUs using the `MA14_Forecast` as your demand estimate
- [ ] Record any manual overrides in the override log (shared Excel — link TBC)

---

## Understanding the Forecast Numbers

| Column | Plain English | What to do with it |
|---|---|---|
| **MA14_Forecast** | Average daily demand over the past 14 days | Use as your base demand estimate |
| **Seasonal_MA14** | MA14 adjusted for the current month's demand pattern | Use this in peak months (see table below) |
| **Reorder Signal** | YES/NO — should you order today? | YES = place an order this morning |
| **Safety_Stock_Qty** | Minimum units to keep on hand | Never let on-hand qty drop below this |
| **MAPE_14d** | How accurate the forecast has been (lower is better) | If > 35%, treat the forecast as a guide only |
| **accuracy_alert** | ⚠️ = this SKU's forecast is less reliable than usual | Apply your judgement — check recent demand manually |

---

## Seasonal Adjustment — When to Use It

Some months are naturally busier than others. The **Seasonal MA14** column already adjusts
for this — but here's a plain-English version of the pattern:

| Month | Demand Level | Tip |
|---|---|---|
| Jan – Feb | Below average | Standard MA14 is fine |
| Mar – Apr | Average | Standard MA14 is fine |
| May – Jun | Slightly above average | Use Seasonal MA14 |
| Jul – Aug | Variable | Watch A-class SKUs closely |
| Sep – Oct | Above average | Use Seasonal MA14 for all A-class |
| Nov – Dec | Highest (peak season) | **Always use Seasonal MA14** |

*Exact indices are updated quarterly by the BA team and reflected automatically in the dashboard.*

---

## ABC Class — What It Means for You

| Class | Description | Your priority |
|---|---|---|
| **A (red)** | Top 10% of SKUs — 80% of network revenue | Check these first, every day |
| **B (orange)** | Next tier — 15% of revenue | Check weekly or when reorder signal fires |
| **C (green)** | Long tail — 5% of revenue | Let the system handle it; check monthly |

**Simple rule:** Start your day with A-class reorder signals. If a C-class SKU fires a signal
but you're short on time, it can wait until tomorrow.

---

## When to Override the System

The forecast is a tool, not a rule. Override the reorder signal when:

- **You know something the system doesn't** — e.g. a client called to say they're pausing orders,
  or a new contract is about to launch and demand will spike.
- **The MAPE alert is showing** and you've checked the recent demand manually and it looks unusual.
- **Lead time has changed** — e.g. a supplier told you delivery will be 2 weeks late.
  Update the lead time in the WMS and tell the BA team so the system can be corrected.

**Always record overrides.** Use the override log (shared Excel, pinned in your Teams channel).
This helps the BA team improve the forecasting model over time.

---

## Getting Help

| Question | Contact |
|---|---|
| Dashboard not loading / data looks wrong | IT helpdesk |
| Forecast numbers seem off / I think there's a data error | BA team (Vinyl Kiran Anipe) |
| Lead time or SKU info needs updating in the system | Your supervisor + WMS team |
| I want to suggest an improvement to this guide | BA team — always welcome |

---

## Glossary

**MAPE** — Mean Absolute Percentage Error. Measures forecast accuracy. 15% means the forecast
was off by an average of 15% vs actual demand. Lower is better.

**Moving Average (MA14)** — Average of the past 14 days of demand. Smooths out day-to-day
noise so you get a stable baseline.

**Reorder Point** — The stock level at which you should place a new order, calculated to arrive
before you run out, accounting for lead time and safety stock.

**Safety Stock** — Extra units held as a buffer against demand spikes or late deliveries.
A-class SKUs have higher safety stock because a stockout on these SKUs has the biggest
financial impact.

**Seasonality Index** — A number that shows how busy a given month is compared to average.
An index of 1.20 means that month is typically 20% busier than a normal month.

---

*Guide version 1.0 · Questions? Contact: Vinyl Kiran Anipe (BA team) · June 2024*
