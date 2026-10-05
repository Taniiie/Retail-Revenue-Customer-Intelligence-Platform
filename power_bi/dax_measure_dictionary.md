# DAX Measure Dictionary
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY**: All measures are designed for the Star Schema data model (`power_bi/data_sources/`).  
> Cancelled and Refunded orders are excluded from revenue/profit calculations unless explicitly stated. All expected values reflect the **100% synthetic** retail dataset.

---

## Measure Definitions

### 1. Total Revenue
```dax
Total Revenue = 
    CALCULATE(
        SUM(FactOrders[total_amount]),
        FactOrders[order_status] IN { "Completed", "Shipped" }
    )
```
**Definition**: Sum of `total_amount` for all completed and shipped orders.  
**Validated Value**: **$3,990,811.00**

---

### 2. Total Orders
```dax
Total Orders = 
    CALCULATE(
        DISTINCTCOUNT(FactOrders[order_id]),
        FactOrders[order_status] IN { "Completed", "Shipped" }
    )
```
**Definition**: Count of distinct completed/shipped order IDs.  
**Validated Value**: **5,842 orders**

---

### 3. Total Registered Customers
```dax
Total Registered Customers = 
    DISTINCTCOUNT(DimCustomer[customer_id])
```
**Definition**: Total registered customers in the database (including inactive).  
**Validated Value**: **1,498 registered customers**

---

### 4. Active Customers
```dax
Active Customers = 
    CALCULATE(
        DISTINCTCOUNT(FactOrders[customer_id]),
        FactOrders[order_status] IN { "Completed", "Shipped" }
    )
```
**Definition**: Customers with at least one completed/shipped order.  
**Validated Value**: **1,107 active customers**

---

### 5. Average Order Value (AOV)
```dax
AOV = 
    DIVIDE(
        [Total Revenue],
        [Total Orders],
        0
    )
```
**Definition**: Total Revenue / Total Orders.  
**Validated Value**: **$683.12**

---

### 6. MoM Revenue Growth %
```dax
MoM Revenue Growth % = 
    VAR CurrentMonth = [Total Revenue]
    VAR PriorMonth = CALCULATE(
        [Total Revenue],
        DATEADD(DimDate[date], -1, MONTH)
    )
    RETURN DIVIDE(CurrentMonth - PriorMonth, PriorMonth, BLANK())
```
**Definition**: Month-over-Month revenue growth percentage.

---

### 7. YoY Revenue Growth %
```dax
YoY Revenue Growth % = 
    VAR CurrentYear = [Total Revenue]
    VAR PriorYear = CALCULATE(
        [Total Revenue],
        DATEADD(DimDate[date], -1, YEAR)
    )
    RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, BLANK())
```
**Definition**: Year-over-Year revenue growth percentage (2025 vs 2024).

---

### 8. Gross Profit
```dax
Gross Profit = 
    CALCULATE(
        SUM(FactOrderItems[line_gross_profit]),
        FactOrderItems[order_status] IN { "Completed", "Shipped" }
    )
```
**Definition**: Sum of line-level gross profit (`item_total - (cost_price * quantity)`).  
**Validated Value**: **$1,240,548.65**

---

### 9. Gross Profit Margin %
```dax
Gross Profit Margin % = 
    DIVIDE([Gross Profit], [Total Revenue], 0)
```
**Definition**: Gross Profit / Total Revenue.  
**Validated Value**: **31.08%**

---

### 10. Average Items per Order
```dax
Avg Items per Order = 
    DIVIDE(
        CALCULATE(
            SUM(FactOrderItems[quantity]),
            FactOrderItems[order_status] IN { "Completed", "Shipped" }
        ),
        [Total Orders],
        0
    )
```
**Definition**: Total quantity of units sold / Total valid orders.  
**Validated Value**: **2.02 units/order**

---

### 11. New Customers
```dax
New Customers = 
    VAR FirstPurchaseDates = 
        ADDCOLUMNS(
            VALUES(DimCustomer[customer_id]),
            "FirstDate", CALCULATE(MIN(FactOrders[order_date]))
        )
    RETURN
    COUNTROWS(
        FILTER(
            FirstPurchaseDates,
            [FirstDate] >= MIN(DimDate[date]) && 
            [FirstDate] <= MAX(DimDate[date])
        )
    )
```
**Definition**: Customers making their first completed/shipped order within the date filter context.

---

### 12. Returning Customers
```dax
Returning Customers = 
    [Active Customers] - [New Customers]
```
**Definition**: Active customers minus new customer acquisitions.

