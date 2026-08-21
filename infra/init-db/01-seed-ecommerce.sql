-- ==============================================================================
-- Governed AI Database Copilot - Sample E-Commerce Seed Script
-- Database: ecommerce_demo
-- ==============================================================================

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS refunds CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS glossary_terms CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;

-- 1. Customers Table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'USA',
    signup_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'churned')),
    lifetime_value NUMERIC(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Orders Table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'cancelled', 'refunded')),
    payment_method VARCHAR(30) NOT NULL,
    shipping_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Order Items Table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_percent NUMERIC(5, 2) DEFAULT 0.00 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    line_total NUMERIC(10, 2) GENERATED ALWAYS AS (quantity * unit_price * (1.0 - (discount_percent / 100.0))) STORED
);

-- 5. Refunds Table
CREATE TABLE refunds (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    refund_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    reason VARCHAR(255) NOT NULL,
    processed_by VARCHAR(50) DEFAULT 'system_auto'
);

-- 6. Business Glossary / Metadata Table
CREATE TABLE glossary_terms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(100) NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    target_table VARCHAR(50),
    target_column VARCHAR(50),
    business_rule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Copilot Audit Logs Table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    connection_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) DEFAULT 'anonymous_user',
    prompt TEXT NOT NULL,
    sql_executed TEXT,
    risk_level VARCHAR(20) NOT NULL, -- 'none', 'low', 'high'
    confirmed_by_user BOOLEAN DEFAULT FALSE,
    confirmation_token VARCHAR(128),
    rows_affected INT DEFAULT 0,
    reverse_sql TEXT,
    rolled_back BOOLEAN DEFAULT FALSE,
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- POPULATE SEED DATA
-- ==============================================================================

-- Seed Customers (Mix of active, inactive, churned across different signup dates)
INSERT INTO customers (id, first_name, last_name, email, country, signup_date, status, lifetime_value) VALUES
(1, 'Alice', 'Morgan', 'alice.morgan@example.com', 'USA', '2023-01-15', 'active', 1450.00),
(2, 'Bob', 'Smith', 'bob.smith@example.com', 'UK', '2022-06-10', 'inactive', 320.50),
(3, 'Charlie', 'Davis', 'charlie.davis@example.com', 'Canada', '2021-11-20', 'churned', 89.00),
(4, 'Diana', 'Prince', 'diana.prince@example.com', 'USA', '2023-03-01', 'active', 2890.00),
(5, 'Evan', 'Wright', 'evan.wright@example.com', 'Germany', '2022-09-18', 'inactive', 450.00),
(6, 'Fiona', 'Gallagher', 'fiona.g@example.com', 'USA', '2024-01-05', 'active', 620.00),
(7, 'George', 'Miller', 'george.m@example.com', 'Australia', '2021-04-12', 'churned', 120.00),
(8, 'Hannah', 'Abbott', 'hannah.a@example.com', 'UK', '2023-07-22', 'active', 940.00),
(9, 'Ian', 'Malcolm', 'ian.m@example.com', 'USA', '2022-02-14', 'inactive', 210.00),
(10, 'Julia', 'Roberts', 'julia.r@example.com', 'France', '2023-10-30', 'active', 1850.00);

SELECT setval('customers_id_seq', 10);

-- Seed Products
INSERT INTO products (id, sku, name, category, unit_price, stock_quantity, is_discontinued) VALUES
(1, 'ELEC-KB-001', 'Mechanical Gaming Keyboard', 'Electronics', 129.99, 45, FALSE),
(2, 'ELEC-MS-002', 'Wireless Ergonomic Mouse', 'Electronics', 69.99, 120, FALSE),
(3, 'ELEC-MN-003', '27-inch 4K IPS Monitor', 'Electronics', 349.99, 18, FALSE),
(4, 'FURN-CH-004', 'Ergonomic Mesh Office Chair', 'Furniture', 249.00, 25, FALSE),
(5, 'FURN-DK-005', 'Motorized Standing Desk', 'Furniture', 499.00, 12, FALSE),
(6, 'ACC-USB-006', 'USB-C Multi-port Hub 7-in-1', 'Accessories', 39.99, 210, FALSE),
(7, 'ACC-HD-007', 'Noise-Cancelling Headphones', 'Audio', 199.99, 35, FALSE),
(8, 'ACC-ST-008', 'Aluminum Laptop Stand', 'Accessories', 45.00, 85, FALSE),
(9, 'ELEC-OLD-009', 'VGA to DVI Adapter Cable', 'Electronics', 9.99, 0, TRUE),
(10, 'FURN-OLD-010', 'Classic Wooden Lamp', 'Furniture', 29.99, 0, TRUE);

SELECT setval('products_id_seq', 10);

