# Formal Defect Log & Remediation Report
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY NOTICE**: The defects documented below represent intentional data quality flaws engineered into the raw synthetic staging dataset (`data/raw/`) to evaluate the data audit and cleaning pipeline (`src/data_quality_validator.py`, `src/db_setup.py`).

---

## Synthetic Data Defect Log

| Defect ID | Defect Summary | Detection Method | Business Impact | Remediation Strategy | Final Status |
|:---|:---|:---|:---|:---|:---:|
| **DEF-01** | **Duplicate Order Items**<br>Identical line item records present for the same order and product. | SQL `GROUP BY order_id, product_id HAVING COUNT(*) > 1`<br>Python Pandas `.duplicated()` check | Inflates line-item quantities, sales volume, and gross revenue metrics. | Deduplicated order items using `ROW_NUMBER() OVER(PARTITION BY order_id, product_id ORDER BY item_id ASC)` keeping only the first record. | **RESOLVED** |
| **DEF-02** | **Invalid Quantity & Price Values**<br>Negative or zero values in line item `quantity` ($\le 0$) or `unit_price` ($\le 0$). | Range check validation SQL query (`WHERE quantity <= 0 OR unit_price <= 0`) | Distorts AOV, product unit margins, and causes division-by-zero errors in pricing formulas. | Filtered out invalid records during raw-to-clean ETL transformation in `src/db_setup.py`. | **RESOLVED** |
| **DEF-03** | **Delivery-Before-Order Dates**<br>`actual_delivery_date` occurs prior to `order_date` timestamp. | Chronological audit query (`DATEDIFF(actual_delivery_date, order_date) < 0`) | Violates physical fulfillment logic, distorting carrier shipping lag and SLA metrics. | Re-calculated or updated invalid delivery dates using `order_date + shipping_lag_days` in data cleaning pipeline. | **RESOLVED** |
| **DEF-04** | **Orphan Foreign Key Records**<br>Payment and shipping records referencing non-existent `order_id` values. | Foreign Key Left Join check (`LEFT JOIN orders ON fk = pk WHERE pk IS NULL`) | Causes referential integrity breaks, unmapped payments, and orphan logistics events. | Enforced foreign key checks during database initialization; removed orphan records before loading clean 3NF database. | **RESOLVED** |
| **DEF-05** | **Order vs Shipping Status Conflict**<br>Orders marked as `Cancelled` but listed as `Delivered On-Time` in shipping. | Cross-table status mismatch query (`WHERE o.order_status = 'Cancelled' AND s.delivery_status = 'Delivered On-Time'`) | Creates severe reporting contradictions between financial metrics and logistics SLAs. | Aligned `delivery_status` to `'Cancelled/Failed'` for all cancelled orders in `src/db_setup.py`. | **RESOLVED** |

---

## Remediation Verification Summary

* **Raw Records Inspected**: 6,494 Orders, 12,500 Raw Order Items, 6,494 Shipping Records, 6,494 Payments.
* **Remediated Records**: 689 duplicate/invalid order items removed; 100% of orphan foreign keys resolved.
* **Post-Remediation Integrity**: Zero referential integrity breaks, zero chronological violations, 100% status alignment in the production relational database (`data/retail_intelligence.db`).
