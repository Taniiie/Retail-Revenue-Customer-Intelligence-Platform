# Power BI Dashboard Specification
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY & IMPLEMENTATION STATUS**: 
> 
> 1. **Data Transparency**: All data in this dashboard specification is derived from **100% synthetic** retail transaction data generated for portfolio analytics demonstration.
> 2. **Implementation Status**: This deliverable is a **Power BI-Ready Interactive Dashboard Specification**. It specifies the exact visual components, grid placement, formatting guidelines, field bindings, and cross-filtering rules required to assemble the report in Power BI Desktop.

---

## Dashboard Structure Overview

| Page # | Title | Primary Business Question | Key Visual Types | Target Audience |
|:---|:---|:---|:---|:---|
| 1 | Executive Revenue Overview | "How is top-line revenue performing over time and by geography?" | KPI Cards, Combo Chart, Bar Chart, Treemap | C-Suite, VP Sales |
| 2 | Customer Intelligence & RFM | "Who are our most valuable customers and where is churn risk?" | RFM Scatter Plot, Persona Grid, Segment Matrix | Head of CRM, Marketing |
| 3 | Cohort Retention & Customer LTV | "How well do newly acquired customer cohorts retain over 12 months?" | Heatmap Matrix, Line Chart, Summary Table | Growth Team, Finance |
| 4 | Product Economics & Operations | "Which products drive gross margin and how is carrier fulfillment performing?" | Clustered Bar, Donut Chart, Quadrant Scatter, Table | Ops Manager, Merchandising |

---

## Page 1: Executive Revenue Overview

### Layout & Visual Grid

**Row 1 — High-Level KPI Cards (Top 5 Cards)**

| Position | KPI Label | DAX Measure | Format | Target Benchmark / Benchmark |
|:---|:---|:---|:---|:---|
| Card 1 | Total Revenue | `[Total Revenue]` | `$#,##0` | **$3,990,811.00** |
| Card 2 | Total Orders | `[Total Orders]` | `#,##0` | **5,842** |
| Card 3 | Average Order Value | `[AOV]` | `$#,##0.00` | **$683.12** |
| Card 4 | Gross Profit Margin | `[Gross Profit Margin %]` | `0.0%` | **31.08%** (Overall) / **32.88%** (Item) |
| Card 5 | MoM Revenue Growth | `[MoM Revenue Growth %]` | `+0.0%` | Conditional Red/Green |

**Row 2 — Primary Revenue Trends (Middle Row)**

| Position | Visual Type | Data Fields | Visual Details |
|:---|:---|:---|:---|
| Left (60%) | Combo Chart (Line + Clustered Column) | Shared Axis: `DimDate[year_month]`<br>Column: `[Total Revenue]`<br>Line: `[Total Orders]` | Dual Y-axis. Column displays net revenue, line displays completed order volume. |
| Right (40%) | Stacked Bar Chart | Y-Axis: `DimProduct[category_name]`<br>X-Axis: `[Total Revenue]`<br>Legend: `DimCategory[department]` | Ranks all 8 categories by net revenue contribution. |

**Row 3 — Breakdown & Product Drivers (Bottom Row)**

| Position | Visual Type | Data Fields | Visual Details |
|:---|:---|:---|:---|
| Left (50%) | Treemap | Group: `DimCustomer[country]` $\rightarrow$ `DimCustomer[state]`<br>Values: `[Total Revenue]` | Geographic revenue distribution across US/Canada/UK/Germany/Australia. |
| Right (50%) | Top 10 Product Table | Columns: `DimProduct[product_name]`, `[Total Orders]`, `[Total Revenue]`, `[Gross Profit]` | Ranks top products from the 40 SKU catalog. |

**Slicers**:
- Date Range: `DimDate[date]` (Between Slicer)
- Category: `DimProduct[category_name]` (Multi-select Dropdown)
- Region: `DimCustomer[country]` (Dropdown)

---

## Page 2: Customer Intelligence & RFM

### Layout & Visual Grid

**Row 1 — Customer KPI Cards (Top 4 Cards)**

| KPI Label | DAX Measure | Format | Benchmark |
|:---|:---|:---|:---|
| Active Customers | `[Active Customers]` | `#,##0` | **1,107** (out of 1,498 total) |
| Revenue per Active Customer | `[Revenue per Customer]` | `$#,##0.00` | **$3,605.07** |
| Champion Revenue Contribution | `[Champion Revenue Contribution %]` | `0.0%` | **54.97%** |
| Repeat Buyer Ratio | `[Repeat Purchase Rate]` | `0.0%` | **83.65%** |

**Row 2 — RFM Persona Matrix & Distribution**

