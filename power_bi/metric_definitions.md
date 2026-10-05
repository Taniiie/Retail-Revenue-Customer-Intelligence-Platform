# Authoritative Metric Definitions Dictionary
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY NOTICE**: All metrics, calculations, and expected values in this document are derived from **100% synthetic** retail transaction data generated for portfolio analytics demonstration.

---

## Overview

To maintain complete cross-platform consistency and ensure interview defensibility, this dictionary defines the exact business definitions, SQL implementations, Python transformations, DAX formulas, expected benchmark values, and filtering assumptions for all core platform metrics.

---

## 1. Total Revenue

* **Metric Name**: Total Revenue (Net Revenue)
* **Business Definition**: The total financial volume generated from completed and shipped sales orders, excluding cancelled, refunded, or pending transactions.
* **Filtering Assumptions**: Excludes `order_status IN ('Cancelled', 'Refunded', 'Processing')`. Includes shipping fees paid by customer.
* **SQL Implementation** (`sql/03_business_analytics.sql`):
  ```sql
  SELECT SUM(total_amount) AS total_revenue
  FROM orders
  WHERE order_status IN ('Completed', 'Shipped');
  ```
* **Python Implementation** (`src/sql_analytics_engine.py` / `src/rfm_analyzer.py`):
  ```python
  total_revenue = df[df['order_status'].isin(['Completed', 'Shipped'])]['total_amount'].sum()
  ```
* **DAX Implementation** (`power_bi/dax_measure_dictionary.md`):
  ```dax
  Total Revenue = 
      CALCULATE(
          SUM(FactOrders[total_amount]),
          FactOrders[order_status] IN { "Completed", "Shipped" }
      )
  ```
* **Expected Validation Value**: **$3,990,811.00**

---

## 2. Total Orders

* **Metric Name**: Total Valid Orders
* **Business Definition**: The count of distinct completed and shipped transaction orders.
* **Filtering Assumptions**: Strictly counts unique `order_id` records where `order_status IN ('Completed', 'Shipped')`.
* **SQL Implementation**:
  ```sql
  SELECT COUNT(DISTINCT order_id) AS total_orders
  FROM orders
  WHERE order_status IN ('Completed', 'Shipped');
  ```
* **Python Implementation**:
  ```python
  total_orders = df[df['order_status'].isin(['Completed', 'Shipped'])]['order_id'].nunique()
  ```
* **DAX Implementation**:
  ```dax
  Total Orders = 
      CALCULATE(
          DISTINCTCOUNT(FactOrders[order_id]),
          FactOrders[order_status] IN { "Completed", "Shipped" }
      )
  ```
* **Expected Validation Value**: **5,842 orders**

---

## 3. Average Order Value (AOV)

* **Metric Name**: Average Order Value (AOV)
* **Business Definition**: The average monetary value spent by customers per completed/shipped transaction.
* **Filtering Assumptions**: `Total Revenue / Total Orders`.
* **SQL Implementation**:
  ```sql
  SELECT ROUND(SUM(total_amount) / COUNT(DISTINCT order_id), 2) AS aov
  FROM orders
  WHERE order_status IN ('Completed', 'Shipped');
  ```
* **Python Implementation**:
  ```python
  aov = total_revenue / total_orders
  ```
* **DAX Implementation**:
  ```dax
  AOV = DIVIDE([Total Revenue], [Total Orders], 0)
  ```
* **Expected Validation Value**: **$683.12**

---

## 4. Active Customers

* **Metric Name**: Total Active Customers
* **Business Definition**: The count of distinct registered customers who have placed at least one completed or shipped order.
* **Filtering Assumptions**: Out of 1,498 total registered customers, 1,107 have valid completed/shipped orders. 391 registered accounts have zero valid orders (only cancelled/refunded/processing).
* **SQL Implementation**:
  ```sql
  SELECT COUNT(DISTINCT customer_id) AS active_customers
  FROM orders
  WHERE order_status IN ('Completed', 'Shipped');
  ```
* **Python Implementation**:
  ```python
  active_customers = df[df['order_status'].isin(['Completed', 'Shipped'])]['customer_id'].nunique()
  ```
