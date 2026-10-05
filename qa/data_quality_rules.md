# Data Quality Rules Catalog
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY NOTICE**: All data quality rules and threshold criteria defined herein apply to the relational schema and analytical data marts derived from **100% synthetic** retail transaction data.

---

## 1. Primary Key & Completeness Rules

| Rule ID | Table | Attribute | Condition / Constraint | Severity | Business Rationale |
|:---|:---|:---|:---|:---:|:---|
| **R-PK-01** | `orders` | `order_id` | `NOT NULL` & `UNIQUE` | CRITICAL | Order transaction primary key must be unique and non-null to prevent duplicate revenue recognition. |
| **R-PK-02** | `customers` | `customer_id` | `NOT NULL` & `UNIQUE` | CRITICAL | Customer master key must be unique to ensure accurate RFM segmentation and cohort tracking. |
| **R-PK-03** | `products` | `product_id` | `NOT NULL` & `UNIQUE` | CRITICAL | Product catalog master key must be unique across all 40 catalog SKUs. |
| **R-PK-04** | `categories` | `category_id` | `NOT NULL` & `UNIQUE` | CRITICAL | Category master key must be unique across all 8 product categories. |

---

## 2. Value Validity & Range Rules

| Rule ID | Table | Attribute | Condition / Constraint | Severity | Business Rationale |
|:---|:---|:---|:---|:---:|:---|
| **R-VAL-01** | `order_items` | `quantity` | `quantity > 0` | CRITICAL | Order line items must reflect positive purchased unit quantities. |
| **R-VAL-02** | `order_items` | `unit_price` | `unit_price > 0` | CRITICAL | Product selling prices must be strictly positive. |
| **R-VAL-03** | `order_items` | `item_total` | `item_total = (quantity * unit_price) - discount_amount` | HIGH | Line item revenue must equal unit price times quantity minus discount. |
| **R-VAL-04** | `orders` | `total_amount` | `total_amount > 0` for valid orders | HIGH | Total order revenue must be positive for completed/shipped transactions. |

---

## 3. Referential Integrity Rules

| Rule ID | Child Table | Foreign Key | Parent Table | Parent Key | Action on Failure |
|:---|:---|:---|:---|:---|:---|
| **R-RI-01** | `order_items` | `order_id` | `orders` | `order_id` | Quarantine orphan line items; delete invalid records. |
| **R-RI-02** | `order_items` | `product_id` | `products` | `product_id` | Quarantine line items with invalid product IDs. |
| **R-RI-03** | `orders` | `customer_id` | `customers` | `customer_id` | Quarantine orphan orders with unmapped customer IDs. |
| **R-RI-04** | `shipping` | `order_id` | `orders` | `order_id` | Quarantine orphan shipping events. |
| **R-RI-05** | `payments` | `order_id` | `orders` | `order_id` | Quarantine orphan payment records. |

---

## 4. Chronological & Status Consistency Rules

| Rule ID | Entity | Rule Logic | Severity | Business Rationale |
|:---|:---|:---|:---:|:---|
| **R-CHR-01** | Fulfillment | `actual_delivery_date >= DATE(order_date)` | HIGH | Delivery cannot occur prior to order placement date. |
| **R-CHR-02** | Shipping | `shipped_date >= DATE(order_date)` | HIGH | Shipment dispatch date cannot precede order date. |
| **R-STA-01** | Operations | `order_status = 'Cancelled' <=> delivery_status = 'Cancelled/Failed'` | HIGH | Cancelled transactions must have matching failed/cancelled shipping status. |
| **R-STA-02** | Revenue | `order_status IN ('Completed', 'Shipped')` for Net Revenue | CRITICAL | Revenue calculations must exclude cancelled, refunded, and pending orders. |

---

## 5. Cross-Platform Reconciliation Rules

| Rule ID | Financial Metric | Source Systems | Tolerance | Enforcement |
|:---|:---|:---|:---:|:---|
| **R-REC-01** | Total Revenue | SQL Monthly Summary = Python RFM = Power BI FactOrders | `$0.00` | Must equal **$3,990,811.00** exactly. |
| **R-REC-02** | Total Orders | SQL Order Count = Power BI FactOrders Count | `0 orders` | Must equal **5,842** orders exactly. |
| **R-REC-03** | Active Customers | SQL Distinct Customers = Python RFM Count = Power BI | `0 customers` | Must equal **1,107** active customers. |
| **R-REC-04** | Gross Profit | Line-item gross profit sum = Category summary sum | `$0.00` | Must equal **$1,240,548.65** exactly. |
| **R-REC-05** | Carrier SLA Rate | FactShipping SLA % = SQL Question 17 SLA % | `0.00%` | Must equal **74.47%** exactly. |
