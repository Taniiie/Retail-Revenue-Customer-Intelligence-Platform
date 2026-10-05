# Power BI Data Model Specification
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY & IMPLEMENTATION STATUS**: 
> 
> 1. **Data Transparency**: All data in this Power BI model is derived from **100% synthetic** retail transaction data generated for portfolio analytics demonstration.
> 2. **Implementation Status**: This deliverable is a **Power BI-Ready Model & Interactive Dashboard Specification**. All star schema datasets are exported to `power_bi/data_sources/`, and all DAX measures are fully defined and mathematically reconciled against SQL and Python.

---

## Data Lineage

```
Raw Synthetic CSV Data (src/data_generator.py)
  -> SQLite Relational Database (3NF normalized, src/db_setup.py)
    -> Data Quality Validation Engine (src/data_quality_validator.py)
      -> SQL Business Analytics Suite (sql/03_business_analytics.sql)
        -> Python RFM & Cohort Analytics (src/rfm_analyzer.py, src/cohort_analyzer.py)
          -> Star Schema Export (src/powerbi_star_schema.py)
            -> Power BI Data Model & DAX Dictionary (power_bi/data_model.md, power_bi/dax_measure_dictionary.md)
              -> Dashboard Layout & Manual Import Protocol (power_bi/dashboard_specification.md)
```

---

## Manual Power BI Desktop Implementation Protocol

If importing these deliverables into Power BI Desktop:

1. **Import Data Sources**:
   * Open Power BI Desktop $\rightarrow$ Click **Get Data** $\rightarrow$ Select **Folder** or **Text/CSV**.
   * Target folder: `power_bi/data_sources/`.
   * Import all 9 CSV files: `DimDate.csv`, `DimCustomer.csv`, `DimProduct.csv`, `DimCategory.csv`, `FactOrders.csv`, `FactOrderItems.csv`, `FactShipping.csv`, `cohort_retention.csv`, `cohort_ltv.csv`.

2. **Configure Data Types & Mark Date Table**:
   * Set `DimDate[date]` column to **Date** data type.
   * Right-click `DimDate` $\rightarrow$ Select **Mark as Date Table** $\rightarrow$ Choose `date` column.
   * Set surrogate keys (`date_key`, `customer_id`, `product_id`, `order_id`) to **Whole Number**.

