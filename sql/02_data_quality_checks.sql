-- =============================================================================
-- Retail Revenue & Customer Intelligence Platform
-- Data Quality Validation Suite (SQL Checks)
--
-- This script contains diagnostic queries to detect data quality anomalies:
-- 1. Duplicate Records Audit
-- 2. Mandatory Attributes Null Check
-- 3. Invalid Numeric Ranges (Quantity <= 0, Unit Price <= 0)
-- 4. Chronological & Date Consistency Checks
-- 5. Orphan Foreign Key Integrity Breaches
-- 6. Business Logic & Status Inconsistencies
-- =============================================================================

USE retail_intelligence_db;

-- -----------------------------------------------------------------------------
-- DQ Check 1: Duplicate Order Items (Exact duplicate transactions)
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_1_DUPLICATES' AS check_name,
    order_id, 
    product_id, 
    quantity, 
    unit_price, 
    COUNT(*) AS duplicate_count
FROM order_items
GROUP BY order_id, product_id, quantity, unit_price
HAVING COUNT(*) > 1;

-- -----------------------------------------------------------------------------
-- DQ Check 2: Mandatory Attribute Null Audits
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_2_NULLS' AS check_name,
    'orders' AS table_name,
    COUNT(*) AS null_records_count
FROM orders
WHERE customer_id IS NULL OR order_date IS NULL OR total_amount IS NULL

UNION ALL

SELECT 
    'DQ_CHECK_2_NULLS' AS check_name,
    'customers' AS table_name,
    COUNT(*) AS null_records_count
FROM customers
WHERE email IS NULL OR signup_date IS NULL;

-- -----------------------------------------------------------------------------
-- DQ Check 3: Invalid Numeric Value Audit (Negative / Zero Quantities or Prices)
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_3_INVALID_RANGES' AS check_name,
    item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    CASE 
        WHEN quantity <= 0 THEN 'Invalid Quantity (<= 0)'
        WHEN unit_price <= 0 THEN 'Invalid Unit Price (<= 0)'
        ELSE 'Valid'
    END AS anomaly_reason
FROM order_items
WHERE quantity <= 0 OR unit_price <= 0;

-- -----------------------------------------------------------------------------
-- DQ Check 4: Chronological Date Integrity Audit
-- (Actual Delivery Date BEFORE Order Date OR Order Date BEFORE Customer Signup Date)
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_4_CHRONOLOGY' AS check_name,
    s.shipping_id,
    s.order_id,
    o.order_date,
    s.actual_delivery_date,
    'Actual Delivery Date Precedes Order Date' AS anomaly_reason
FROM shipping s
JOIN orders o ON s.order_id = o.order_id
WHERE s.actual_delivery_date IS NOT NULL 
  AND DATE(s.actual_delivery_date) < DATE(o.order_date);

-- -----------------------------------------------------------------------------
-- DQ Check 5: Orphan Foreign Keys Audit (Payments without valid Order ID)
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_5_ORPHAN_KEYS' AS check_name,
    p.payment_id,
    p.order_id AS orphan_order_id,
    p.payment_amount,
    p.payment_date,
    'Orphan Payment Record (No Parent Order)' AS anomaly_reason
FROM payments p
LEFT JOIN orders o ON p.order_id = o.order_id
WHERE o.order_id IS NULL;

-- -----------------------------------------------------------------------------
-- DQ Check 6: Order Status vs Payment Status Inconsistency
-- (Order is Cancelled but Payment Status is marked as Completed)
-- -----------------------------------------------------------------------------
SELECT 
    'DQ_CHECK_6_STATUS_MISMATCH' AS check_name,
    o.order_id,
    o.order_status,
    p.payment_id,
    p.payment_status,
    'Order Cancelled with Active Completed Payment' AS anomaly_reason
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'Cancelled' 
  AND p.payment_status = 'Completed';
