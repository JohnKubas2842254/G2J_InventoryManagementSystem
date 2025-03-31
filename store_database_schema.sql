-- G2J Store Inventory Management System Database Schema
-- Updated Date: 2025-03-31

-- Create the database
CREATE DATABASE IF NOT EXISTS store_inventory;
USE store_inventory;

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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create sales table to track daily sales
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create reorders table
CREATE TABLE IF NOT EXISTS reorders (
    reorder_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    date_requested DATETIME NOT NULL,
    date_received DATETIME NULL,
    status ENUM('PENDING', 'ORDERED', 'RECEIVED', 'CANCELED') NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert some sample product data
INSERT INTO products (upc, product_name, description, category, current_quantity, reorder_point, reorder_quantity, unit_price)
VALUES
    ('123456789012', 'Milk (1 gallon)', 'Whole milk, 1 gallon', 'Dairy', 50, 15, 30, 3.99),
    ('234567890123', 'Bread (White)', 'White bread loaf', 'Bakery', 35, 10, 25, 2.49),
    ('345678901234', 'Eggs (dozen)', 'Large eggs, 1 dozen', 'Dairy', 20, 8, 20, 3.29),
    ('456789012345', 'Bananas', 'Bananas, per pound', 'Produce', 45, 15, 30, 0.59),
    ('567890123456', 'Ground Beef', 'Ground beef, per pound', 'Meat', 12, 5, 15, 4.99),
    ('678901234567', 'Chicken Breast', 'Chicken breast, per pound', 'Meat', 18, 7, 20, 3.99),
    ('789012345678', 'Pasta (1 lb)', 'Spaghetti, 1 pound box', 'Dry Goods', 40, 12, 30, 1.29),
    ('890123456789', 'Tomato Sauce', 'Tomato sauce, 24 oz jar', 'Canned Goods', 25, 8, 20, 1.99);