3. **Configure Model Relationships**:
   * Navigate to the **Model View**.
   * Create relationships as specified in the [Relationships](#relationships) section below (1:N Single Direction).

4. **Add DAX Measures**:
   * Click **New Table** $\rightarrow$ Name it `_Measures`.
   * Copy-paste all 20 DAX measure definitions from `power_bi/dax_measure_dictionary.md`.

5. **Build Visual Pages**:
   * Construct Page 1 (Executive Overview), Page 2 (Customer RFM Intelligence), Page 3 (Cohort Retention & LTV), and Page 4 (Operations & Fulfillment) following `power_bi/dashboard_specification.md`.

---

## Star Schema Entity-Relationship Diagram

```
                    ┌──────────────┐
                    │   DimDate    │
                    │ (date_key PK)│
                    └──────┬───────┘
                           │ 1:N
    ┌──────────────┐   ┌───┴───────────┐   ┌──────────────┐
    │ DimCustomer  │──►│  FactOrders   │◄──│  DimProduct   │
    │(customer_id) │   │  (order_id PK)│   │(product_id)   │
    └──────────────┘   └───┬───────────┘   └───┬──────────┘
          │ 1:N            │ 1:N               │ 1:N
          │            ┌───┴───────────┐       │
          └───────────►│FactOrderItems │◄──────┘
                       │ (item_id PK)  │
                       └───────────────┘
                           │
    ┌──────────────┐       │ (via order_id)
    │ DimCategory  │       │
    │(category_id) │   ┌───┴───────────┐
    └──────────────┘   │ FactShipping  │
                       │(shipping_id PK)│
                       └───────────────┘
```

---

## Table Specifications

### Dimension Tables

#### DimDate
| Column | Type | Description |
|:---|:---|:---|
| `date_key` (PK) | Integer | Surrogate key in YYYYMMDD format |
| `date` | Date | Calendar date |
| `year` | Integer | Calendar year (2024, 2025) |
| `quarter` | Integer | Quarter number (1-4) |
| `quarter_label` | Text | Quarter label (Q1, Q2, Q3, Q4) |
| `month_number` | Integer | Month number (1-12) |
| `month_name` | Text | Full month name (January, February...) |
| `month_short` | Text | Abbreviated month (Jan, Feb...) |
| `year_month` | Text | Year-Month string (2024-01) |
| `year_quarter` | Text | Year-Quarter string (2024-Q1) |
| `week_number` | Integer | ISO week number |
| `day_of_week` | Integer | Day of week (0=Monday, 6=Sunday) |
| `day_name` | Text | Full day name |
| `is_weekend` | Integer | Weekend flag (0/1) |
| `day_of_month` | Integer | Day of month (1-31) |
| `month_sort_key` | Integer | Sort key for chronological ordering |

**Row Count**: 731 rows (2024-01-01 to 2025-12-31)

---

#### DimCustomer
| Column | Type | Description |
|:---|:---|:---|
| `customer_id` (PK) | Integer | Unique customer identifier |
| `first_name` | Text | Customer first name |
| `last_name` | Text | Customer last name |
| `email` | Text | Customer email address |
| `city` | Text | Customer city |
| `state` | Text | Customer state/province |
| `country` | Text | Customer country |
| `signup_date` | Date | Customer registration date |
| `customer_segment_tier` | Text | Original tier (Standard) |
| `recency` | Integer | Days since last order (from reference date) |
| `frequency` | Integer | Total completed/shipped orders |
| `monetary` | Decimal | Total net revenue from customer |
| `r_score` | Integer | Recency quantile score (1-5) |
| `f_score` | Integer | Frequency quantile score (1-5) |
| `m_score` | Integer | Monetary quantile score (1-5) |
| `rfm_score_str` | Text | Composite RFM string (e.g., "555") |
| `rfm_score_avg` | Decimal | Average RFM score |
| `rfm_segment` | Text | Customer persona segment |
| `last_order_date` | Date | Most recent order date |

**Row Count**: 1,498 rows (1,107 active customers with valid orders; 391 registered customers with no valid orders)

---

#### DimProduct
| Column | Type | Description |
|:---|:---|:---|
| `product_id` (PK) | Integer | Unique product identifier |
| `product_name` | Text | Product display name |
| `category_id` (FK) | Integer | Foreign key to DimCategory |
| `category_name` | Text | Category name (denormalized) |
| `department` | Text | Department name (denormalized) |
| `cost_price` | Decimal | Product cost of goods sold |
| `unit_price` | Decimal | Product list/selling price |
| `stock_quantity` | Integer | Current stock level |
| `list_margin_pct` | Decimal | List price margin percentage |

**Row Count**: 40 products across 8 categories (Authoritative catalog universe)

---

#### DimCategory
| Column | Type | Description |
|:---|:---|:---|
| `category_id` (PK) | Integer | Unique category identifier |
| `category_name` | Text | Category name |
| `department` | Text | Department name |

**Row Count**: 8 categories across 4 departments

---

### Fact Tables

#### FactOrders (Grain: One row per order)
| Column | Type | Description |
|:---|:---|:---|
| `order_id` (PK) | Integer | Unique order identifier |
| `customer_id` (FK) | Integer | Foreign key to DimCustomer |
| `order_date` | DateTime | Order placement timestamp |
| `order_date_key` (FK) | Integer | Foreign key to DimDate |
| `order_status` | Text | Order status (Completed/Shipped/Processing/Cancelled/Refunded) |
| `shipping_cost` | Decimal | Shipping fee charged |
| `total_amount` | Decimal | Total order amount (items + shipping) |

**Row Count**: 5,842 orders (Completed/Shipped) / 6,494 raw total transactions

---

#### FactOrderItems (Grain: One row per line item)
| Column | Type | Description |
|:---|:---|:---|
| `item_id` (PK) | Integer | Unique line item identifier |
| `order_id` (FK) | Integer | Foreign key to FactOrders |
| `product_id` (FK) | Integer | Foreign key to DimProduct |
| `customer_id` (FK) | Integer | Foreign key to DimCustomer |
| `order_date` | DateTime | Order date |
| `order_date_key` (FK) | Integer | Foreign key to DimDate |
| `order_status` | Text | Order status |
| `quantity` | Integer | Units purchased |
| `sold_unit_price` | Decimal | Actual selling price |
| `discount_amount` | Decimal | Discount applied |
| `item_total` | Decimal | Line item total |
| `cost_price` | Decimal | Product COGS |
| `line_gross_profit` | Decimal | Line-level gross profit |

**Row Count**: 11,811 line items

---

#### FactShipping (Grain: One row per shipment)
| Column | Type | Description |
|:---|:---|:---|
| `shipping_id` (PK) | Integer | Unique shipment identifier |
| `order_id` (FK) | Integer | Foreign key to FactOrders |
| `customer_id` (FK) | Integer | Foreign key to DimCustomer |
| `carrier` | Text | Shipping carrier name |
| `shipped_date` | DateTime | Ship date |
| `estimated_delivery_date` | Date | Estimated delivery date |
| `actual_delivery_date` | Date | Actual delivery date |
| `delivery_status` | Text | Delivery status |
| `order_status` | Text | Related order status |
| `payment_method` | Text | Payment method used |
| `payment_status` | Text | Payment processing status |

**Row Count**: 6,494 shipments (5,316 delivered with recorded delivery dates)

---

## Relationships

| From Table | From Column | To Table | To Column | Cardinality | Cross-Filter | Active |
|:---|:---|:---|:---|:---|:---|:---|
| FactOrders | `order_date_key` | DimDate | `date_key` | Many-to-One | Single (Dim→Fact) | Yes |
| FactOrders | `customer_id` | DimCustomer | `customer_id` | Many-to-One | Single (Dim→Fact) | Yes |
| FactOrderItems | `order_id` | FactOrders | `order_id` | Many-to-One | Single | Yes |
| FactOrderItems | `product_id` | DimProduct | `product_id` | Many-to-One | Single (Dim→Fact) | Yes |
| FactOrderItems | `order_date_key` | DimDate | `date_key` | Many-to-One | Single (Dim→Fact) | No (Inactive) |
| FactShipping | `order_id` | FactOrders | `order_id` | One-to-One | Single | Yes |
| DimProduct | `category_id` | DimCategory | `category_id` | Many-to-One | Single (Dim→Fact) | Yes |
