# DHL SKU Segmentation — Tableau Public Build Guide

**Author:** Vinyl Kiran Anipe  
**Project:** DHL Supply Chain — BA/DA Portfolio · Project 1  
**Data source folder:** `dashboard/tableau/`  
**Tableau Public workbook name (suggested):** `DHL_SKU_Segmentation`

---

## Data Sources to Connect

| File | Rows | Use for |
|---|---|---|
| `tableau_sku_detail.csv` | 1,664 | Charts 1, 2, 4, 5 |
| `tableau_segment_summary.csv` | 6 | Charts 2, 4 |
| `tableau_category_summary.csv` | 8 | Chart 3 |

Connect all three as separate data sources. No joins required — each chart uses one source independently.

---

## Chart 1 — Revenue Pareto Bar Chart

**File:** `tableau_sku_detail.csv`  
**Sheet name:** `01 Revenue Pareto`

### Build steps
1. Drag `Revenue_Rank` → Columns (treat as **Dimension**, not measure)
2. Drag `Revenue_Pct` → Rows (Bar chart)
3. Drag `ABC_Class` → Color
   - A = `#D40511` · B = `#FF8C00` · C = `#4CAF50`
4. Add a second axis: drag `Cumulative_Revenue_Pct` → Rows, right-click → **Dual Axis** → Synchronise
   - Change mark type for this axis to **Line**, color `#D40511`, size 2pt
5. Add two reference lines on the secondary axis:
   - Value = `80`, label `A/B boundary`, line dash, color orange
   - Value = `95`, label `B/C boundary`, line dash, color green
6. Tooltip: `SKU_ID`, `Category`, `ABC_Class`, `Total_Revenue` (formatted as `$#,##0`)
7. Title: **SKU Revenue Pareto — ABC Classification**

### Key insight to annotate
> 164 SKUs (9.9% of catalogue) drive 80% of total revenue

---

## Chart 2 — ABC/XYZ Segment Heatmap

**File:** `tableau_segment_summary.csv`  
**Sheet name:** `02 Segment Heatmap`

### Build steps
1. Drag `XYZ_Class` → Columns · `ABC_Class` → Rows
2. Drag `SKU_Count` → Color (sequential, yellow → red, `#FFF9C4` → `#D40511`)
3. Drag `SKU_Count` → Label (bold, white font)
4. Drag `Revenue_Pct` → Tooltip (formatted as `0.0"%"`)
5. Change mark type to **Square**
6. Increase mark size to fill cells — use **Size** slider
7. Add a second sheet for Revenue version:
   - Swap `SKU_Count` for `Total_Revenue` on Color and Label
   - Format label as `$#.0B` using a calculated field: `STR(ROUND([Total_Revenue]/1000000000,1))+"B"`
8. Place both sheets side-by-side on a dashboard container
9. Title: **ABC/XYZ Segment Matrix**

### Key insight to annotate
> AY segment: 115 SKUs carrying 56.3% of network revenue

---

## Chart 3 — Category Revenue Treemap

**File:** `tableau_category_summary.csv`  
**Sheet name:** `03 Category Treemap`

### Build steps
1. Drag `Category` → Color and Label
2. Drag `Total_Revenue` → Size
3. Change mark type to **Square** → Tableau will render as treemap
4. Drag `Revenue_Pct` → Label
   - Format label: `[Category]` + newline + `$[Total_Revenue formatted]` + newline + `[Revenue_Pct]%`
5. Color by `Revenue_Pct` (sequential red scale) **or** by category (manual distinct palette)
6. Add `A_Class_SKUs` to Tooltip with label `"A-class SKUs"`
7. Title: **Revenue by Product Category — 24-Month Period**

### Calculated field for label
```
[Category] + " · $" + STR(ROUND([Total_Revenue]/1000000000, 1)) + "B · " + STR([Revenue_Pct]) + "%"
```

### Key insight to annotate
> Consumer Electronics + Industrial = 55% of total revenue, ~25% of active SKUs

---

## Chart 4 — Stockout Rate by Segment Bar Chart

**File:** `tableau_segment_summary.csv`  
**Sheet name:** `04 Stockout by Segment`

### Build steps
1. Drag `Segment` → Columns (sort by `Avg_Stockout_Rate` descending)
2. Drag `Avg_Stockout_Rate` → Rows
3. Drag `ABC_Class` → Color (same palette as Chart 1)
4. Add a **Reference Line** at the constant value of the network average (`3.02`):
   - Line: dashed, grey, label `Network avg 3.02%`
