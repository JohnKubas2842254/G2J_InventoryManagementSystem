#!/usr/bin/env python3
"""
G2J Inventory Management System - Store Reorder Generator

This script processes sales data from an input.txt file (one UPC code per line),
updates the store's inventory levels, and generates a reorder list for
products when the number of units sold reaches a multiple of the case size.

Usage:
    python reorder_generator.py [input_file]
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
    Check current inventory levels against sales data to determine what needs reordering
    based on case size logic.
    
    Args:
        connection: Database connection
        sales_data (Counter): Dictionary with UPC codes and quantities sold
        
    Returns:
        list: Items that need to be reordered with their details
    """
    reorder_list = []
    products_with_cases_consumed = {}
    
    try:
        with connection.cursor() as cursor:
            for upc, quantity_sold in sales_data.items():
                # Get product info from database
                cursor.execute(
                    "SELECT product_id, product_name, current_quantity, case_size FROM products WHERE upc = %s", 
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
                    
                    # Check if the number of units sold is a multiple of case size
                    if product['case_size'] > 0 and quantity_sold % product['case_size'] == 0:
                        cases_consumed = quantity_sold // product['case_size']
                        
                        # Only add to reorder list if at least one full case was consumed
                        if cases_consumed > 0:
                            # We'll track the number of cases consumed for this product
                            if product['product_id'] in products_with_cases_consumed:
                                products_with_cases_consumed[product['product_id']]['cases_consumed'] += cases_consumed
                            else:
                                products_with_cases_consumed[product['product_id']] = {
                                    'product_id': product['product_id'],
                                    'upc': upc,
                                    'product_name': product['product_name'],
                                    'current_quantity': new_quantity,
                                    'case_size': product['case_size'],
                                    'cases_consumed': cases_consumed
                                }
                else:
                    print(f"Warning: Product with UPC {upc} not found in database.")
            
            # Add all products that had at least one full case consumed to the reorder list
            reorder_list = list(products_with_cases_consumed.values())
            
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
    For each case consumed, output the UPC once.
    
    Args:
        reorder_list (list): Items that need to be reordered
        output_file (str): Path to the output file
    """
    if not reorder_list:
        print("No items need to be reordered.")
        with open(output_file, 'w') as file:
            file.write("No items need to be reordered.\n")
        return
    
    try:
        with open(output_file, 'w') as file:
            for item in reorder_list:
                upc = item['upc']
                cases_consumed = item['cases_consumed']
                
                # Write one line per case consumed
                for _ in range(cases_consumed):
                    file.write(f"{upc}\n")
        
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
                # Create a reorder record in the database based on cases consumed
                quantity_to_order = item['cases_consumed'] * item['case_size']
                
                cursor.execute(
                    "INSERT INTO reorders (product_id, quantity, date_requested, status) "
                    "VALUES (%s, %s, %s, %s)",
                    (item['product_id'], quantity_to_order, current_date, 'PENDING')
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
    if len(sys.argv) != 2:
        print("Usage: python reorder_generator.py [input_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    output_files_directory = "/Users/kube/VSprojects/G2J_InventoryManagementSystem/ReOrder_Lists"
    os.makedirs(output_files_directory, exist_ok=True)
    # Generate the output file name based on the current date and time
    current_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    output_file = os.path.join(output_files_directory, f"reorder_list_{current_time}.txt")
    
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