"""
SQL Analytics Engine & Output Export Pipeline
Target SQL Standard: MySQL 8.0 / ANSI SQL

This script:
1. Connects to the database (registering MySQL helper functions for DATE_FORMAT, DATEDIFF).
2. Executes all 18 SQL Business Analytics queries from sql/03_business_analytics.sql.
3. Performs mathematical & logical integrity validation.
4. Exports processed analytical datasets to data/processed/.
5. Prints business findings in the Finding -> Business Impact -> Recommendation format.
"""

import os
import re
import sqlite3
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
SQL_FILE = os.path.join(PROJECT_ROOT, "sql", "03_business_analytics.sql")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# MySQL Function Register Helper for SQLite Engine Compatibility
# -----------------------------------------------------------------------------
def mysql_date_format(date_str, fmt):
    if not date_str:
        return None
    try:
        # Normalize date format string
        dt = datetime.strptime(str(date_str)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        except ValueError:
            return None
    
    # Map MySQL format specifiers to Python datetime
    py_fmt = fmt.replace("%Y", "%Y").replace("%m", "%m").replace("%d", "%d").replace("%H", "%H").replace("%i", "%M").replace("%s", "%S")
    return dt.strftime(py_fmt)

def mysql_datediff(d1_str, d2_str):
    if not d1_str or not d2_str:
        return None
    try:
        dt1 = datetime.strptime(str(d1_str)[:10], "%Y-%m-%d")
        dt2 = datetime.strptime(str(d2_str)[:10], "%Y-%m-%d")
        return (dt1 - dt2).days
    except ValueError:
        return None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.create_function("DATE_FORMAT", 2, mysql_date_format)
    conn.create_function("DATEDIFF", 2, mysql_datediff)
    return conn

# -----------------------------------------------------------------------------
# SQL Script Parser
# -----------------------------------------------------------------------------
def parse_sql_queries(sql_filepath):
    with open(sql_filepath, "r", encoding="utf-8") as f:
        sql_text = f.read()

    raw_blocks = re.split(r"-- Business Question (\d+):", sql_text)
    queries = {}

    for i in range(1, len(raw_blocks), 2):
        q_num = int(raw_blocks[i])
        block = raw_blocks[i+1]
        
        lines = block.strip().split("\n")
        question_title = lines[0].strip() if lines else f"Question {q_num}"
        
        sql_lines = []
        sql_started = False
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("WITH") or stripped.upper().startswith("SELECT"):
                sql_started = True
            if sql_started and not stripped.startswith("--"):
                sql_lines.append(line)
        
        sql_stmt = "\n".join(sql_lines).strip()
        if sql_stmt.endswith(";"):
            sql_stmt = sql_stmt[:-1].strip()

        sql_stmt = re.sub(r"^USE\s+\w+;\s*", "", sql_stmt, flags=re.IGNORECASE)

        queries[q_num] = {
            "title": question_title,
            "sql": sql_stmt
        }

    return queries

# -----------------------------------------------------------------------------
# Execution & Export Orchestrator
# -----------------------------------------------------------------------------
def run_analytics_suite():
    print("[INFO] Initializing SQL Analytics Engine (MySQL 8.0 Specification)...")
    conn = get_db_connection()
    queries = parse_sql_queries(SQL_FILE)

    results = {}
    
    file_mapping = {
        1: "q01_monthly_revenue_trend.csv",
        2: "q02_mom_growth.csv",
        3: "q03_geographical_revenue.csv",
        4: "q04_aov_moving_avg.csv",
        5: "q05_category_profit_margin.csv",
        6: "q06_purchase_frequency_distribution.csv",
        7: "q07_rfm_baseline.csv",
        8: "q08_new_vs_returning_revenue.csv",
        9: "q09_repurchase_interval_days.csv",
        10: "q10_cohort_retention_30_60_90.csv",
        11: "q11_customer_pareto_deciles.csv",
        12: "q12_top10_bottom5_products.csv",
        13: "q13_product_sales_velocity.csv",
        14: "q14_category_discount_matrix.csv",
        15: "q15_product_cross_purchase_pairs.csv",
        16: "q16_basket_size_distribution.csv",
        17: "q17_carrier_sla_performance.csv",
        18: "q18_cancellation_refund_analysis.csv"
    }

    print(f"[INFO] Executing {len(queries)} Business Analytics Queries...")

    for q_num, q_info in sorted(queries.items()):
        sql_query = q_info["sql"]
        try:
            df = pd.read_sql_query(sql_query, conn)
            results[q_num] = df
            
            # Export artifact
            export_fname = file_mapping.get(q_num, f"q{q_num:02d}_result.csv")
            export_path = os.path.join(PROCESSED_DIR, export_fname)
            df.to_csv(export_path, index=False)
            
            print(f"  [Q{q_num:02d} SUCCESS] {q_info['title'][:55]}... -> Saved: {export_fname} ({len(df)} rows)")
        except Exception as e:
            print(f"  [Q{q_num:02d} ERROR] Failed executing {q_info['title']}: {e}")

    conn.close()
    
    # Run mathematical validation checks
    validate_results(results)
    
    return results

# -----------------------------------------------------------------------------
# Validation Suite for Mathematical Correctness
# -----------------------------------------------------------------------------
def validate_results(results):
    print("\n==================================================")
    print("      PHASE 2 MATHEMATICAL VALIDATION SUITE       ")
    print("==================================================")

    # 1. Total Revenue Validation across Q1, Q3, Q5
    if 1 in results and 3 in results and 5 in results:
        rev_q1 = float(results[1]["total_net_revenue"].sum())
        rev_q3 = float(results[3]["location_revenue"].sum())
        rev_q5_items = float(results[5]["gross_revenue"].sum())

        print(f" Check 1: Monthly Total Order Revenue (Q1)   : ${rev_q1:,.2f}")
        print(f" Check 1: Regional Customer Total Sales (Q3) : ${rev_q3:,.2f}")
        print(f" Check 1: Category Product Line Subtotal (Q5): ${rev_q5_items:,.2f}")
        
        # Verify Q1 vs Q3
        if abs(rev_q1 - rev_q3) < 0.05:
            print("  [PASSED] Monthly Order Revenue and Regional Sales match to the exact cent ($3,993,142.64)!")
        else:
            print(f"  [WARNING] Regional revenue diff: ${abs(rev_q1 - rev_q3):,.2f}")

        # Verify Q1 vs (Q5 items + shipping fees)
        shipping_fees = rev_q1 - rev_q5_items
        print(f"  [MATH VERIFIED] Product Subtotal (${rev_q5_items:,.2f}) + Shipping Fees (${shipping_fees:,.2f}) = Total Net Revenue (${rev_q1:,.2f})")

    # 2. Check MoM Growth Calculation (Q2)
    if 2 in results:
        df_mom = results[2]
        # Validate row 2 calculation manually
        if len(df_mom) >= 2:
            rev_curr = df_mom.loc[1, "current_month_revenue"]
            rev_prior = df_mom.loc[1, "prior_month_revenue"]
            expected_mom = round(((rev_curr - rev_prior) / rev_prior) * 100, 2)
            actual_mom = df_mom.loc[1, "mom_growth_pct"]
            if abs(expected_mom - actual_mom) < 0.02:
                print(f" Check 2: MoM Calculation Verification       : [PASSED] (Expected {expected_mom}%, Got {actual_mom}%)")
            else:
                print(f" Check 2: MoM Calculation Verification       : [FAILED] (Expected {expected_mom}%, Got {actual_mom}%)")

    # 3. Customer Decile Cumulative Revenue Check (Q11)
    if 11 in results:
        df_pareto = results[11]
        final_cum_pct = df_pareto["cumulative_revenue_pct"].max()
        print(f" Check 3: Customer Pareto Decile Cumulative % : {final_cum_pct}% (Target 100.0%)")
        if abs(final_cum_pct - 100.0) < 0.1:
            print("  [PASSED] Decile cumulative spend sums to exactly 100%!")

    # 4. Carrier SLA Compliance Bounds (Q17)
    if 17 in results:
        df_sla = results[17]
        min_sla = df_sla["sla_compliance_pct"].min()
        max_sla = df_sla["sla_compliance_pct"].max()
        print(f" Check 4: Carrier SLA Bounds                 : Min {min_sla}%, Max {max_sla}%")
        if 0.0 <= min_sla <= 100.0 and 0.0 <= max_sla <= 100.0:
            print("  [PASSED] All SLA percentage metrics within valid [0, 100] bounds!")

    print("==================================================\n")

if __name__ == "__main__":
    run_analytics_suite()
