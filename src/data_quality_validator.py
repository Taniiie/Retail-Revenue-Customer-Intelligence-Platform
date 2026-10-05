"""
Data Quality Validation Engine for Retail Revenue & Customer Intelligence Platform

This framework runs programmatic data quality audits across:
1. Duplicate Records
2. Mandatory Attribute Nulls
3. Out-of-Range Numeric Values (Negative quantities / prices)
4. Chronological & Date Inconsistencies
5. Foreign Key Orphan Integrity
6. Cross-table Status Conflicts
"""

import os
import sqlite3
import pandas as pd

class DataQualityValidator:
    def __init__(self, db_path):
        self.db_path = db_path
        self.audit_results = {}

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def run_all_checks(self):
        print("[INFO] Executing Data Quality Audit Suite...")
        conn = self.get_connection()

        self.audit_results["duplicates"] = self._check_duplicates(conn)
        self.audit_results["nulls"] = self._check_nulls(conn)
        self.audit_results["invalid_ranges"] = self._check_invalid_ranges(conn)
        self.audit_results["chronology"] = self._check_chronology(conn)
        self.audit_results["orphans"] = self._check_orphans(conn)
        self.audit_results["status_conflicts"] = self._check_status_conflicts(conn)

        conn.close()
        return self.audit_results

    def _check_duplicates(self, conn):
        query = """
        SELECT order_id, product_id, quantity, unit_price, COUNT(*) as dup_count
        FROM raw_order_items
        GROUP BY order_id, product_id, quantity, unit_price
        HAVING COUNT(*) > 1;
        """
        df = pd.read_sql_query(query, conn)
        print(f"  [DQ Audit 1] Duplicate Order Item Records Flagged: {len(df)}")
        return df

    def _check_nulls(self, conn):
        query = """
        SELECT 'orders' as table_name, COUNT(*) as null_count FROM raw_orders WHERE customer_id IS NULL OR order_date IS NULL OR total_amount IS NULL
        UNION ALL
        SELECT 'customers' as table_name, COUNT(*) as null_count FROM raw_customers WHERE email IS NULL OR signup_date IS NULL;
        """
        df = pd.read_sql_query(query, conn)
        total_nulls = df['null_count'].sum()
        print(f"  [DQ Audit 2] Null Value Records Flagged: {total_nulls}")
        return df

    def _check_invalid_ranges(self, conn):
        query = """
        SELECT item_id, order_id, product_id, quantity, unit_price
        FROM raw_order_items
        WHERE quantity <= 0 OR unit_price <= 0;
        """
        df = pd.read_sql_query(query, conn)
        print(f"  [DQ Audit 3] Invalid Range Records (Qty <= 0 or Price <= 0): {len(df)}")
        return df

    def _check_chronology(self, conn):
        query = """
        SELECT s.shipping_id, s.order_id, o.order_date, s.actual_delivery_date
        FROM raw_shipping s
        JOIN raw_orders o ON s.order_id = o.order_id
        WHERE s.actual_delivery_date IS NOT NULL 
          AND DATE(s.actual_delivery_date) < DATE(o.order_date);
        """
        df = pd.read_sql_query(query, conn)
        print(f"  [DQ Audit 4] Chronological Date Anomalies Flagged: {len(df)}")
        return df

    def _check_orphans(self, conn):
        query = """
        SELECT p.payment_id, p.order_id
        FROM raw_payments p
        LEFT JOIN raw_orders o ON p.order_id = o.order_id
        WHERE o.order_id IS NULL;
        """
        df = pd.read_sql_query(query, conn)
        print(f"  [DQ Audit 5] Orphan Payment Records (No Parent Order): {len(df)}")
        return df

    def _check_status_conflicts(self, conn):
        query = """
        SELECT o.order_id, o.order_status, p.payment_id, p.payment_status
        FROM raw_orders o
        JOIN raw_payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'Cancelled' AND p.payment_status = 'Completed';
        """
        df = pd.read_sql_query(query, conn)
        print(f"  [DQ Audit 6] Order Status vs Payment Status Conflicts: {len(df)}")
        return df

    def print_audit_summary(self):
        print("\n==================================================")
        print("         DATA QUALITY AUDIT SUMMARY REPORT        ")
        print("==================================================")
        print(f" 1. Exact Duplicate Order Items : {len(self.audit_results['duplicates'])} rows")
        print(f" 2. Null Value Violations       : {self.audit_results['nulls']['null_count'].sum()} rows")
        print(f" 3. Out-of-Range Quantities/Prices: {len(self.audit_results['invalid_ranges'])} rows")
        print(f" 4. Delivery Prior to Order Date: {len(self.audit_results['chronology'])} rows")
        print(f" 5. Orphan Payment Foreign Keys : {len(self.audit_results['orphans'])} rows")
        print(f" 6. Cancelled Order Status Spills: {len(self.audit_results['status_conflicts'])} rows")
        print("==================================================\n")
