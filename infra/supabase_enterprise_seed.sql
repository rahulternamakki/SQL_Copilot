-- ==============================================================================
-- GOVERNED AI DATABASE COPILOT - ENTERPRISE SUPABASE TEST DATASET
-- Database Schema: Enterprise E-Commerce & Retail Operations
-- Instructions: Copy and paste this entire script into your Supabase SQL Editor
-- ==============================================================================

-- 1. Clean up old tables if re-running
DROP TABLE IF EXISTS support_tickets CASCADE;
DROP TABLE IF EXISTS refunds CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ==============================================================================
-- TABLE DEFINITIONS
-- ==============================================================================

-- 1. Customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    country VARCHAR(50) NOT NULL DEFAULT 'USA',
    city VARCHAR(50),
    signup_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'churned', 'vip')),
    loyalty_tier VARCHAR(20) NOT NULL DEFAULT 'bronze' CHECK (loyalty_tier IN ('bronze', 'silver', 'gold', 'platinum')),
    total_spend NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Employees (Sales & Support Reps)
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL CHECK (department IN ('Sales', 'Support', 'Logistics', 'Management')),
    region VARCHAR(50) NOT NULL DEFAULT 'North America',
    hire_date DATE NOT NULL,
    salary NUMERIC(10, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Product Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    margin_target_percent NUMERIC(5, 2) DEFAULT 30.00
);

-- 4. Products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    category_id INT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    cost_price NUMERIC(10, 2) NOT NULL CHECK (cost_price >= 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= cost_price),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    sales_rep_id INT REFERENCES employees(id) ON DELETE SET NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled', 'refunded')),
    payment_method VARCHAR(30) NOT NULL CHECK (payment_method IN ('Credit Card', 'PayPal', 'Wire Transfer', 'Apple Pay')),
    shipping_country VARCHAR(50) NOT NULL DEFAULT 'USA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Order Items
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_percent NUMERIC(5, 2) DEFAULT 0.00 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    line_total NUMERIC(10, 2) GENERATED ALWAYS AS (quantity * unit_price * (1.0 - (discount_percent / 100.0))) STORED
);

-- 7. Refunds
CREATE TABLE refunds (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    refund_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    reason VARCHAR(100) NOT NULL CHECK (reason IN ('Defective Item', 'Late Delivery', 'Customer Changed Mind', 'Wrong Item Sent', 'Billing Error')),
    processed_by INT REFERENCES employees(id) ON DELETE SET NULL
);

