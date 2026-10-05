"""
Summary Marts Data Exporter
Target: Retail Revenue & Customer Intelligence Platform

Generates clean analytical data mart artifacts for downstream Power BI reporting:
- product_summary.csv
- monthly_revenue_summary.csv
"""

import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def export_summary_marts():
    print("[INFO] Exporting Summary Mart Artifacts for Power BI...")
    conn = sqlite3.connect(DB_PATH)

    # 1. Product Summary Mart
    q_product = """
    SELECT 
        p.product_id,
        p.product_name,
        cat.category_name,
        cat.department,
        p.cost_price,
        p.unit_price,
        p.stock_quantity,
        COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
        COALESCE(SUM(oi.item_total), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.item_total) - SUM(p.cost_price * oi.quantity), 0.0) AS gross_profit,
        ROUND(
            (COALESCE(SUM(oi.item_total) - SUM(p.cost_price * oi.quantity), 0.0) / NULLIF(SUM(oi.item_total), 0)) * 100, 
            2
        ) AS profit_margin_pct
    FROM products p
    JOIN categories cat ON p.category_id = cat.category_id
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_status IN ('Completed', 'Shipped')
    GROUP BY p.product_id, p.product_name, cat.category_name, cat.department, p.cost_price, p.unit_price, p.stock_quantity
    ORDER BY gross_revenue DESC
    """
    df_product = pd.read_sql_query(q_product, conn)
    df_product.to_csv(os.path.join(PROCESSED_DIR, "product_summary.csv"), index=False)
    print(f" [SUCCESS] Exported product_summary.csv ({len(df_product)} rows)")

    # 2. Monthly Revenue Summary Mart
    q_monthly = """
    SELECT 
        DATE_FORMAT(order_date, '%Y-%m') AS month_year,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS active_customers,
        ROUND(SUM(total_amount), 2) AS net_revenue,
        ROUND(SUM(shipping_cost), 2) AS total_shipping_revenue,
        ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS monthly_aov
    FROM orders
    WHERE order_status IN ('Completed', 'Shipped')
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
    ORDER BY month_year ASC
    """
    # Use custom MySQL helper registration if executing raw SQL string on SQLite
    conn.create_function("DATE_FORMAT", 2, lambda dt, fmt: dt[:7] if dt else None)
    df_monthly = pd.read_sql_query(q_monthly, conn)
    df_monthly.to_csv(os.path.join(PROCESSED_DIR, "monthly_revenue_summary.csv"), index=False)
    print(f" [SUCCESS] Exported monthly_revenue_summary.csv ({len(df_monthly)} rows)")

    conn.close()

if __name__ == "__main__":
    export_summary_marts()
