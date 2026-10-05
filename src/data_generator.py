"""
Synthetic Data Generator for Retail Revenue & Customer Intelligence Platform
NOTE: All generated data in this module is 100% SYNTHETIC and generated using probabilistic 
statistical distributions for portfolio analytics and data pipeline validation. 
It does NOT represent real-world customer or proprietary business transactions.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Output directory setup
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_synthetic_dataset():
    print("[INFO] Starting synthetic retail dataset generation...")


    # ---------------------------------------------------------
    # 1. Categories Table (8 categories across 4 departments)
    # ---------------------------------------------------------
    categories_data = [
        {"category_id": 1, "category_name": "Smartphones & Audio", "department": "Electronics"},
        {"category_id": 2, "category_name": "Laptops & Computing", "department": "Electronics"},
        {"category_id": 3, "category_name": "Apparel & Activewear", "department": "Fashion"},
        {"category_id": 4, "category_name": "Footwear & Accessories", "department": "Fashion"},
        {"category_id": 5, "category_name": "Home Appliances & Decor", "department": "Home & Living"},
        {"category_id": 6, "category_name": "Kitchenware & Dining", "department": "Home & Living"},
        {"category_id": 7, "category_name": "Fitness & Outdoor Gear", "department": "Sports & Recreation"},
        {"category_id": 8, "category_name": "Beauty & Personal Care", "department": "Wellness"}
    ]
    df_categories = pd.DataFrame(categories_data)

    # ---------------------------------------------------------
    # 2. Products Table (45 products)
    # ---------------------------------------------------------
    product_names = {
        1: ["Noise-Canceling Wireless Headphones", "Flagship Smartphone Pro", "Bluetooth Pocket Speaker", "Earbuds Ultra", "Smartwatch Series X"],
        2: ["UltraSlim Laptop 15-inch", "Ergonomic Mechanical Keyboard", "4K Ultra-HD Monitor 27-inch", "USB-C Multi-Port Hub", "Wireless Precision Mouse"],
        3: ["Performance Running Jacket", "Seamless Gym Leggings", "Cotton Crewneck T-Shirt 3-Pack", "Thermal Winter Fleece", "Waterproof Hooded Parka"],
        4: ["Leather Crossbody Bag", "Lightweight Trail Running Shoes", "Classic Canvas Sneakers", "Polarized Sunglasses", "Minimalist Leather Wallet"],
        5: ["Robotic Vacuum Cleaner", "HEPA Air Purifier", "Smart LED Desk Lamp", "Memory Foam Pillow Set", "Ceramic Table Lamp"],
        6: ["Stainless Steel Cookware Set", "Programmable Espresso Machine", "Chef Knife 8-inch Premium", "Digital Air Fryer 5L", "Insulated Water Bottle 1L"],
        7: ["Adjustable Dumbbell Pair 24kg", "Yoga Mat Eco-NonSlip", "Camping Tent 4-Person", "Hydration Backpack", "Resistance Band Set"],
        8: ["Hydrating Facial Serum 50ml", "Sonic Electric Toothbrush", "Organic Hair Oil 100ml", "Sunscreen Lotion SPF50", "Botanical Body Wash 500ml"]
    }

    products_list = []
    prod_id_counter = 101

    for cat_id, p_names in product_names.items():
        for name in p_names:
            # Generate realistic pricing & margins
            cost_price = round(float(np.random.uniform(8.0, 350.0)), 2)
            margin_pct = np.random.uniform(0.30, 0.75) # 30% to 75% margin
            unit_price = round(cost_price * (1 + margin_pct), 2)
            stock_qty = int(np.random.randint(25, 500))
            
            products_list.append({
                "product_id": prod_id_counter,
                "product_name": name,
                "category_id": cat_id,
                "cost_price": cost_price,
                "unit_price": unit_price,
                "stock_quantity": stock_qty
            })
            prod_id_counter += 1

    df_products = pd.DataFrame(products_list)

    # ---------------------------------------------------------
    # 3. Customers Table (1,500 customers)
    # ---------------------------------------------------------
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]
    
    locations = [
        ("New York", "NY", "USA"), ("Los Angeles", "CA", "USA"), ("Chicago", "IL", "USA"),
        ("Houston", "TX", "USA"), ("Phoenix", "AZ", "USA"), ("Philadelphia", "PA", "USA"),
        ("San Antonio", "TX", "USA"), ("San Diego", "CA", "USA"), ("Dallas", "TX", "USA"),
        ("Toronto", "ON", "Canada"), ("Vancouver", "BC", "Canada"), ("London", "ENG", "UK"),
        ("Manchester", "ENG", "UK"), ("Berlin", "BE", "Germany"), ("Sydney", "NSW", "Australia")
    ]

    start_signup = datetime(2024, 1, 1)
    end_signup = datetime(2025, 11, 30)
    total_days = (end_signup - start_signup).days

    customers_list = []
    for c_id in range(1001, 2501):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        city, state, country = random.choice(locations)
        
        # Acquisition dates distributed across 2024-2025
        random_days = int(np.random.beta(a=1.5, b=2.0) * total_days)
        signup_dt = start_signup + timedelta(days=random_days)
        
        # Email generation
        email = f"{fn.lower()}.{ln.lower()}{random.randint(10,999)}@example-mail.com"

        customers_list.append({
            "customer_id": c_id,
            "first_name": fn,
            "last_name": ln,
            "email": email,
            "city": city,
            "state": state,
            "country": country,
            "signup_date": signup_dt.strftime("%Y-%m-%d"),
            "customer_segment_tier": "Standard" # Default tier, updated during analytical enrichment
        })

    df_customers = pd.DataFrame(customers_list)

    # ---------------------------------------------------------
    # 4. Orders & Order Items Tables (6,500 orders, ~16,000 items)
    # ---------------------------------------------------------
    orders_list = []
    order_items_list = []
    payments_list = []
    shipping_list = []

    order_id_counter = 50001
    item_id_counter = 80001
    payment_id_counter = 90001
    shipping_id_counter = 70001

    payment_methods = ["Credit Card", "PayPal", "Debit Card", "Apple Pay", "Klarna / BNPL"]
    payment_weights = [0.45, 0.25, 0.15, 0.10, 0.05]

    carriers = ["FedEx Express", "UPS Ground", "DHL Express", "USPS Priority"]

    # Order status weights: Completed=82%, Shipped=8%, Processing=4%, Cancelled=4%, Refunded=2%
    order_statuses = ["Completed", "Shipped", "Processing", "Cancelled", "Refunded"]
    status_weights = [0.82, 0.08, 0.04, 0.04, 0.02]

    start_order_date = datetime(2024, 1, 1)
    end_order_date = datetime(2025, 12, 31)
    total_order_span_days = (end_order_date - start_order_date).days

    # Customer purchase probabilities (Pareto distribution: 20% customers place 60%+ orders)
    customer_ids = df_customers["customer_id"].tolist()
    customer_weights = np.random.pareto(a=2.5, size=len(customer_ids))
    customer_weights /= customer_weights.sum()

    for _ in range(6500):
        c_id = np.random.choice(customer_ids, p=customer_weights)
        c_signup_dt = datetime.strptime(df_customers.loc[df_customers["customer_id"] == c_id, "signup_date"].values[0], "%Y-%m-%d")
        
        # Order date must be on or after signup date
        days_after_signup = int(np.random.exponential(scale=120)) # Mean 120 days lifetime window
        o_date = c_signup_dt + timedelta(days=days_after_signup)
        if o_date > end_order_date:
            o_date = end_order_date - timedelta(days=random.randint(0, 30))
        
        o_status = np.random.choice(order_statuses, p=status_weights)
        shipping_cost = round(float(random.choice([0.00, 4.99, 7.99, 12.50, 15.00])), 2)

        # Generate 1 to 4 items per order
        num_items = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
        selected_prods = df_products.sample(n=num_items)

        order_subtotal = 0.0
        for _, prod in selected_prods.iterrows():
            qty = random.choices([1, 2, 3, 4], weights=[0.70, 0.20, 0.07, 0.03])[0]
            unit_p = float(prod["unit_price"])
            
            # Random discount: 0%, 5%, 10%, 15%, 20%
            disc_pct = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.60, 0.15, 0.15, 0.06, 0.04])[0]
            disc_amt = round(unit_p * qty * disc_pct, 2)
            item_total = round((unit_p * qty) - disc_amt, 2)
            order_subtotal += item_total

            order_items_list.append({
                "item_id": item_id_counter,
                "order_id": order_id_counter,
                "product_id": int(prod["product_id"]),
                "quantity": qty,
                "unit_price": unit_p,
                "discount_amount": disc_amt,
                "item_total": item_total
            })
            item_id_counter += 1

        order_total_amount = round(order_subtotal + shipping_cost, 2)

        orders_list.append({
            "order_id": order_id_counter,
            "customer_id": int(c_id),
            "order_date": o_date.strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": o_status,
            "shipping_cost": shipping_cost,
            "total_amount": order_total_amount
        })

        # Generate Payment record
        pay_method = np.random.choice(payment_methods, p=payment_weights)
        if o_status in ["Completed", "Shipped", "Processing"]:
            pay_status = "Completed"
        elif o_status == "Refunded":
            pay_status = "Refunded"
        else:
            pay_status = "Failed" if random.random() < 0.7 else "Completed"

        pay_dt = o_date + timedelta(minutes=random.randint(1, 30))

        payments_list.append({
            "payment_id": payment_id_counter,
            "order_id": order_id_counter,
            "payment_method": pay_method,
            "payment_status": pay_status,
            "payment_date": pay_dt.strftime("%Y-%m-%d %H:%M:%S")
        })
        payment_id_counter += 1

        # Generate Shipping record
        carrier = random.choice(carriers)
        shipped_dt = o_date + timedelta(hours=random.randint(12, 48))
        est_delivery_dt = shipped_dt + timedelta(days=random.randint(2, 5))
        
        # Delivery delay simulation
        delay_days = random.choices([0, 1, 2, 3, 5], weights=[0.75, 0.12, 0.07, 0.04, 0.02])[0]
        act_delivery_dt = est_delivery_dt + timedelta(days=delay_days)

        if o_status == "Completed":
            delivery_status = "Delivered On-Time" if delay_days == 0 else "Delivered Delayed"
        elif o_status == "Shipped":
            delivery_status = "In-Transit"
            act_delivery_dt = None
        else:
            delivery_status = "Cancelled/Failed"
            shipped_dt = None
            est_delivery_dt = None
            act_delivery_dt = None

        shipping_list.append({
            "shipping_id": shipping_id_counter,
            "order_id": order_id_counter,
            "carrier": carrier,
            "shipped_date": shipped_dt.strftime("%Y-%m-%d %H:%M:%S") if shipped_dt else None,
            "estimated_delivery_date": est_delivery_dt.strftime("%Y-%m-%d") if est_delivery_dt else None,
            "actual_delivery_date": act_delivery_dt.strftime("%Y-%m-%d") if act_delivery_dt else None,
            "delivery_status": delivery_status
        })
        shipping_id_counter += 1
        order_id_counter += 1

    df_orders = pd.DataFrame(orders_list)
    df_order_items = pd.DataFrame(order_items_list)
    df_payments = pd.DataFrame(payments_list)
    df_shipping = pd.DataFrame(shipping_list)

    # ---------------------------------------------------------
    # 5. Inject Controlled Data-Quality Anomalies for Validation Suite
    # ---------------------------------------------------------
    print("[INFO] Injecting controlled data quality anomalies for Data Quality Engine testing...")
    
    # Anomaly 1: 15 Duplicate Order Item rows
    dup_items = df_order_items.sample(n=15, random_state=42).copy()
    df_order_items = pd.concat([df_order_items, dup_items], ignore_index=True)

    # Anomaly 2: 10 Negative or Zero Quantity/Price values in order items
    anomaly_indices = df_order_items.sample(n=10, random_state=101).index
    df_order_items.loc[anomaly_indices[:5], "quantity"] = -1
    df_order_items.loc[anomaly_indices[5:], "unit_price"] = 0.00

    # Anomaly 3: 8 Orphan Payment records (order_id not in orders table)
    for i in range(8):
        payments_list.append({
            "payment_id": 99990 + i,
            "order_id": 999990 + i, # Non-existent order_id
            "payment_method": "Credit Card",
            "payment_status": "Completed",
            "payment_date": "2025-06-15 10:00:00"
        })
    df_payments = pd.DataFrame(payments_list)

    # Anomaly 4: 12 Delivery dates preceding order date
    shipping_anomaly_idx = df_shipping[df_shipping["actual_delivery_date"].notnull()].sample(n=12, random_state=202).index
    df_shipping.loc[shipping_anomaly_idx, "actual_delivery_date"] = "2023-12-01"

    # Anomaly 5: 10 Order Status vs Payment Status Inconsistencies (Order Cancelled, Payment Completed)
    cancelled_orders = df_orders[df_orders["order_status"] == "Cancelled"]["order_id"].tolist()
    if len(cancelled_orders) >= 10:
        target_orders = cancelled_orders[:10]
        df_payments.loc[df_payments["order_id"].isin(target_orders), "payment_status"] = "Completed"

    # ---------------------------------------------------------
    # 6. Save Raw CSV Artifacts
    # ---------------------------------------------------------
    datasets = {
        "categories.csv": df_categories,
        "products.csv": df_products,
        "customers.csv": df_customers,
        "orders.csv": df_orders,
        "order_items.csv": df_order_items,
        "payments.csv": df_payments,
        "shipping.csv": df_shipping
    }

    for fname, df in datasets.items():
        filepath = os.path.join(OUTPUT_DIR, fname)
        df.to_csv(filepath, index=False)
        print(f" [SUCCESS] Saved raw artifact: {fname} ({len(df):,} rows)")

    print("[SUCCESS] Synthetic data generation completed successfully!")
    return OUTPUT_DIR

if __name__ == "__main__":
    generate_synthetic_dataset()