-- 8. Customer Support Tickets
CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    assigned_agent_id INT REFERENCES employees(id) ON DELETE SET NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(20) NOT NULL DEFAULT 'resolved' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    subject VARCHAR(150) NOT NULL,
    resolution_time_hours NUMERIC(6, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- DUMMY DATA POPULATION
-- ==============================================================================

-- 1. Insert Categories
INSERT INTO categories (id, name, description, margin_target_percent) VALUES
(1, 'Enterprise Electronics', 'High-end laptops, servers, and enterprise compute hardware', 35.00),
(2, 'Office Ergonomics', 'Standing desks, ergonomic chairs, and monitor arms', 45.00),
(3, 'Cloud Networking', 'Managed switches, Wi-Fi 7 access points, and rack hardware', 40.00),
(4, 'Developer Peripherals', 'Mechanical keyboards, 4K monitors, and precision mice', 50.00);

-- 2. Insert Employees
INSERT INTO employees (id, first_name, last_name, email, department, region, hire_date, salary, is_active) VALUES
(1, 'Sarah', 'Connor', 's.connor@enterprisecorp.io', 'Sales', 'North America', '2021-03-15', 95000.00, TRUE),
(2, 'Marcus', 'Vance', 'm.vance@enterprisecorp.io', 'Sales', 'Europe', '2022-01-10', 88000.00, TRUE),
(3, 'Elena', 'Rostova', 'e.rostova@enterprisecorp.io', 'Support', 'North America', '2022-06-01', 65000.00, TRUE),
(4, 'David', 'Kim', 'd.kim@enterprisecorp.io', 'Support', 'Asia-Pacific', '2023-02-20', 62000.00, TRUE),
(5, 'Rachel', 'Green', 'r.green@enterprisecorp.io', 'Management', 'Global', '2020-01-05', 135000.00, TRUE);

-- 3. Insert Customers
INSERT INTO customers (id, first_name, last_name, email, phone, country, city, signup_date, status, loyalty_tier, total_spend) VALUES
(1, 'Alice', 'Morgan', 'alice.morgan@techcorp.com', '+1-555-0101', 'USA', 'San Francisco', '2021-04-12', 'vip', 'platinum', 18450.00),
(2, 'Bob', 'Chen', 'bchen@innovate.co.uk', '+44-20-7946-0123', 'UK', 'London', '2021-08-19', 'active', 'gold', 9200.00),
(3, 'Carla', 'Gomez', 'cgomez@devstudio.es', '+34-91-123-4567', 'Spain', 'Madrid', '2022-02-14', 'active', 'silver', 4300.00),
(4, 'Derek', 'Zoolander', 'derek@fashiontech.com', '+1-555-0199', 'USA', 'New York', '2020-11-05', 'inactive', 'bronze', 1200.00),
(5, 'Evelyn', 'Reed', 'e.reed@quantumai.org', '+1-555-0144', 'USA', 'Austin', '2022-09-30', 'vip', 'platinum', 24900.00),
(6, 'Fiona', 'Gallagher', 'fiona@southside.net', '+1-555-0188', 'USA', 'Chicago', '2021-01-15', 'churned', 'bronze', 450.00),
(7, 'George', 'Clark', 'gclark@cloudstack.de', '+49-30-123456', 'Germany', 'Berlin', '2023-04-01', 'active', 'gold', 11500.00),
(8, 'Hannah', 'Abbott', 'hannah@biolabs.ca', '+1-416-555-0177', 'Canada', 'Toronto', '2022-11-20', 'active', 'silver', 5800.00),
(9, 'Ian', 'Malcolm', 'ian.chaos@dinotech.io', '+1-555-0166', 'USA', 'Seattle', '2020-05-18', 'churned', 'bronze', 890.00),
(10, 'Julia', 'Roberts', 'julia@cinemasoft.com', '+1-555-0133', 'USA', 'Los Angeles', '2023-01-10', 'active', 'gold', 8400.00);

-- 4. Insert Products
INSERT INTO products (id, sku, name, category_id, cost_price, unit_price, stock_quantity, is_discontinued) VALUES
(1, 'ELEC-SRV-01', 'Apex Titan Enterprise AI Rack Server', 1, 4200.00, 6800.00, 15, FALSE),
(2, 'ELEC-LAP-02', 'UltraBook Pro 16" OLED Workstation', 1, 1400.00, 2399.00, 45, FALSE),
(3, 'DESK-ERG-01', 'ErgoPro Motorized Bamboo Standing Desk', 2, 380.00, 799.00, 60, FALSE),
(4, 'CHAIR-ERG-02', 'Aeroflow Mesh High-Back Task Chair', 2, 240.00, 549.00, 85, FALSE),
(5, 'NET-SW-01', 'Gigabit L3 Managed 48-Port PoE Switch', 3, 550.00, 1150.00, 30, FALSE),
(6, 'NET-AP-02', 'Enterprise Wi-Fi 7 Tri-Band Access Point', 3, 180.00, 399.00, 110, FALSE),
(7, 'DEV-KB-01', 'Tactile Wireless Mechanical Pro Keyboard', 4, 75.00, 189.00, 200, FALSE),
(8, 'DEV-MON-02', '34" Curved QD-OLED 175Hz Monitor', 4, 450.00, 899.00, 40, FALSE),
(9, 'ELEC-OLD-99', 'Legacy Server Blade Gen 1 (Obsolete)', 1, 800.00, 999.00, 0, TRUE);

-- 5. Insert Orders
INSERT INTO orders (id, customer_id, sales_rep_id, order_date, total_amount, status, payment_method, shipping_country) VALUES
(101, 1, 1, '2024-01-15 10:30:00+00', 13600.00, 'completed', 'Wire Transfer', 'USA'),
(102, 2, 2, '2024-01-20 14:15:00+00', 4798.00, 'completed', 'Credit Card', 'UK'),
(103, 5, 1, '2024-02-05 09:00:00+00', 14398.00, 'completed', 'Wire Transfer', 'USA'),
(104, 3, 2, '2024-02-18 16:45:00+00', 2197.00, 'completed', 'PayPal', 'Spain'),
(105, 7, 2, '2024-03-01 11:20:00+00', 8050.00, 'completed', 'Credit Card', 'Germany'),
(106, 8, 1, '2024-03-12 13:10:00+00', 3596.00, 'completed', 'Apple Pay', 'Canada'),
(107, 10, 1, '2024-03-25 15:50:00+00', 4598.00, 'completed', 'Credit Card', 'USA'),
(108, 1, 1, '2024-04-02 08:30:00+00', 4850.00, 'completed', 'Wire Transfer', 'USA'),
(109, 4, NULL, '2021-08-10 12:00:00+00', 1200.00, 'completed', 'Credit Card', 'USA'),
(110, 6, NULL, '2021-05-22 14:30:00+00', 450.00, 'refunded', 'PayPal', 'USA');

-- 6. Insert Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent) VALUES
(101, 1, 2, 6800.00, 0.00),
(102, 2, 2, 2399.00, 0.00),
(103, 1, 2, 6800.00, 5.00),
(103, 4, 2, 549.00, 10.00),
(104, 3, 2, 799.00, 0.00),
(104, 7, 3, 189.00, 0.00),
(105, 5, 7, 1150.00, 0.00),
(106, 8, 4, 899.00, 0.00),
(107, 2, 1, 2399.00, 0.00),
(107, 8, 2, 899.00, 0.00),
(107, 7, 2, 189.00, 0.00),
(108, 1, 1, 6800.00, 0.00),
(109, 3, 1, 799.00, 0.00),
(110, 7, 2, 189.00, 0.00);

-- 7. Insert Refunds
INSERT INTO refunds (order_id, refund_date, amount, reason, processed_by) VALUES
(110, '2021-05-25 10:00:00+00', 378.00, 'Customer Changed Mind', 3);

-- 8. Insert Support Tickets
INSERT INTO support_tickets (customer_id, assigned_agent_id, priority, status, subject, resolution_time_hours) VALUES
(1, 3, 'urgent', 'resolved', 'Firmware upgrade assistance on AI Rack Server', 1.50),
(2, 4, 'medium', 'resolved', 'Customs documentation for UK shipment', 4.25),
(5, 3, 'high', 'resolved', 'PoE switch configuration question', 2.10),
(6, 4, 'low', 'closed', 'Refund processing inquiry', 24.00),
(8, 3, 'medium', 'resolved', 'Warranty extension on OLED monitors', 3.00);

-- ==============================================================================
-- RESET AUTO-INCREMENT SEQUENCES
-- ==============================================================================
SELECT setval('customers_id_seq', (SELECT MAX(id) FROM customers));
SELECT setval('employees_id_seq', (SELECT MAX(id) FROM employees));
SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));
SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items));
SELECT setval('refunds_id_seq', (SELECT MAX(id) FROM refunds));
SELECT setval('support_tickets_id_seq', (SELECT MAX(id) FROM support_tickets));
