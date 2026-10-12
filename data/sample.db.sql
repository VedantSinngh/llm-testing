-- Sample database schema and seed data for Text-to-SQL evaluations

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Seed sample records
INSERT OR IGNORE INTO customers (id, name, email, country) VALUES
(1, 'Alice Johnson', 'alice@example.com', 'USA'),
(2, 'Bob Smith', 'bob@example.com', 'UK'),
(3, 'Charlie Lee', 'charlie@example.com', 'Canada');

INSERT OR IGNORE INTO products (id, name, category, price, stock) VALUES
(1, 'Wireless Mouse', 'Electronics', 29.99, 150),
(2, 'Mechanical Keyboard', 'Electronics', 89.99, 45),
(3, 'Coffee Mug', 'Kitchenware', 12.50, 200);

INSERT OR IGNORE INTO orders (id, customer_id, product_id, quantity, total_price, order_date) VALUES
(1, 1, 1, 2, 59.98, '2025-01-15'),
(2, 2, 2, 1, 89.99, '2025-01-16'),
(3, 3, 3, 4, 50.00, '2025-01-17');