| Position | Visual Type | Data Fields | Visual Details |
|:---|:---|:---|:---|
| Left (50%) | Scatter Plot | X-Axis: `DimCustomer[recency]` (Days)<br>Y-Axis: `DimCustomer[monetary]` ($)<br>Size: `DimCustomer[frequency]`<br>Color: `DimCustomer[rfm_segment]` | Clusters active customers across 7 RFM personas. |
| Right (50%) | Clustered Column Chart | X-Axis: `DimCustomer[rfm_segment]`<br>Y-Axis 1: `[RFM Segment Customer Count]`<br>Y-Axis 2: `[RFM Segment Revenue]` | Displays customer volume vs revenue per segment. |

**Row 3 — At-Risk Action Table**

| Position | Visual Type | Data Fields | Details |
|:---|:---|:---|:---|
| Full Width | Table | Columns: Customer Name, Email, RFM Segment, Recency Days, Order Count, Monetary Spend, Last Order Date | Filtered to `rfm_segment IN ('At Risk', 'Hibernating', 'Needs Attention')`. |

---

## Page 3: Cohort Retention & Customer LTV

### Layout & Visual Grid

**Row 1 — Cohort Summary KPIs**

| KPI Label | Benchmark Value | Description |
|:---|:---|:---|
| Month 1 Retention Rate | **40.98%** | Average retention 1 month post-acquisition |
| Month 6 Retention Rate | **19.54%** | Simple arithmetic average retention 6 months post-acquisition |
| 12-Month Realized LTV | **$3,377.90** | Average cumulative revenue per customer at 12 months across all cohorts |

**Row 2 — Retention Matrix Heatmap**

| Visual Type | Data Source | Formatting |
|:---|:---|:---|
| Matrix Visual | `cohort_retention.csv` | Rows: `Cohort Month`, Columns: `Month 0` to `Month 12`, Values: `Retention %`. Applied conditional green-to-red color scale. |

**Row 3 — LTV Growth Trajectory**

| Visual Type | Data Source | Details |
|:---|:---|:---|
| Line Chart | `cohort_ltv.csv` | X-Axis: `Cohort Index Month (0-12)`, Y-Axis: `Cumulative LTV ($)`, Legend: `Cohort Month`. Demonstrates non-decreasing monotonic growth. |

---

## Page 4: Product Economics & Operations

### Layout & Visual Grid

**Row 1 — Operations KPI Cards**

| KPI Label | DAX Measure / Benchmark | Benchmark Value |
|:---|:---|:---|
| Gross Profit | `[Gross Profit]` | **$1,240,548.65** |
| Carrier SLA Compliance Rate | `[On-Time Delivery Rate %]` | **74.47%** (3,959 / 5,316 delivered) |
| Average Shipping Lag | `[Avg Shipping Lag Days]` | **3.01 days** |
| Catalog SKU Count | Catalog Universe | **40 Products** across 8 Categories |

**Row 2 — Product Margin & Carrier SLA**

| Position | Visual Type | Data Fields | Visual Details |
|:---|:---|:---|:---|
| Left (50%) | Clustered Bar Chart | Y-Axis: `DimProduct[category_name]`<br>X1: `Gross Revenue`<br>X2: `Gross Profit` | Side-by-side revenue vs gross profit per category. |
| Right (50%) | Clustered Column Chart | X-Axis: `FactShipping[carrier]`<br>Y-Axis: `SLA Compliance %` | Carrier comparison: DHL (75.36%), UPS (74.90%), USPS (73.84%), FedEx (73.81%). |

**Row 3 — Fulfillment Distribution & Payment Gateways**

| Position | Visual Type | Data Fields | Visual Details |
|:---|:---|:---|:---|
| Left (50%) | Donut Chart | Legend: `FactShipping[delivery_status]`<br>Values: `COUNT(shipping_id)` | Delivery status split: Delivered On-Time (3,959), Delivered Delayed (1,357), In-Transit (514), Cancelled/Failed (652). |
| Right (50%) | Stacked Bar Chart | Y-Axis: `FactShipping[payment_method]`<br>X-Axis: `[Total Orders]`<br>Legend: `FactOrders[order_status]` | Payment gateway order status breakdown (Credit Card, PayPal, Debit Card, Apple Pay). |

---

## Global Design Standards

- **Color Palette**: Executive Dark Navy (#1B2A4A), Accent Teal (#2D9CDB), Warning Amber (#F2C94C), Alert Coral (#EB5757).
- **Typography**: Segoe UI, 11pt Body, 24pt Bold KPI metrics.
- **Data Callouts**: Mandatory "100% SYNTHETIC DATA — PORTFOLIO SPECIFICATION" banner embedded in header.

---

## Manual Assembly Checklist (Power BI Desktop)

1. Open Power BI Desktop $\rightarrow$ Click **Get Data** $\rightarrow$ Load all 9 CSV files from `power_bi/data_sources/`.
2. Configure `DimDate` as Date Table and build single-direction 1:N relationships per `power_bi/data_model.md`.
3. Create measure table `_Measures` and insert formulas from `power_bi/dax_measure_dictionary.md`.
4. Construct visual layout for Pages 1–4 using grid coordinates and fields specified above.
5. Save project file as `retail_intelligence_dashboard.pbix`.
