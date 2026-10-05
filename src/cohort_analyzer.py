"""
Cohort Retention & Customer LTV Analytics Engine
Target: Retail Revenue & Customer Intelligence Platform

DATA TRANSPARENCY NOTICE:
All cohort matrices, retention percentages, and LTV curves are computed from 
100% SYNTHETIC retail transaction records generated for portfolio demonstration.

METHODOLOGY & FORMULATION:
--------------------------------------------------------------------------------
1. Acquisition Cohort: Defined by the month of a customer's first valid completed purchase (e.g. '2024-01').
2. Cohort Index: The integer month offset elapsed between order month and acquisition month:
   Cohort_Index = (Order_Year - First_Year) * 12 + (Order_Month - First_Month)
3. Retention Rate (%):
   Retention_Rate_M_i = (Unique Active Customers in Month_i / Initial Cohort Customer Count) * 100
4. Cumulative Cohort Revenue (LTV Curve):
   Cumulative_Revenue_M_i = Sum of all net order revenue from Cohort up to Month_i
5. Average Cumulative Revenue Per Customer (Historical LTV Metric):
   Historical_LTV_M_i = Cumulative_Revenue_M_i / Initial Cohort Customer Count
   NOTE: This represents the empirical historical LTV realization curve, NOT a predictive ML projection.
--------------------------------------------------------------------------------
"""

import os
import sqlite3
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

def compute_cohort_analytics():
    print("[INFO] Initializing Cohort Retention & LTV Analytics Engine...")
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT 
        o.customer_id,
        o.order_id,
        o.order_date,
        o.total_amount
    FROM orders o
    WHERE o.order_status IN ('Completed', 'Shipped')
    """
    
    df_orders = pd.read_sql_query(query, conn)
    conn.close()

    df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
    df_orders["order_month"] = df_orders["order_date"].dt.to_period("M")

    # 1. Identify First Purchase Month per Customer (Acquisition Cohort)
    df_orders["cohort_month"] = df_orders.groupby("customer_id")["order_month"].transform("min")

    # 2. Compute Cohort Index (Months Elapsed)
    def calculate_cohort_index(df):
        order_year = df["order_month"].dt.year
        order_month = df["order_month"].dt.month
        cohort_year = df["cohort_month"].dt.year
        cohort_month = df["cohort_month"].dt.month
        
        return (order_year - cohort_year) * 12 + (order_month - cohort_month)

    df_orders["cohort_index"] = calculate_cohort_index(df_orders)

    # 3. Build Retention Matrix (Count of Unique Customers)
    cohort_data = df_orders.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().reset_index()
    
    # Pivot into Cohort Retention Matrix
    retention_matrix = cohort_data.pivot(index="cohort_month", columns="cohort_index", values="customer_id")
    
    # Initial Cohort Sizes (Month 0 active count)
    cohort_sizes = retention_matrix.iloc[:, 0]

    # Retention Percentage Matrix
    retention_pct_matrix = retention_matrix.divide(cohort_sizes, axis=0) * 100.0
    retention_pct_matrix = retention_pct_matrix.round(2)

    # 4. Build Cumulative Revenue & LTV Matrix
    revenue_cohort_data = df_orders.groupby(["cohort_month", "cohort_index"])["total_amount"].sum().reset_index()
    revenue_matrix = revenue_cohort_data.pivot(index="cohort_month", columns="cohort_index", values="total_amount").fillna(0)
    
    # Cumulative Revenue across Cohort Index
    cumulative_revenue_matrix = revenue_matrix.cumsum(axis=1)

    # Historical LTV per Customer Matrix (Cumulative Revenue / Cohort Size)
    ltv_matrix = cumulative_revenue_matrix.divide(cohort_sizes, axis=0).round(2)

    # 5. Export Cohort Artifacts
    # Convert PeriodIndex to String for CSV export
    retention_pct_export = retention_pct_matrix.copy()
    retention_pct_export.index = retention_pct_export.index.astype(str)
    retention_export_path = os.path.join(PROCESSED_DIR, "cohort_retention.csv")
    retention_pct_export.to_csv(retention_export_path)
    print(f"[SUCCESS] Exported Cohort Retention Matrix: {retention_export_path}")

    ltv_export = ltv_matrix.copy()
    ltv_export.index = ltv_export.index.astype(str)
    ltv_export_path = os.path.join(PROCESSED_DIR, "cohort_ltv.csv")
    ltv_export.to_csv(ltv_export_path)
    print(f"[SUCCESS] Exported Cohort LTV Matrix: {ltv_export_path}")

    # Print Summary Matrix Check
    print("\n==================================================")
    print("        COHORT RETENTION & LTV AUDIT SUMMARY      ")
    print("==================================================")
    print(f" Total Acquisition Cohorts Tracked : {len(cohort_sizes)}")
    print(f" Average Cohort Size             : {cohort_sizes.mean():.1f} customers")
    print(f" Average Month 1 Retention Rate  : {retention_pct_matrix[1].mean():.2f}%")
    print(f" Average Month 6 Retention Rate  : {retention_pct_matrix[6].mean():.2f}%")
    print(f" Average Month 12 Cumulative LTV : ${ltv_matrix[12].mean():.2f} per customer")
    print("==================================================\n")

    return retention_pct_matrix, ltv_matrix, cohort_sizes

if __name__ == "__main__":
    compute_cohort_analytics()
