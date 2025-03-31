#!/usr/bin/env python3
"""
G2J Inventory Management System - Store Reorder Generator

This script processes sales data from an input.txt file (one UPC code per line),
updates the store's inventory levels, and generates a reorder list for
products that fall below their reorder thresholds.

Usage:
    python reorder_generator.py [input_file] [output_file]

Current Date: 2025-03-31
"""

import sys
import os
import pymysql #type: ignore
from collections import Counter
from datetime import datetime

# Configuration for database connection
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "2842254K",
    "database": "G2J_InventoryManagement",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def connect_to_database():
    """Establish a connection to the MySQL database."""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("Successfully connected to the database.")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        sys.exit(1)

def count_sales(input_file):
    """
    Read the input file and count occurrences of each UPC code.
    
    Args:
        input_file (str): Path to the input file containing one UPC per line
        
    Returns:
        Counter: Dictionary-like object with UPC codes as keys and quantities as values
    """
    try:
        with open(input_file, 'r') as file:
            # Read all lines and remove any whitespace
            upcs = [line.strip() for line in file if line.strip()]
            
        # Count occurrences of each UPC
        sales_count = Counter(upcs)
        print(f"Processed {len(upcs)} sales transactions with {len(sales_count)} unique products.")
        return sales_count
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

def check_inventory_levels(connection, sales_data):
    """
    Check current inventory levels against sales data to determine what needs reordering.
    
    Args:
        connection: Database connection
        sales_data (Counter): Dictionary with UPC codes and quantities sold
        
    Returns:
        list: Items that need to be reordered with their details
    """
    reorder_list = []
    
    try:
        with connection.cursor() as cursor:
            for upc, quantity_sold in sales_data.items():
                # Get product info from database
                cursor.execute(
                    "SELECT product_id, product_name, current_quantity, reorder_point, " 
                    "reorder_quantity FROM products WHERE upc = %s", 
                    (upc,)
                )
                product = cursor.fetchone()
                
                if product:
                    # Calculate new quantity after sales
                    new_quantity = product['current_quantity'] - quantity_sold
                    
                    # Update the inventory in the database
                    cursor.execute(
                        "UPDATE products SET current_quantity = %s WHERE product_id = %s",
                        (new_quantity, product['product_id'])
                    )
                    
                    # Check if reorder is needed
                    if new_quantity <= product['reorder_point']:
                        reorder_list.append({
                            'product_id': product['product_id'],
                            'upc': upc,
                            'product_name': product['product_name'],
                            'current_quantity': new_quantity,
                            'reorder_quantity': product['reorder_quantity']
                        })
                else:
                    print(f"Warning: Product with UPC {upc} not found in database.")
            
            # Commit the changes to the database
            connection.commit()
            
        print(f"Identified {len(reorder_list)} products that need reordering.")
        return reorder_list
    except pymysql.MySQLError as e:
        connection.rollback()
        print(f"Database error while checking inventory: {e}")
        sys.exit(1)

def generate_reorder_report(reorder_list, output_file):
    """
    Generate a reorder report and save to the output file.
    
    Args:
        reorder_list (list): Items that need to be reordered
        output_file (str): Path to the output file
    """
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if not reorder_list:
        print("No items need to be reordered.")
        with open(output_file, 'w') as file:
            file.write(f"G2J INVENTORY MANAGEMENT SYSTEM - REORDER REPORT\n")
            file.write(f"Generated on: {current_date}\n\n")
            file.write("No items need to be reordered.\n")
        return
    
    try:
        with open(output_file, 'w') as file:
            # Write header
            file.write("G2J INVENTORY MANAGEMENT SYSTEM - REORDER REPORT\n")
            file.write(f"Generated on: {current_date}\n")
            file.write(f"Store Location: Gloria, Jamison and John's Store\n\n")
            file.write("-" * 80 + "\n")
            file.write(f"{'PRODUCT ID':<12} {'UPC':<15} {'PRODUCT NAME':<30} {'CURRENT QTY':<12} {'REORDER QTY':<12}\n")
            file.write("-" * 80 + "\n")
            
            # Write each product that needs reordering
            for item in reorder_list:
                file.write(f"{item['product_id']:<12} {item['upc']:<15} {item['product_name']:<30} {item['current_quantity']:<12} {item['reorder_quantity']:<12}\n")
            
            file.write("-" * 80 + "\n")
            file.write(f"\nTotal items to reorder: {len(reorder_list)}\n")
        
        print(f"Reorder report generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating reorder report: {e}")
        sys.exit(1)

def create_reorder_records(connection, reorder_list):
    """
    Add reorder records to the database.
    
    Args:
        connection: Database connection
        reorder_list (list): Items that need to be reordered
    """
    if not reorder_list:
        return
    
    try:
        with connection.cursor() as cursor:
            current_date = datetime.now()
            for item in reorder_list:
                # Create a reorder record in the database
                cursor.execute(
                    "INSERT INTO reorders (product_id, quantity, date_requested, status) "
                    "VALUES (%s, %s, %s, %s)",
                    (item['product_id'], item['reorder_quantity'], current_date, 'PENDING')
                )
            
            # Commit the changes to the database
            connection.commit()
            
        print(f"Created {len(reorder_list)} reorder request records in the database.")
    except pymysql.MySQLError as e:
        connection.rollback()
        print(f"Database error while creating reorder records: {e}")
        sys.exit(1)

def main():
    """Main function to orchestrate the reorder generation process."""
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python reorder_generator.py [input_file] [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Starting reorder generation process...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Process the input file
    sales_data = count_sales(input_file)
    
    # Connect to the database
    connection = connect_to_database()
    
    try:
        # Check inventory levels and get items for reordering
        reorder_list = check_inventory_levels(connection, sales_data)
        
        # Create reorder records in the database
        create_reorder_records(connection, reorder_list)
        
        # Generate the reorder report
        generate_reorder_report(reorder_list, output_file)
        
        print("Reorder generation process completed successfully.")
    finally:
        connection.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()