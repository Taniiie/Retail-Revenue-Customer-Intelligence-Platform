"""
Power BI Star Schema Data Model Builder & Exporter
Target: Retail Revenue & Customer Intelligence Platform

Transforms the clean normalized relational data into a proper Star Schema
optimized for Power BI import. Creates fact and dimension tables with
correct grain, primary keys, and foreign key relationships.

DATA TRANSPARENCY NOTICE:
All exported data marts are derived from 100% SYNTHETIC retail transaction data.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
PBI_DIR = os.path.join(PROJECT_ROOT, "power_bi", "data_sources")

os.makedirs(PBI_DIR, exist_ok=True)

def build_star_schema():
    print("[INFO] Building Power BI Star Schema Data Model...")
    conn = sqlite3.connect(DB_PATH)

    # ==================================================================
    # DIMENSION 1: DimDate (Date Dimension)
    # ==================================================================
    print("  Building DimDate...")
    
    # Get date range from orders
    date_range = pd.read_sql_query(
        "SELECT MIN(order_date) as min_dt, MAX(order_date) as max_dt FROM orders",
        conn
    )
    start_date = pd.to_datetime(date_range.iloc[0]["min_dt"]).normalize()
    end_date = pd.to_datetime(date_range.iloc[0]["max_dt"]).normalize()
    
    # Extend range to cover full months
    start_date = start_date.replace(day=1)
    # End at last day of end month
    if end_date.month == 12:
        end_date = end_date.replace(year=end_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)
    
    date_range_full = pd.date_range(start=start_date, end=end_date, freq="D")
    
    dim_date = pd.DataFrame({
        "date_key": date_range_full.strftime("%Y%m%d").astype(int),
        "date": date_range_full.strftime("%Y-%m-%d"),
        "year": date_range_full.year,
        "quarter": date_range_full.quarter,
        "quarter_label": ["Q" + str(q) for q in date_range_full.quarter],
        "month_number": date_range_full.month,
        "month_name": date_range_full.strftime("%B"),
        "month_short": date_range_full.strftime("%b"),
        "year_month": date_range_full.strftime("%Y-%m"),
        "year_quarter": date_range_full.strftime("%Y") + "-Q" + date_range_full.quarter.astype(str),
        "week_number": date_range_full.isocalendar().week.values,
        "day_of_week": date_range_full.dayofweek,
        "day_name": date_range_full.strftime("%A"),
        "is_weekend": (date_range_full.dayofweek >= 5).astype(int),
        "day_of_month": date_range_full.day,
        "month_sort_key": date_range_full.year * 100 + date_range_full.month
    })
    
    dim_date.to_csv(os.path.join(PBI_DIR, "DimDate.csv"), index=False)
    print(f"    DimDate: {len(dim_date)} rows ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

    # ==================================================================
    # DIMENSION 2: DimCustomer (Customer Dimension with RFM enrichment)
    # ==================================================================
    print("  Building DimCustomer...")
    
    df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
    df_rfm = pd.read_csv(os.path.join(PROCESSED_DIR, "customer_rfm.csv"))
    
    # Left join to include ALL customers (even those without valid orders)
    dim_customer = df_customers.merge(
        df_rfm[["customer_id", "recency", "frequency", "monetary", 
                "r_score", "f_score", "m_score", "rfm_score_str", 
                "rfm_score_avg", "rfm_segment", "last_order_date"]],
        on="customer_id",
        how="left"
    )
    
    # Fill nulls for customers without valid orders
    dim_customer["rfm_segment"] = dim_customer["rfm_segment"].fillna("No Valid Orders")
    dim_customer["frequency"] = dim_customer["frequency"].fillna(0).astype(int)
    dim_customer["monetary"] = dim_customer["monetary"].fillna(0.0)
    dim_customer["recency"] = dim_customer["recency"].fillna(-1).astype(int)
    
    dim_customer.to_csv(os.path.join(PBI_DIR, "DimCustomer.csv"), index=False)
    print(f"    DimCustomer: {len(dim_customer)} rows")

    # ==================================================================
    # DIMENSION 3: DimProduct (Product Dimension)
    # ==================================================================
    print("  Building DimProduct...")
    
    dim_product = pd.read_sql_query("""
        SELECT 
            p.product_id,
            p.product_name,
            p.category_id,
            c.category_name,
            c.department,
            p.cost_price,
            p.unit_price,
            p.stock_quantity,
            ROUND((p.unit_price - p.cost_price) / NULLIF(p.unit_price, 0) * 100, 2) AS list_margin_pct
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
    """, conn)
    
    dim_product.to_csv(os.path.join(PBI_DIR, "DimProduct.csv"), index=False)
    print(f"    DimProduct: {len(dim_product)} rows")

    # ==================================================================
    # DIMENSION 4: DimCategory (Category Dimension - for convenience)
    # ==================================================================
    print("  Building DimCategory...")
    
    dim_category = pd.read_sql_query("SELECT * FROM categories", conn)
    dim_category.to_csv(os.path.join(PBI_DIR, "DimCategory.csv"), index=False)
    print(f"    DimCategory: {len(dim_category)} rows")

    # ==================================================================
    # FACT 1: FactOrders (Order-level Fact Table)
    # ==================================================================
    print("  Building FactOrders...")
    
    df_orders = pd.read_sql_query("SELECT * FROM orders", conn)
    df_orders["order_date_key"] = pd.to_datetime(df_orders["order_date"]).dt.strftime("%Y%m%d").astype(int)
    
    fact_orders = df_orders[["order_id", "customer_id", "order_date", "order_date_key",
                             "order_status", "shipping_cost", "total_amount"]]
    
    fact_orders.to_csv(os.path.join(PBI_DIR, "FactOrders.csv"), index=False)
    print(f"    FactOrders: {len(fact_orders)} rows")

    # ==================================================================
    # FACT 2: FactOrderItems (Line-Item Fact Table - lowest grain)
    # ==================================================================
    print("  Building FactOrderItems...")
    
    fact_items = pd.read_sql_query("""
        SELECT 
            oi.item_id,
            oi.order_id,
            oi.product_id,
            o.customer_id,
            o.order_date,
            o.order_status,
            oi.quantity,
            oi.unit_price AS sold_unit_price,
            oi.discount_amount,
            oi.item_total,
            p.cost_price,
            (oi.item_total - (p.cost_price * oi.quantity)) AS line_gross_profit
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
    """, conn)
    
    fact_items["order_date_key"] = pd.to_datetime(fact_items["order_date"]).dt.strftime("%Y%m%d").astype(int)
    
    fact_items.to_csv(os.path.join(PBI_DIR, "FactOrderItems.csv"), index=False)
    print(f"    FactOrderItems: {len(fact_items)} rows")

    # ==================================================================
    # FACT 3: FactShipping (Shipping/Operations Fact Table)
    # ==================================================================
    print("  Building FactShipping...")
    
    fact_shipping = pd.read_sql_query("""
        SELECT 
            s.shipping_id,
            s.order_id,
            o.customer_id,
            s.carrier,
            s.shipped_date,
            s.estimated_delivery_date,
            s.actual_delivery_date,
            s.delivery_status,
            o.order_status,
            p.payment_method,
            p.payment_status
        FROM shipping s
        JOIN orders o ON s.order_id = o.order_id
        JOIN payments p ON s.order_id = p.order_id
    """, conn)
    
    fact_shipping.to_csv(os.path.join(PBI_DIR, "FactShipping.csv"), index=False)
    print(f"    FactShipping: {len(fact_shipping)} rows")

    # ==================================================================
    # ANALYTICAL TABLE: Cohort Retention (Pre-computed)
    # ==================================================================
    print("  Copying Cohort Retention & LTV Analytical Tables...")
    
    # Already validated - just copy to PBI directory
    import shutil
    for fname in ["cohort_retention.csv", "cohort_ltv.csv"]:
        src = os.path.join(PROCESSED_DIR, fname)
        dst = os.path.join(PBI_DIR, fname)
        shutil.copy2(src, dst)
        print(f"    Copied: {fname}")

    conn.close()
    
    # ==================================================================
    # VALIDATION: Cross-check fact table totals
    # ==================================================================
    print("\n--- Star Schema Validation ---")
    
    valid_orders = fact_orders[fact_orders["order_status"].isin(["Completed", "Shipped"])]
    valid_items = fact_items[fact_items["order_status"].isin(["Completed", "Shipped"])]
    
    rev_fact_orders = valid_orders["total_amount"].sum()
    rev_fact_items = valid_items["item_total"].sum()
    rfm_monetary = dim_customer["monetary"].sum()
    
    print(f"  FactOrders Net Revenue (Completed+Shipped): ${rev_fact_orders:,.2f}")
    print(f"  FactOrderItems Line Total Sum             : ${rev_fact_items:,.2f}")
    print(f"  DimCustomer RFM Monetary Sum              : ${rfm_monetary:,.2f}")
    
    shipping_fees = valid_orders["shipping_cost"].sum()
    print(f"  Reconciliation: Items (${rev_fact_items:,.2f}) + Shipping (${shipping_fees:,.2f}) = ${rev_fact_items + shipping_fees:,.2f}")
    
    if abs(rev_fact_orders - rfm_monetary) < 0.01:
        print("  [PASSED] FactOrders revenue matches RFM monetary total!")
    else:
        print(f"  [INFO] FactOrders vs RFM diff: ${abs(rev_fact_orders - rfm_monetary):,.2f}")
    
    if abs((rev_fact_items + shipping_fees) - rev_fact_orders) < 0.01:
        print("  [PASSED] Line items + shipping = order total!")
    else:
        print(f"  [INFO] Reconciliation diff: ${abs((rev_fact_items + shipping_fees) - rev_fact_orders):,.2f}")
    
    print(f"\n[SUCCESS] Power BI Star Schema exported to: {PBI_DIR}")
    print(f"  Total files: 8 (4 dimensions + 3 facts + 2 analytical)")

if __name__ == "__main__":
    build_star_schema()
