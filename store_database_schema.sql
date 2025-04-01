-- G2J Store Inventory Management System Database Schema
-- Updated Date: 2025-03-31

-- Create the database
CREATE DATABASE IF NOT EXISTS G2J_InventoryManagement;
USE G2J_InventoryManagement;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    upc VARCHAR(20) NOT NULL UNIQUE,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    current_quantity INT NOT NULL DEFAULT 0,
    case_size INT NOT NULL DEFAULT 1,
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
INSERT IGNORE INTO products (upc, product_name, description, category, current_quantity, case_size, unit_price)
VALUES
    ('123456789012', 'Milk (1 gallon)', 'Whole milk, 1 gallon', 'Dairy', 50, 12, 3.99),
    ('234567890123', 'Bread (White)', 'White bread loaf', 'Bakery', 35, 10, 2.49),
    ('345678901234', 'Eggs (dozen)', 'Large eggs, 1 dozen', 'Dairy', 20, 6, 3.29),
    ('456789012345', 'Bananas', 'Bananas, per pound', 'Produce', 45, 8, 0.59),
    ('567890123456', 'Ground Beef', 'Ground beef, per pound', 'Meat', 12, 5, 4.99),
    ('678901234567', 'Chicken Breast', 'Chicken breast, per pound', 'Meat', 18, 7, 3.99),
    ('789012345678', 'Pasta (1 lb)', 'Spaghetti, 1 pound box', 'Dry Goods', 40, 12, 1.29),
    ('890123456789', 'Tomato Sauce', 'Tomato sauce, 24 oz jar', 'Canned Goods', 25, 8, 1.99),
    ('037000941514', 'Charmin Ultra-Strong Toilet Paper', '6 = 24 XL pack', 'Paper Products', 12, 6, 8.99),
    ('715141627039', 'Large Brown Eggs', 'Large brown eggs, 1 dozen', 'Dairy', 15, 5, 4.29),
    ('715141328615', 'Jumbo White Eggs', 'Jumbo white eggs, 1 dozen', 'Dairy', 18, 6, 4.49),
    ('696551750930', 'A & W Root Beer Soda 12 Pack', '12 pack cans', 'Beverages', 10, 5, 5.99),
    ('074590516654', 'Quaker Instant Oatmeal', 'Original flavor, 12 packets', 'Breakfast', 20, 8, 3.79),
    ('041457878026', 'Honey Nut Cheerios', 'Cereal, 18oz box', 'Breakfast', 25, 8, 4.29),
    ('030100062134', 'Rice Krispies Treats Bars', '8 pack', 'Snacks', 30, 10, 3.49),
    ('077567019905', 'Oreo Cookies Cream Filled Double Stuf', '10.25 Oz package', 'Snacks', 25, 8, 3.99),
    ('722252369840', 'Clif Bars Peanut Butter', '6 pack energy bars', 'Snacks', 15, 6, 6.99),
    ('785357012059', 'Peets Coffee Major Dickasons K-Cup', '10 count box', 'Coffee', 12, 4, 8.99);