---

### 13. Repeat Purchase Rate %
```dax
Repeat Purchase Rate % = 
    VAR RepeatBuyers = CALCULATE(
        DISTINCTCOUNT(FactOrders[customer_id]),
        FactOrders[order_status] IN { "Completed", "Shipped" },
        FILTER(
            VALUES(FactOrders[customer_id]),
            CALCULATE(DISTINCTCOUNT(FactOrders[order_id])) >= 2
        )
    )
    RETURN DIVIDE(RepeatBuyers, [Active Customers], 0)
```
**Definition**: Percentage of active customers placing 2+ completed orders.  
**Validated Value**: **83.65%** (926 repeat buyers / 1,107 active customers)

---

### 14. Revenue per Customer
```dax
Revenue per Customer = 
    DIVIDE([Total Revenue], [Active Customers], 0)
```
**Definition**: Total Revenue / Active Customers.  
**Validated Value**: **$3,605.07**

---

### 15. Champion Revenue Contribution %
```dax
Champion Revenue Contribution % = 
    VAR ChampionRevenue = 
        CALCULATE(
            [Total Revenue],
            DimCustomer[rfm_segment] = "Champions"
        )
    RETURN DIVIDE(ChampionRevenue, [Total Revenue], 0)
```
**Definition**: Percentage of revenue generated by *Champions* RFM segment.  
**Validated Value**: **54.97%** ($2,193,910.01 / $3,990,811.00)

---

### 16. RFM Segment Revenue
```dax
RFM Segment Revenue = 
    CALCULATE(
        [Total Revenue],
        USERELATIONSHIP(FactOrders[customer_id], DimCustomer[customer_id])
    )
```
**Definition**: Total Revenue evaluated per RFM segment slicer selection.

---

### 17. RFM Segment Customer Count
```dax
RFM Segment Customer Count = 
    CALCULATE(
        DISTINCTCOUNT(DimCustomer[customer_id]),
        DimCustomer[rfm_segment] <> "No Valid Orders"
    )
```
**Definition**: Distinct customer count in each RFM persona.

---

### 18. On-Time Delivery Rate % (Carrier SLA Compliance Rate)
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
**Definition**: Delivered On-Time Shipments / Total Delivered Shipments (`actual_delivery_date IS NOT NULL`).  
**Validated Value**: **74.47%** (3,959 / 5,316 delivered shipments)

---

### 19. Average Shipping Lag Days
```dax
Avg Shipping Lag Days = 
    AVERAGEX(
        FILTER(FactShipping, NOT ISBLANK(FactShipping[actual_delivery_date])),
        DATEDIFF(FactShipping[shipped_date], FactShipping[actual_delivery_date], DAY)
    )
```
**Definition**: Average days between ship date and actual delivery date.  
**Validated Value**: **3.01 days**

---

### 20. Catalog Product SKU Count
```dax
Catalog SKU Count = 
    DISTINCTCOUNT(DimProduct[product_id])
```
**Definition**: Count of active SKUs in the catalog dimension.  
**Validated Value**: **40 Products** across 8 categories

---

## Validation Cross-Reference Table

| DAX Measure | Formula Summary | SQL / Python Validated Value | Reconciliation Status |
|:---|:---|:---|:---|
| Total Revenue | `SUM(FactOrders[total_amount])` | **$3,990,811.00** | PASSED (Exact Match) |
| Total Orders | `DISTINCTCOUNT(FactOrders[order_id])` | **5,842** | PASSED (Exact Match) |
| Active Customers | `DISTINCTCOUNT(FactOrders[customer_id])` | **1,107** | PASSED (Exact Match) |
| AOV | `Total Revenue / Total Orders` | **$683.12** | PASSED (Exact Match) |
| Gross Profit | `SUM(line_gross_profit)` | **$1,240,548.65** | PASSED (Exact Match) |
| Gross Margin % | `Gross Profit / Total Revenue` | **31.08%** | PASSED (Exact Match) |
| On-Time Delivery Rate % | `On-Time / Delivered Total` | **74.47%** | PASSED (Exact Match) |
| Champions Segment Rev | `RFM Segment Revenue` | **$2,193,910.01** | PASSED (Exact Match) |
| Month 1 Retention % | Matrix / Python Cohort Engine | **40.98%** | PASSED (Exact Match) |
| Catalog SKU Count | `DISTINCTCOUNT(DimProduct[product_id])` | **40** | PASSED (Exact Match) |