* **DAX Implementation**:
  ```dax
  Active Customers = 
      CALCULATE(
          DISTINCTCOUNT(FactOrders[customer_id]),
          FactOrders[order_status] IN { "Completed", "Shipped" }
      )
  ```
* **Expected Validation Value**: **1,107 active customers**

---

## 5. Gross Profit

* **Metric Name**: Total Gross Profit
* **Business Definition**: Cumulative line-item gross margin generated from products sold in valid completed and shipped orders.
* **Filtering Assumptions**: Line Gross Profit = `item_total - (cost_price * quantity)`. Excludes cancelled and refunded line items.
* **SQL Implementation**:
  ```sql
  SELECT SUM(oi.item_total - (p.cost_price * oi.quantity)) AS gross_profit
  FROM order_items oi
  JOIN orders o ON oi.order_id = o.order_id
  JOIN products p ON oi.product_id = p.product_id
  WHERE o.order_status IN ('Completed', 'Shipped');
  ```
* **Python Implementation**:
  ```python
  fact_items['line_gross_profit'] = fact_items['item_total'] - (fact_items['cost_price'] * fact_items['quantity'])
  gross_profit = fact_items[fact_items['order_status'].isin(['Completed', 'Shipped'])]['line_gross_profit'].sum()
  ```
* **DAX Implementation**:
  ```dax
  Gross Profit = 
      CALCULATE(
          SUM(FactOrderItems[line_gross_profit]),
          FactOrderItems[order_status] IN { "Completed", "Shipped" }
      )
  ```
* **Expected Validation Value**: **$1,240,548.65**

---

## 6. Gross Profit Margin %

* **Metric Name**: Gross Profit Margin Percentage
* **Business Definition**: The proportion of item product revenue retained as profit after accounting for product unit cost prices.
* **Filtering Assumptions**: Ratio of `Gross Profit` over total item product sales ($3,990,811.00 total order revenue).
* **SQL Implementation**:
  ```sql
  SELECT ROUND(SUM(line_gross_profit) * 100.0 / SUM(item_total), 2) AS gross_margin_pct
  FROM (...)
  ```
* **Python Implementation**:
  ```python
  gross_margin_pct = (gross_profit / item_revenue) * 100
  ```
* **DAX Implementation**:
  ```dax
  Gross Profit Margin % = DIVIDE([Gross Profit], [Total Revenue], 0)
  ```
* **Expected Validation Value**: **31.08%** (Overall order level margin) / **32.88%** (Direct item revenue margin excluding shipping charges).

---

## 7. Carrier SLA Compliance Rate (On-Time Delivery Rate)

* **Metric Name**: Carrier SLA Compliance Rate / On-Time Delivery Rate
* **Business Definition**: The percentage of fulfilled shipments delivered on or before the estimated delivery date out of all completed shipments with a recorded delivery date.
* **Filtering Assumptions**: Evaluates only delivered shipments (`actual_delivery_date IS NOT NULL`). Excludes in-transit (514) and cancelled/failed (652) shipments.
* **SQL Implementation** (`sql/03_business_analytics.sql` Q17):
  ```sql
  SELECT 
      ROUND(
          COUNT(CASE WHEN s.delivery_status = 'Delivered On-Time' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN s.actual_delivery_date IS NOT NULL THEN 1 END), 0), 
          2
      ) AS carrier_sla_compliance_pct
  FROM shipping s
  WHERE s.actual_delivery_date IS NOT NULL;
  ```
* **Python Implementation**:
  ```python
  delivered = df_shipping[df_shipping['actual_delivery_date'].notna()]
  on_time_pct = (len(delivered[delivered['delivery_status'] == 'Delivered On-Time']) / len(delivered)) * 100
  ```
* **DAX Implementation**:
  ```dax
  On-Time Delivery Rate % = 
      VAR DeliveredShipments = 
          CALCULATE(
              COUNT(FactShipping[shipping_id]),
              NOT ISBLANK(FactShipping[actual_delivery_date])
          )
      VAR OnTimeShipments = 
          CALCULATE(
              COUNT(FactShipping[shipping_id]),
              FactShipping[delivery_status] = "Delivered On-Time"
          )
      RETURN DIVIDE(OnTimeShipments, DeliveredShipments, 0)
  ```
