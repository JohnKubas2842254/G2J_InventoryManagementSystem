-- G2J Inventory Management System Database Schema

-- Create the database
CREATE DATABASE IF NOT EXISTS g2j_inventory;
USE g2j_inventory;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role ENUM('admin', 'manager', 'staff') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL,
    active BOOLEAN DEFAULT TRUE
);

-- Create suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    upc VARCHAR(20) NOT NULL UNIQUE,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    current_quantity INT NOT NULL DEFAULT 0,
    reorder_point INT NOT NULL DEFAULT 0,
    reorder_quantity INT NOT NULL DEFAULT 0,
    unit_price DECIMAL(10, 2) NOT NULL,
    supplier_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_type ENUM('sale', 'purchase', 'adjustment') NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create transaction_items table
CREATE TABLE IF NOT EXISTS transaction_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create reorder_requests table
CREATE TABLE IF NOT EXISTS reorder_requests (
    reorder_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity_requested INT NOT NULL,
    date_requested DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_fulfilled DATETIME NULL,
    status ENUM('PENDING', 'ORDERED', 'RECEIVED', 'CANCELED') NOT NULL DEFAULT 'PENDING',
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert some sample data for testing
INSERT INTO suppliers (supplier_name, contact_name, contact_email, contact_phone, address)
VALUES
    ('ABC Supplies', 'John Smith', 'jsmith@abcsupplies.com', '555-123-4567', '123 Business Ave, City, State 12345'),
    ('XYZ Corporation', 'Jane Doe', 'jdoe@xyzcorp.com', '555-987-6543', '456 Corporate Blvd, City, State 67890');

-- Insert some sample products
INSERT INTO products (upc, product_name, description, category, current_quantity, reorder_point, reorder_quantity, unit_price, supplier_id)
VALUES
    ('123456789012', 'Widget A', 'Standard widget', 'Widgets', 50, 15, 30, 9.99, 1),
    ('234567890123', 'Widget B', 'Deluxe widget', 'Widgets', 35, 10, 25, 14.99, 1),
    ('345678901234', 'Gadget C', 'Basic gadget', 'Gadgets', 20, 8, 20, 24.99, 2),
    ('456789012345', 'Gadget D', 'Premium gadget', 'Gadgets', 12, 5, 15, 39.99, 2);

-- Insert admin user (password: admin123)
INSERT INTO users (username, password_hash, full_name, email, role)
VALUES
    ('admin', '$2b$12$tRD0fY4MUQhP.N5P7ZgTfeshGiWivwlrfLg8BXgVo4MO/HGBlHcf2', 'Admin User', 'admin@g2j.com', 'admin');