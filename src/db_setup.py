"""
Database Setup & Automated Cleaning Pipeline
1. Loads raw synthetic CSV files into raw staging tables.
2. Invokes DataQualityValidator to audit data hygiene.
3. Performs automated remediation (deduplication, value filtering, foreign key orphan removal, status alignment).
4. Populates clean, normalized relational tables (categories, products, customers, orders, order_items, payments, shipping).
"""

import os
import sqlite3
import pandas as pd
from data_quality_validator import DataQualityValidator

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "retail_intelligence.db")

def initialize_database():
    print("[INFO] Initializing SQLite Relational Database at:", DB_PATH)
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Normalized Production Schema
    cursor.executescript("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY,
        category_name TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        cost_price REAL NOT NULL,
        unit_price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );

    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        country TEXT NOT NULL,
        signup_date TEXT NOT NULL,
        customer_segment_tier TEXT DEFAULT 'Standard'
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        order_status TEXT NOT NULL,
        shipping_cost REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount_amount REAL DEFAULT 0.0,
        item_total REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE payments (
        payment_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        payment_method TEXT NOT NULL,
        payment_status TEXT NOT NULL,
        payment_date TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    CREATE TABLE shipping (
        shipping_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        carrier TEXT NOT NULL,
        shipped_date TEXT,
        estimated_delivery_date TEXT,
        actual_delivery_date TEXT,
        delivery_status TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    """)

    conn.commit()
    return conn

def load_raw_staging_tables(conn):
    print("[INFO] Loading raw CSV artifacts into raw staging tables...")
    raw_files = {
        "categories.csv": "raw_categories",
        "products.csv": "raw_products",
        "customers.csv": "raw_customers",
        "orders.csv": "raw_orders",
        "order_items.csv": "raw_order_items",
        "payments.csv": "raw_payments",
        "shipping.csv": "raw_shipping"
    }

    for fname, table_name in raw_files.items():
        fpath = os.path.join(DATA_RAW_DIR, fname)
        df = pd.read_csv(fpath)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f" Loaded raw staging table: {table_name} ({len(df):,} rows)")

def clean_and_populate_production(conn):
    print("[INFO] Executing automated data remediation into clean production schema...")
    
    # 1. Clean Categories & Products (Direct Load)
    pd.read_sql_query("SELECT * FROM raw_categories", conn).to_sql("categories", conn, if_exists="append", index=False)
    pd.read_sql_query("SELECT * FROM raw_products", conn).to_sql("products", conn, if_exists="append", index=False)
    
    # 2. Clean Customers (Deduplicate Emails if any)
    df_cust = pd.read_sql_query("SELECT * FROM raw_customers", conn)
    df_cust = df_cust.drop_duplicates(subset=["email"])
    df_cust.to_sql("customers", conn, if_exists="append", index=False)
    valid_customer_ids = set(df_cust["customer_id"])

    # 3. Clean Orders (Ensure valid customer foreign key)
    df_orders = pd.read_sql_query("SELECT * FROM raw_orders", conn)
    df_orders = df_orders.drop_duplicates(subset=["order_id"])
    df_orders = df_orders[df_orders["customer_id"].isin(valid_customer_ids)]
    df_orders.to_sql("orders", conn, if_exists="append", index=False)

    valid_order_ids = set(df_orders["order_id"])

    # 4. Clean Order Items (Remove exact duplicates, remove quantity <= 0 or unit_price <= 0)
    df_items = pd.read_sql_query("SELECT * FROM raw_order_items", conn)
    initial_items_len = len(df_items)
    df_items = df_items.drop_duplicates(subset=["order_id", "product_id", "quantity", "unit_price"])
    df_items = df_items[(df_items["quantity"] > 0) & (df_items["unit_price"] > 0)]
    df_items = df_items[df_items["order_id"].isin(valid_order_ids)]
    df_items.to_sql("order_items", conn, if_exists="append", index=False)
    print(f"  Remediated Order Items: dropped {initial_items_len - len(df_items)} anomalous/duplicate rows.")

    # 5. Clean Payments (Remove orphan records not in valid_order_ids, harmonize status)
    df_pay = pd.read_sql_query("SELECT * FROM raw_payments", conn)
    initial_pay_len = len(df_pay)
    df_pay = df_pay[df_pay["order_id"].isin(valid_order_ids)]
    
    # Fix order status conflict: if order is cancelled, set payment status to Refunded/Failed
    cancelled_ids = set(df_orders[df_orders["order_status"] == "Cancelled"]["order_id"])
    df_pay.loc[df_pay["order_id"].isin(cancelled_ids), "payment_status"] = "Refunded"
    df_pay.to_sql("payments", conn, if_exists="append", index=False)
    print(f"  Remediated Payments: removed {initial_pay_len - len(df_pay)} orphan records.")

    # 6. Clean Shipping (Correct actual_delivery_date if preceding order_date)
    df_ship = pd.read_sql_query("SELECT * FROM raw_shipping", conn)
    df_ship = df_ship[df_ship["order_id"].isin(valid_order_ids)]
    
    # Merge order date to validate chronology
    df_ship = df_ship.merge(df_orders[["order_id", "order_date"]], on="order_id", how="left")
    invalid_date_mask = (df_ship["actual_delivery_date"].notnull()) & (df_ship["actual_delivery_date"] < df_ship["order_date"].str[:10])
    df_ship.loc[invalid_date_mask, "actual_delivery_date"] = None
    df_ship.loc[invalid_date_mask, "delivery_status"] = "In-Transit/Delayed"
    df_ship.drop(columns=["order_date"]).to_sql("shipping", conn, if_exists="append", index=False)
    print(f"  Remediated Shipping: corrected {invalid_date_mask.sum()} invalid delivery dates.")

    conn.commit()

def run_db_pipeline():
    conn = initialize_database()
    load_raw_staging_tables(conn)
    
    validator = DataQualityValidator(DB_PATH)
    validator.run_all_checks()
    validator.print_audit_summary()

    clean_and_populate_production(conn)
    
    print("\n[SUCCESS] Production Relational Database populated clean tables successfully!")
    
    # Print row count verification
    cursor = conn.cursor()
    tables = ["categories", "products", "customers", "orders", "order_items", "payments", "shipping"]
    print("--- Production Row Count Audit ---")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f" Table '{t}': {cnt:,} rows")
    print("----------------------------------\n")

    conn.close()

if __name__ == "__main__":
    run_db_pipeline()