-- Seed Orders
INSERT INTO orders (id, customer_id, order_date, total_amount, status, payment_method, shipping_address) VALUES
(1, 1, '2024-01-10 14:20:00+00', 479.98, 'completed', 'credit_card', '123 Main St, New York, NY'),
(2, 4, '2024-01-15 09:45:00+00', 748.00, 'completed', 'stripe', '456 Elm St, Metropolis, NY'),
(3, 2, '2023-12-05 11:30:00+00', 129.99, 'completed', 'paypal', '10 Downing St, London, UK'),
(4, 6, '2024-02-01 16:15:00+00', 69.99, 'completed', 'credit_card', '789 Oak St, Chicago, IL'),
(5, 8, '2024-02-10 10:00:00+00', 584.00, 'processing', 'credit_card', '14 Victoria Rd, Manchester, UK'),
(6, 10, '2024-02-18 18:22:00+00', 349.99, 'completed', 'apple_pay', '5 Champs-Elysees, Paris, France'),
(7, 3, '2022-08-14 13:00:00+00', 89.00, 'refunded', 'credit_card', '88 Maple Ave, Toronto, Canada'),
(8, 5, '2023-05-20 15:40:00+00', 249.00, 'completed', 'bank_transfer', '12 Berliner Strasse, Berlin, Germany'),
(9, 7, '2022-01-11 12:10:00+00', 120.00, 'cancelled', 'paypal', '20 Sydney Way, Sydney, Australia'),
(10, 1, '2024-02-25 17:05:00+00', 239.98, 'completed', 'credit_card', '123 Main St, New York, NY'),
(11, 4, '2024-03-01 08:30:00+00', 499.00, 'completed', 'stripe', '456 Elm St, Metropolis, NY'),
(12, 9, '2023-04-10 19:15:00+00', 210.00, 'completed', 'credit_card', '99 Jurassic Rd, Isla Nublar, CR');

SELECT setval('orders_id_seq', 12);

-- Seed Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent) VALUES
(1, 3, 1, 349.99, 0.0),
(1, 1, 1, 129.99, 0.0),
(2, 5, 1, 499.00, 0.0),
(2, 4, 1, 249.00, 0.0),
(3, 1, 1, 129.99, 0.0),
(4, 2, 1, 69.99, 0.0),
(5, 5, 1, 499.00, 0.0),
(5, 8, 2, 45.00, 5.0),
(6, 3, 1, 349.99, 0.0),
(7, 8, 2, 45.00, 0.0),
(8, 4, 1, 249.00, 0.0),
(9, 6, 3, 40.00, 0.0),
(10, 7, 1, 199.99, 0.0),
(10, 6, 1, 39.99, 0.0),
(11, 5, 1, 499.00, 0.0),
(12, 7, 1, 199.99, 0.0),
(12, 9, 1, 9.99, 0.0);

-- Seed Refunds
INSERT INTO refunds (order_id, refund_date, amount, reason, processed_by) VALUES
(7, '2022-08-16 10:30:00+00', 89.00, 'Customer requested return due to incorrect item size', 'support_sarah');

-- Seed Glossary Terms (Business definitions to support RAG and Ambiguity checks)
INSERT INTO glossary_terms (term, definition, target_table, target_column, business_rule) VALUES
('churned customer', 'A customer who has not placed an order in over 180 days or whose status is marked as churned.', 'customers', 'status', 'Filter WHERE status = ''churned'' OR id NOT IN (SELECT customer_id FROM orders WHERE order_date >= NOW() - INTERVAL ''180 days'')'),
('active customer', 'A customer with status = ''active'' who has made at least one completed purchase in the last 90 days.', 'customers', 'status', 'Filter WHERE status = ''active'''),
('best employee', 'AMBIGUOUS TERM. Could refer to highest sales revenue processed, highest number of orders managed, or best support ticket resolution.', NULL, NULL, 'MUST trigger disambiguation question to the user'),
('gross sales', 'Sum of all completed and processing order total_amount values before refunds.', 'orders', 'total_amount', 'SUM(total_amount) WHERE status IN (''completed'', ''processing'')'),
('net sales', 'Gross sales minus total amount of processed refunds.', 'orders', 'total_amount', 'Gross sales SUM minus refunds SUM(amount)'),
('discontinued products', 'Products where is_discontinued is TRUE or stock_quantity = 0 with no restock date.', 'products', 'is_discontinued', 'WHERE is_discontinued = TRUE');

-- Verify seeding counts
DO $$
DECLARE
    cust_count INT;
    prod_count INT;
    order_count INT;
BEGIN
    SELECT COUNT(*) INTO cust_count FROM customers;
    SELECT COUNT(*) INTO prod_count FROM products;
    SELECT COUNT(*) INTO order_count FROM orders;
    RAISE NOTICE 'Database Seed Complete: % customers, % products, % orders.', cust_count, prod_count, order_count;
END $$;
