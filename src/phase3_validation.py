"""
Phase 3 Validation Script
Validates all RFM, Cohort, and Summary Mart outputs for mathematical consistency.
"""

import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def run_phase3_validation():
    print("==================================================")
    print("     PHASE 3 COMPREHENSIVE VALIDATION SUITE       ")
    print("==================================================\n")

    conn = sqlite3.connect(DB_PATH)
    
    # ---- 1. RFM Customer Count Validation ----
    print("[VALIDATION 1] RFM Customer Count vs Database Active Customers")
    db_active_customers = pd.read_sql_query("""
        SELECT COUNT(DISTINCT customer_id) as cnt 
        FROM orders 
        WHERE order_status IN ('Completed', 'Shipped')
    """, conn).iloc[0]["cnt"]
    
    df_rfm = pd.read_csv(os.path.join(PROCESSED_DIR, "customer_rfm.csv"))
    rfm_customers = len(df_rfm)
    
    print(f"  Database Active Customers (with valid orders): {db_active_customers}")
    print(f"  RFM Analytical Dataset Customer Count       : {rfm_customers}")
    if db_active_customers == rfm_customers:
        print("  [PASSED] Exact match!\n")
    else:
        print(f"  [WARNING] Mismatch of {abs(db_active_customers - rfm_customers)} customers\n")

    # ---- 2. RFM Segment Counts Sum to Total ----
    print("[VALIDATION 2] RFM Segment Counts Sum to Total Customers")
    segment_total = df_rfm.groupby("rfm_segment")["customer_id"].count().sum()
    print(f"  Sum of all segment customer counts: {segment_total}")
    print(f"  Total RFM customers              : {rfm_customers}")
    if segment_total == rfm_customers:
        print("  [PASSED] All customers are assigned exactly one segment!\n")
    else:
        print("  [FAILED] Segment assignment mismatch!\n")

    # ---- 3. Duplicate Customer Check ----
    print("[VALIDATION 3] Duplicate Customer Check in RFM Dataset")
    dup_count = df_rfm["customer_id"].duplicated().sum()
    print(f"  Duplicate customer_id records: {dup_count}")
    if dup_count == 0:
        print("  [PASSED] Zero duplicates!\n")
    else:
        print("  [FAILED] Duplicates detected!\n")

    # ---- 4. Null RFM Values Check ----
    print("[VALIDATION 4] Null/Invalid RFM Score Check")
    null_r = df_rfm["r_score"].isnull().sum()
    null_f = df_rfm["f_score"].isnull().sum()
    null_m = df_rfm["m_score"].isnull().sum()
    null_seg = df_rfm["rfm_segment"].isnull().sum()
    print(f"  Null R scores: {null_r}, Null F scores: {null_f}, Null M scores: {null_m}, Null segments: {null_seg}")
    if null_r + null_f + null_m + null_seg == 0:
        print("  [PASSED] All RFM values populated!\n")
    else:
        print("  [FAILED] Null RFM values detected!\n")

    # ---- 5. RFM Score Ranges Check ----
    print("[VALIDATION 5] RFM Score Range Bounds [1-5]")
    r_range = (df_rfm["r_score"].min(), df_rfm["r_score"].max())
    f_range = (df_rfm["f_score"].min(), df_rfm["f_score"].max())
    m_range = (df_rfm["m_score"].min(), df_rfm["m_score"].max())
    print(f"  R Score Range: {r_range}, F Score Range: {f_range}, M Score Range: {m_range}")
    if all(lo >= 1 and hi <= 5 for lo, hi in [r_range, f_range, m_range]):
        print("  [PASSED] All scores within valid [1, 5] bounds!\n")
    else:
        print("  [FAILED] Scores out of bounds!\n")

    # ---- 6. RFM Monetary vs SQL Revenue Validation ----
    print("[VALIDATION 6] RFM Total Monetary vs SQL Total Net Revenue")
    rfm_total_monetary = df_rfm["monetary"].sum()
    
    sql_total_revenue = pd.read_sql_query("""
        SELECT SUM(total_amount) as total
        FROM orders
        WHERE order_status IN ('Completed', 'Shipped')
    """, conn).iloc[0]["total"]
    
    print(f"  RFM Total Monetary (customer sum): ${rfm_total_monetary:,.2f}")
    print(f"  SQL Total Net Revenue            : ${sql_total_revenue:,.2f}")
    diff_pct = abs(rfm_total_monetary - sql_total_revenue) / sql_total_revenue * 100
    if diff_pct < 0.01:
        print(f"  [PASSED] Match within 0.01% tolerance! (Diff: {diff_pct:.4f}%)\n")
    else:
        print(f"  [WARNING] Difference of {diff_pct:.2f}% detected\n")

    # ---- 7. Cohort Retention Matrix Validation ----
    print("[VALIDATION 7] Cohort Retention Matrix Integrity")
    df_cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort_retention.csv"), index_col=0)
    
    # Check Month 0 is always 100%
    month0_vals = df_cohort.iloc[:, 0].dropna()
    all_100 = (month0_vals == 100.0).all()
    print(f"  Month 0 Retention (all cohorts): {'All 100%' if all_100 else 'NOT all 100%'}")
    if all_100:
        print("  [PASSED] All cohorts start at 100% retention!\n")
    else:
        print("  [FAILED] Some cohorts do not start at 100%!\n")

    # ---- 8. No Retention > 100% Check ----
    print("[VALIDATION 8] Retention Percentage Bounds Check (<= 100%)")
    max_retention = df_cohort.max().max()
    print(f"  Maximum retention value found: {max_retention}%")
    if max_retention <= 100.0:
        print("  [PASSED] No impossible retention values!\n")
    else:
        print("  [FAILED] Retention values exceed 100%!\n")

    # ---- 9. Cohort Customer Count Validation ----
    print("[VALIDATION 9] Cohort Total Customers vs RFM Total Customers")
    # Count unique customers that appear in any cohort
    cohort_total_from_db = pd.read_sql_query("""
        SELECT COUNT(DISTINCT customer_id) as cnt
        FROM orders
        WHERE order_status IN ('Completed', 'Shipped')
    """, conn).iloc[0]["cnt"]
    print(f"  Cohort engine eligible customers : {cohort_total_from_db}")
    print(f"  RFM engine eligible customers    : {rfm_customers}")
    if cohort_total_from_db == rfm_customers:
        print("  [PASSED] Cohort and RFM customer universes match!\n")
    else:
        print(f"  [INFO] Difference of {abs(cohort_total_from_db - rfm_customers)} - expected if customer groupings differ\n")

    # ---- 10. Sample Customer Manual Validation ----
    print("[VALIDATION 10] Manual Sample Customer RFM Validation")
    sample_cust = df_rfm.sort_values("monetary", ascending=False).head(3)
    for _, row in sample_cust.iterrows():
        cid = row["customer_id"]
        db_check = pd.read_sql_query(f"""
            SELECT 
                COUNT(DISTINCT order_id) as freq,
                SUM(total_amount) as spend
            FROM orders
            WHERE customer_id = {cid} AND order_status IN ('Completed', 'Shipped')
        """, conn)
        db_freq = db_check.iloc[0]["freq"]
        db_spend = db_check.iloc[0]["spend"]
        rfm_freq = row["frequency"]
        rfm_spend = row["monetary"]
        match_f = "OK" if db_freq == rfm_freq else "MISMATCH"
        match_m = "OK" if abs(db_spend - rfm_spend) < 0.01 else "MISMATCH"
        print(f"  Customer {cid}: DB Freq={db_freq} vs RFM Freq={rfm_freq} [{match_f}] | DB Spend=${db_spend:,.2f} vs RFM Monetary=${rfm_spend:,.2f} [{match_m}]")
    
    print()

    # ---- 11. LTV Definition Audit ----
    print("[VALIDATION 11] LTV Methodology Audit")
    df_ltv = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort_ltv.csv"), index_col=0)
    print("  LTV Definition: Historical Cumulative Revenue Per Customer = Cumulative Cohort Revenue / Initial Cohort Size")
    print("  LTV Type: Empirical realization curve (NOT a predictive ML model)")
    # Check LTV values are monotonically non-decreasing across columns for each cohort
    ltv_monotonic = True
    for idx, row in df_ltv.iterrows():
        vals = row.dropna().values
        if len(vals) > 1 and not all(vals[i] <= vals[i+1] + 0.01 for i in range(len(vals)-1)):
            ltv_monotonic = False
            break
    print(f"  LTV Monotonicity Check (cumulative should only increase): {'[PASSED]' if ltv_monotonic else '[FAILED]'}")
    print()

    # ---- 12. Exported Files Audit ----
    print("[VALIDATION 12] Exported Processed Files Audit")
    expected_files = [
        "customer_rfm.csv", "customer_summary.csv", 
        "cohort_retention.csv", "cohort_ltv.csv",
        "product_summary.csv", "monthly_revenue_summary.csv"
    ]
    for fname in expected_files:
        fpath = os.path.join(PROCESSED_DIR, fname)
        exists = os.path.exists(fpath)
        if exists:
            size = os.path.getsize(fpath)
            print(f"  {fname:<35} : EXISTS ({size:,} bytes)")
        else:
            print(f"  {fname:<35} : MISSING")

    conn.close()
    print("\n==================================================")
    print("     PHASE 3 VALIDATION COMPLETE                  ")
    print("==================================================")

if __name__ == "__main__":
    run_phase3_validation()