5. Add `Avg_Stockout_Rate` → Label, formatted as `0.00"%"`
6. Add bar border: right-click Color → **Border** → set to `#D40511` for segments above average
   - Create a calculated field: `IF [Avg_Stockout_Rate] > 3.02 THEN "Above" ELSE "Below" END`
   - Use this field to control border color via Detail/tooltip
7. Tooltip: `Segment`, `SKU_Count`, `Avg_Stockout_Rate`, `Revenue_Pct`
8. Title: **Stockout Rate by Segment — Network Average Reference**

### Key insight to annotate
> Same ~3% rate across all segments masks vastly different revenue consequences. A-class stockouts = $379K+ unfulfilled units.

---

## Chart 5 — SKU Detail Scatter Plot (Revenue vs CV)

**File:** `tableau_sku_detail.csv`  
**Sheet name:** `05 Revenue vs Variability`

### Build steps
1. Drag `CV` → Columns · `Total_Revenue` → Rows
2. Change mark type to **Circle**, reduce opacity to 60%, size to small
3. Drag `ABC_Class` → Color
   - A = `#D40511` · B = `#FF8C00` · C = `#4CAF50`
4. Drag `Category` → Shape (optional — use distinct shapes per category)
5. Add **Reference Lines**:
   - Vertical: `CV = 0.30` (X/Y boundary), dashed, label `CV 0.30`
   - Vertical: `CV = 0.70` (Y/Z boundary), dashed, label `CV 0.70`  
     *(Note: no Z-class SKUs exist in this dataset — line is forward-looking)*
6. Format Y-axis: right-click → **Format** → Number → Currency, `$#,##0`
7. Add filter card for `Category` and `ABC_Class` so viewers can explore
8. Tooltip: `SKU_ID`, `Category`, `Segment`, `Total_Revenue`, `CV`, `Priority_Flag`
9. Title: **Revenue vs Demand Variability — ABC Classification**

### Calculated field — Quadrant label
```
IF [CV] < 0.30 AND [Total_Revenue] > WINDOW_MEDIAN(SUM([Total_Revenue]))
  THEN "High-Value · Stable (AX/BX target)"
ELSEIF [CV] >= 0.30 AND [Total_Revenue] > WINDOW_MEDIAN(SUM([Total_Revenue]))
  THEN "High-Value · Variable (AY/BY — buffer aggressively)"
ELSEIF [CV] < 0.30
  THEN "Low-Value · Stable (CX — reduce stock)"
ELSE "Low-Value · Variable (CY — review)"
END
```

### Key insight to annotate
> AY quadrant (high revenue, high CV) contains 115 SKUs carrying 56% of revenue — highest priority for policy tightening.

---

## Dashboard Layout Suggestion

```
┌────────────────────────────────────────────────────────────┐
│  DHL │ SKU Segmentation Dashboard              [4 KPI tiles]│
├──────────────────────────┬─────────────────────────────────┤
│  Chart 1: Pareto (full width)                              │
├──────────────────────────┬─────────────────────────────────┤
│  Chart 2: Heatmap        │  Chart 3: Category Treemap      │
├──────────────────────────┴─────────────────────────────────┤
│  Chart 4: Stockout by Segment (full width)                 │
├────────────────────────────────────────────────────────────┤
│  Chart 5: Revenue vs CV Scatter (full width)               │
└────────────────────────────────────────────────────────────┘
```

**Suggested KPI tiles (text objects or calculated sheets):**
- Total Active SKUs: `1,664`
- A-Class SKUs: `164` (9.9% of catalogue)
- Network Revenue: `$19.4B`
- Avg Stockout Rate: `3.02%`

---

## Formatting Conventions

| Element | Value |
|---|---|
| Primary brand color | `#D40511` (DHL Red) |
| Accent color | `#FFCC00` (DHL Yellow) |
| A-class color | `#D40511` |
| B-class color | `#FF8C00` |
| C-class color | `#4CAF50` |
| Background | `#F5F5F5` (light grey) or white |
| Font | Tableau Book or Arial |
| Header background | `#D40511` with white text |

---

## Publishing to Tableau Public

1. File → Save to Tableau Public As → `DHL_SKU_Segmentation`
2. Make sure all three CSV data sources are embedded (Extract, not Live)
3. Set workbook permissions to Public
4. Suggested description:
   > ABC/XYZ inventory segmentation analysis of 1,664 active SKUs across DHL's 3-warehouse network. 
   > Demonstrates revenue Pareto, demand variability classification, and replenishment policy framework.

---

*Build guide version 1.0 · Vinyl Kiran Anipe · DHL BA/DA Portfolio · 2024*