* **Expected Validation Value**: **74.47%** (Overall across 5,316 delivered orders: 3,959 On-Time / 1,357 Delayed). Carrier breakdown:
  * DHL Express: **75.36%** (1,003 / 1,331)
  * UPS Ground: **74.90%** (973 / 1,299)
  * USPS Priority: **73.84%** (971 / 1,315)
  * FedEx Express: **73.81%** (1,012 / 1,371)
* **Reconciliation Note**: If calculated against all 5,842 valid orders (including 514 in-transit), the rate is 67.77%. If calculated against all 6,494 raw shipping records (including 652 cancelled/failed), the rate is 60.96%. The **authoritative platform definition** is **74.47%** (Delivered On-Time / Delivered Total).

---

## 8. RFM Segment Revenue

* **Metric Name**: Segment Monetary Spend
* **Business Definition**: Sum of monetary revenue contributed by customers categorized into each RFM persona.
* **Filtering Assumptions**: Customer segmentation based on 5x5x5 quantile scoring with standard rules (`Champions`, `Loyal Customers`, `At Risk`, `Needs Attention`, `Hibernating`, `Potential Loyalists`, `Lost Customers`).
* **Expected Validation Values**:
  * **Champions**: 254 customers | **$2,193,910.01** (54.97% of total revenue)
  * **Loyal Customers**: 175 customers | **$707,457.22** (17.73%)
  * **At Risk**: 157 customers | **$600,497.52** (15.05%)
  * **Needs Attention**: 217 customers | **$199,903.92** (5.01%)
  * **Hibernating**: 123 customers | **$167,870.40** (4.21%)
  * **Potential Loyalists**: 52 customers | **$72,947.75** (1.83%)
  * **Lost Customers**: 129 customers | **$48,224.18** (1.21%)
  * **Total**: 1,107 active customers | **$3,990,811.00**

---

## 9. Cohort Month 1 Retention %

* **Metric Name**: Cohort 1-Month Retention Rate
* **Business Definition**: The percentage of customers in an initial acquisition cohort who returned to make at least one purchase 1 month after their initial acquisition month.
* **Filtering Assumptions**: Based on month of customer's first completed/shipped purchase.
* **Python / DAX Calculation**: `(Active Cohort Customers in Month 1) / (Initial Cohort Size in Month 0) * 100`
* **Expected Validation Value**: **40.98%** (Weighted average across all eligible acquisition cohorts).

---

## 10. Cohort Month 6 Retention %

* **Metric Name**: Cohort 6-Month Retention Rate
* **Business Definition**: The percentage of customers in an initial acquisition cohort who remained active 6 months after acquisition.
* **Calculation Method**: Unweighted simple arithmetic average across all 18 eligible acquisition cohorts with Month 6 data (Jan 2024 through Jun 2025).
* **Expected Validation Value**: **19.54%** (Simple arithmetic mean) / **18.97%** (Weighted average by initial cohort size).

---

## 11. Historical Realized LTV

* **Metric Name**: Historical Realized Lifetime Value (LTV)
* **Business Definition**: Cumulative revenue per customer realized by an acquisition cohort over $N$ months of customer lifecycle.
* **Filtering Assumptions**: Realized cumulative revenue divided by initial cohort size. Not a predictive ML model.
* **Expected Validation Values**:
  * Month 0: **$1,048.87** / customer
  * Month 1: **$1,592.51** / customer
  * Month 3: **$2,168.32** / customer
  * Month 6: **$2,610.15** / customer
  * Month 12: **$3,377.90** / customer (Simple average across all cohorts) / **$3,838.25** (2024 full-year cohorts)


---

## 12. Product Count & Category Universe

* **Metric Name**: Catalog Product Count
* **Business Definition**: Total active SKUs cataloged in the retail product dimension.
* **Authoritative Value**: **40 Products** evenly distributed across 8 product categories (5 SKUs per category).
  * Apparel & Activewear: 5 SKUs
  * Beauty & Personal Care: 5 SKUs
  * Fitness & Outdoor Gear: 5 SKUs
  * Footwear & Accessories: 5 SKUs
  * Home Appliances & Decor: 5 SKUs
  * Kitchenware & Dining: 5 SKUs
  * Laptops & Computing: 5 SKUs
  * Smartphones & Audio: 5 SKUs
