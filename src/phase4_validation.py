"""
Phase 4 Cross-Platform Validation & Reconciliation Script
Validates Power BI star schema outputs against SQL and Python analytical totals.
"""

import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")
PBI_DIR = os.path.join(PROJECT_ROOT, "power_bi", "data_sources")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def run_phase4_validation():
    print("=" * 60)
    print("  PHASE 4: POWER BI CROSS-PLATFORM VALIDATION REPORT")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Load Star Schema Tables
    fact_orders = pd.read_csv(os.path.join(PBI_DIR, "FactOrders.csv"))
    fact_items = pd.read_csv(os.path.join(PBI_DIR, "FactOrderItems.csv"))
    fact_shipping = pd.read_csv(os.path.join(PBI_DIR, "FactShipping.csv"))
    dim_customer = pd.read_csv(os.path.join(PBI_DIR, "DimCustomer.csv"))
    dim_product = pd.read_csv(os.path.join(PBI_DIR, "DimProduct.csv"))
    dim_date = pd.read_csv(os.path.join(PBI_DIR, "DimDate.csv"))
    dim_category = pd.read_csv(os.path.join(PBI_DIR, "DimCategory.csv"))

    # Load pre-validated SQL/Python outputs
    df_monthly = pd.read_csv(os.path.join(PROCESSED_DIR, "monthly_revenue_summary.csv"))
    df_rfm = pd.read_csv(os.path.join(PROCESSED_DIR, "customer_rfm.csv"))
    df_cust_summary = pd.read_csv(os.path.join(PROCESSED_DIR, "customer_summary.csv"))
    df_cohort_ret = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort_retention.csv"), index_col=0)
    df_cohort_ltv = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort_ltv.csv"), index_col=0)

    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            status = "PASSED"
            passed += 1
        else:
            status = "FAILED"
            failed += 1
        print(f"  [{status}] {label}")
        if detail:
            print(f"           {detail}")

    # ---- 1. Total Revenue ----
    print("\n[CHECK 1] Total Revenue Reconciliation")
    pbi_rev = fact_orders[fact_orders["order_status"].isin(["Completed", "Shipped"])]["total_amount"].sum()
    sql_rev = df_monthly["net_revenue"].sum()
    rfm_rev = df_rfm["monetary"].sum()
    db_rev = pd.read_sql_query(
        "SELECT SUM(total_amount) as t FROM orders WHERE order_status IN ('Completed','Shipped')", conn
    ).iloc[0]["t"]
    
    check("PBI FactOrders vs SQL Monthly Revenue",
          abs(pbi_rev - sql_rev) < 0.01,
          f"PBI: ${pbi_rev:,.2f} | SQL: ${sql_rev:,.2f}")
    check("PBI FactOrders vs RFM Monetary Total",
          abs(pbi_rev - rfm_rev) < 0.01,
          f"PBI: ${pbi_rev:,.2f} | RFM: ${rfm_rev:,.2f}")
    check("PBI FactOrders vs Database Direct Query",
          abs(pbi_rev - db_rev) < 0.01,
          f"PBI: ${pbi_rev:,.2f} | DB: ${db_rev:,.2f}")

    # ---- 2. Total Orders ----
    print("\n[CHECK 2] Total Orders Reconciliation")
    pbi_orders = fact_orders[fact_orders["order_status"].isin(["Completed", "Shipped"])]["order_id"].nunique()
    sql_orders = int(df_monthly["total_orders"].sum())
    db_orders = pd.read_sql_query(
        "SELECT COUNT(DISTINCT order_id) as t FROM orders WHERE order_status IN ('Completed','Shipped')", conn
    ).iloc[0]["t"]
    
    check("PBI FactOrders vs SQL Order Count",
          pbi_orders == sql_orders,
          f"PBI: {pbi_orders} | SQL: {sql_orders}")
    check("PBI FactOrders vs Database Direct Query",
          pbi_orders == db_orders,
          f"PBI: {pbi_orders} | DB: {db_orders}")

    # ---- 3. Active Customer Count ----
    print("\n[CHECK 3] Active Customer Count Reconciliation")
    pbi_customers = fact_orders[fact_orders["order_status"].isin(["Completed", "Shipped"])]["customer_id"].nunique()
    rfm_customers = len(df_rfm)
    
    check("PBI FactOrders Active Customers vs RFM Dataset",
          pbi_customers == rfm_customers,
          f"PBI: {pbi_customers} | RFM: {rfm_customers}")

    # ---- 4. AOV ----
    print("\n[CHECK 4] AOV Reconciliation")
    pbi_aov = pbi_rev / pbi_orders
    sql_aov = sql_rev / sql_orders
    
    check("PBI AOV vs SQL AOV",
          abs(pbi_aov - sql_aov) < 0.01,
          f"PBI: ${pbi_aov:,.2f} | SQL: ${sql_aov:,.2f}")

    # ---- 5. Product Universe Reconciliation ----
    print("\n[CHECK 5] Product Count Reconciliation")
    db_products = pd.read_sql_query("SELECT COUNT(*) as t FROM products", conn).iloc[0]["t"]
    pbi_products = len(dim_product)
    check("DimProduct Count vs Database Product Catalog",
          pbi_products == 40 and db_products == 40 and pbi_products == db_products,
          f"DimProduct: {pbi_products} | Database: {db_products} | Target Authoritative: 40")

    # ---- 6. Carrier SLA Compliance & Shipping Reconciliation ----
    print("\n[CHECK 6] Carrier SLA Compliance & Shipping Reconciliation")
    delivered_shipping = fact_shipping[fact_shipping["actual_delivery_date"].notna()]
    on_time_count = len(delivered_shipping[delivered_shipping["delivery_status"] == "Delivered On-Time"])
    delivered_count = len(delivered_shipping)
    pbi_sla_rate = round((on_time_count / delivered_count) * 100, 2)
    
    db_shipping_sla = pd.read_sql_query("""
        SELECT ROUND(
            COUNT(CASE WHEN delivery_status = 'Delivered On-Time' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN actual_delivery_date IS NOT NULL THEN 1 END), 0), 2
        ) AS sla_pct
        FROM shipping
        WHERE actual_delivery_date IS NOT NULL
    """, conn).iloc[0]["sla_pct"]

    check("PBI FactShipping Carrier SLA Rate vs SQL Q17",
          abs(pbi_sla_rate - db_shipping_sla) < 0.01 and abs(pbi_sla_rate - 74.47) < 0.01,
          f"PBI Star Schema SLA Rate: {pbi_sla_rate}% | SQL Q17 SLA Rate: {db_shipping_sla}% | Authoritative Benchmark: 74.47%")

    # ---- 7. Category Revenue ----
    print("\n[CHECK 7] Category Revenue Reconciliation")
    valid_items = fact_items[fact_items["order_status"].isin(["Completed", "Shipped"])]
    pbi_cat_rev = valid_items.merge(dim_product[["product_id", "category_name"]], on="product_id") \
        .groupby("category_name")["item_total"].sum().sort_values(ascending=False)
    
    sql_cat = pd.read_csv(os.path.join(PROCESSED_DIR, "q05_category_profit_margin.csv"))
    
    for _, row in sql_cat.iterrows():
        cat = row["category_name"]
        sql_val = row["gross_revenue"]
        pbi_val = pbi_cat_rev.get(cat, 0)
        check(f"Category '{cat}'",
              abs(pbi_val - sql_val) < 0.01,
              f"PBI: ${pbi_val:,.2f} | SQL: ${sql_val:,.2f}")

    # ---- 8. RFM Segment Revenue ----
    print("\n[CHECK 8] RFM Segment Revenue Reconciliation")
    for _, row in df_cust_summary.iterrows():
        seg = row["rfm_segment"]
        seg_rev_python = row["total_segment_revenue"]
        seg_cust_python = int(row["customer_count"])
        
        seg_customers_pbi = dim_customer[dim_customer["rfm_segment"] == seg]
        seg_cust_pbi = len(seg_customers_pbi)
        seg_rev_pbi = seg_customers_pbi["monetary"].sum()
        
        check(f"Segment '{seg}' Customer Count",
              seg_cust_pbi == seg_cust_python,
              f"PBI: {seg_cust_pbi} | Python: {seg_cust_python}")
        check(f"Segment '{seg}' Revenue",
              abs(seg_rev_pbi - seg_rev_python) < 0.01,
              f"PBI: ${seg_rev_pbi:,.2f} | Python: ${seg_rev_python:,.2f}")

    # ---- 9. Cohort Retention ----
    print("\n[CHECK 9] Cohort Retention Validation")
    pbi_cohort = pd.read_csv(os.path.join(PBI_DIR, "cohort_retention.csv"), index_col=0)
    
    # Check Month 0 = 100%
    month0 = pbi_cohort.iloc[:, 0].dropna()
    check("All cohorts Month 0 = 100%",
          (month0 == 100.0).all(),
          f"Values: min={month0.min()}, max={month0.max()}")
    
    # Check no value > 100%
    max_ret = pbi_cohort.max().max()
    check("No retention value exceeds 100%",
          max_ret <= 100.0,
          f"Max retention: {max_ret}%")
    
    # Check Month 1 average matches
    python_m1 = df_cohort_ret.iloc[:, 1].mean() if df_cohort_ret.shape[1] > 1 else 0
    pbi_m1 = pbi_cohort.iloc[:, 1].mean() if pbi_cohort.shape[1] > 1 else 0
    check("Avg Month 1 Retention Match",
          abs(python_m1 - pbi_m1) < 0.01 and abs(pbi_m1 - 40.98) < 0.01,
          f"PBI: {pbi_m1:.2f}% | Python: {python_m1:.2f}% | Target: 40.98%")

    # Check Month 6 average matches
    pbi_m6 = pbi_cohort["6"].dropna().mean() if "6" in pbi_cohort.columns else 0
    check("Avg Month 6 Retention Match (Authoritative Benchmark)",
          abs(pbi_m6 - 19.54) < 0.01,
          f"PBI Star Schema M6 Retention: {pbi_m6:.2f}% | Target Authoritative Benchmark: 19.54%")

    # ---- 10. Historical LTV ----
    print("\n[CHECK 10] Historical LTV Validation")
    pbi_ltv = pd.read_csv(os.path.join(PBI_DIR, "cohort_ltv.csv"), index_col=0)
    
    # LTV should be monotonically non-decreasing
    ltv_ok = True
    for idx, row in pbi_ltv.iterrows():
        vals = row.dropna().values
        if len(vals) > 1 and not all(vals[i] <= vals[i+1] + 0.01 for i in range(len(vals)-1)):
            ltv_ok = False
            break
    check("LTV Monotonicity (cumulative, non-decreasing)", ltv_ok)

    # ---- 11. Gross Profit ----
    print("\n[CHECK 11] Gross Profit Reconciliation")
    pbi_gp = valid_items["line_gross_profit"].sum()
    sql_gp = sql_cat["gross_profit"].sum()
    check("PBI Gross Profit vs SQL Category Gross Profit Sum",
          abs(pbi_gp - sql_gp) < 0.01,
          f"PBI: ${pbi_gp:,.2f} | SQL: ${sql_gp:,.2f}")

    # ---- 12. DimDate Coverage ----
    print("\n[CHECK 12] DimDate Coverage Validation")
    min_order = pd.to_datetime(fact_orders["order_date"]).min().strftime("%Y-%m-%d")
    max_order = pd.to_datetime(fact_orders["order_date"]).max().strftime("%Y-%m-%d")
    min_dim = dim_date["date"].min()
    max_dim = dim_date["date"].max()
    check("DimDate covers full order date range",
          min_dim <= min_order and max_dim >= max_order,
          f"Orders: {min_order} to {max_order} | DimDate: {min_dim} to {max_dim}")

    # ---- 13. File Completeness ----
    print("\n[CHECK 13] Star Schema File Completeness")
    expected_files = [
        "DimDate.csv", "DimCustomer.csv", "DimProduct.csv", "DimCategory.csv",
        "FactOrders.csv", "FactOrderItems.csv", "FactShipping.csv",
        "cohort_retention.csv", "cohort_ltv.csv"
    ]
    for f in expected_files:
        exists = os.path.exists(os.path.join(PBI_DIR, f))
        check(f"File: {f}", exists)

    conn.close()

    # ---- Summary ----
    print("\n" + "=" * 60)
    print(f"  VALIDATION SUMMARY: {passed} PASSED / {failed} FAILED")
    print("=" * 60)

if __name__ == "__main__":
    run_phase4_validation()
