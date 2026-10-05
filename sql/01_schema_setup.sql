-- =============================================================================
-- Retail Revenue & Customer Intelligence Platform
-- Database Schema Definition (MySQL 8.0 / ANSI SQL compliant DDL)
-- 
-- NOTE: Designed for 3NF Transactional Processing with Primary Keys,
-- Foreign Keys, Cascade Rules, Indexing, and Data Type Optimization.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS retail_intelligence_db;
USE retail_intelligence_db;

-- Drop tables in reverse order of foreign key dependency if recreating
DROP TABLE IF EXISTS shipping;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

-- -----------------------------------------------------------------------------
-- 1. Table: categories
-- -----------------------------------------------------------------------------
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 2. Table: products
-- -----------------------------------------------------------------------------
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    cost_price DECIMAL(10, 2) NOT NULL CHECK (cost_price >= 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_categories 
        FOREIGN KEY (category_id) REFERENCES categories(category_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_products_category ON products(category_id);

-- -----------------------------------------------------------------------------
-- 3. Table: customers
-- -----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    signup_date DATE NOT NULL,
    customer_segment_tier VARCHAR(50) DEFAULT 'Standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_customers_signup ON customers(signup_date);
CREATE INDEX idx_customers_location ON customers(country, state, city);

-- -----------------------------------------------------------------------------
-- 4. Table: orders
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME NOT NULL,
    order_status VARCHAR(50) NOT NULL CHECK (order_status IN ('Completed', 'Shipped', 'Processing', 'Cancelled', 'Refunded')),
    shipping_cost DECIMAL(10, 2) DEFAULT 0.00 CHECK (shipping_cost >= 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_customers 
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(order_status);

-- -----------------------------------------------------------------------------
-- 5. Table: order_items
-- -----------------------------------------------------------------------------
CREATE TABLE order_items (
    item_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_amount DECIMAL(10, 2) DEFAULT 0.00 CHECK (discount_amount >= 0),
    item_total DECIMAL(10, 2) NOT NULL CHECK (item_total >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_items_orders 
        FOREIGN KEY (order_id) REFERENCES orders(order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_items_products 
        FOREIGN KEY (product_id) REFERENCES products(product_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);

-- -----------------------------------------------------------------------------
-- 6. Table: payments
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
    payment_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL CHECK (payment_status IN ('Completed', 'Failed', 'Refunded', 'Pending')),
    payment_date DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_orders 
        FOREIGN KEY (order_id) REFERENCES orders(order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(payment_status);

-- -----------------------------------------------------------------------------
-- 7. Table: shipping
-- -----------------------------------------------------------------------------
CREATE TABLE shipping (
    shipping_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    carrier VARCHAR(100) NOT NULL,
    shipped_date DATETIME NULL,
    estimated_delivery_date DATE NULL,
    actual_delivery_date DATE NULL,
    delivery_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_shipping_orders 
        FOREIGN KEY (order_id) REFERENCES orders(order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_shipping_order ON shipping(order_id);
CREATE INDEX idx_shipping_carrier ON shipping(carrier);
