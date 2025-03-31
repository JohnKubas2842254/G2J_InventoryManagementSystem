#!/usr/bin/env python3
"""
G2J Inventory Management System - Sales Data Generator

This script generates random sales data for testing the reorder system.

Usage:
    python generate_test_sales.py [number_of_sales] [output_file]
"""

import sys
import random
import pymysql #type: ignore

# Configuration for database connection
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "2842254K",
    "database": "G2J_InventoryManagement",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def generate_sales_data(connection, number_of_sales, output_file):
    """
    Generate random sales data for testing.
    
    Args:
        connection: Database connection
        number_of_sales (int): Number of sales transactions to generate
        output_file (str): Path to the output file
    """
    try:
        # Get all UPCs from the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT upc FROM products")
            products = cursor.fetchall()
        
        if not products:
            print("No products found in the database.")
            return
        
        # Extract UPCs
        upcs = [p['upc'] for p in products]
        
        # Generate random sales
        with open(output_file, 'w') as file:
            for _ in range(number_of_sales):
                # Select a random UPC
                upc = random.choice(upcs)
                file.write(f"{upc}\n")
        
        print(f"Generated {number_of_sales} random sales transactions in {output_file}")
        
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error generating sales data: {e}")

def main():
    """Main function to generate test sales data."""
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python generate_test_sales.py [number_of_sales] [output_file]")
        sys.exit(1)
    
    try:
        number_of_sales = int(sys.argv[1])
    except ValueError:
        print("Error: Number of sales must be an integer.")
        sys.exit(1)
    
    output_file = sys.argv[2]
    
    # Connect to the database
    try:
        connection = pymysql.connect(**DB_CONFIG)
        generate_sales_data(connection, number_of_sales, output_file)
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    main()