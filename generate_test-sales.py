#!/usr/bin/env python3
"""
G2J Inventory Management System - Inventory Viewer

This script displays the current inventory levels and reorder status.

Usage:
    python inventory_view.py

Current Date: 2025-03-31
"""

import pymysql #type: ignore
from tabulate import tabulate #type: ignore
# Configuration for database connection
DB_CONFIG = {
    "host": "localhost",
    "user": "store_user",
    "password": "store_password",
    "database": "store_inventory",
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
        exit(1)

def display_inventory(connection):
    """Display the current inventory levels and status."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT product_id, upc, product_name, current_quantity, reorder_point, "
                "reorder_quantity, unit_price FROM products ORDER BY category, product_name"
            )
            products = cursor.fetchall()
            
            if not products:
                print("No products found in inventory.")
                return
            
            # Prepare data for display
            table_data = []
            for product in products:
                # Determine status
                if product['current_quantity'] <= product['reorder_point']:
                    status = "REORDER"
                elif product['current_quantity'] <= product['reorder_point'] * 2:
                    status = "LOW"
                else:
                    status = "OK"
                
                table_data.append([
                    product['product_id'],
                    product['upc'],
                    product['product_name'],
                    product['current_quantity'],
                    product['reorder_point'],
                    product['reorder_quantity'],
                    f"${product['unit_price']:.2f}",
                    status
                ])
            
            # Print the table
            headers = ["ID", "UPC", "Product Name", "Quantity", "Reorder At", "Reorder Qty", "Unit Price", "Status"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Print summary
            reorder_count = sum(1 for row in table_data if row[7] == "REORDER")
            low_count = sum(1 for row in table_data if row[7] == "LOW")
            
            print(f"\nSummary: {len(products)} total products")
            print(f"         {reorder_count} products need reordering")
            print(f"         {low_count} products are running low")
            
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")

def display_pending_reorders(connection):
    """Display pending reorder requests."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT r.reorder_id, p.product_name, r.quantity, r.date_requested, r.status "
                "FROM reorders r "
                "JOIN products p ON r.product_id = p.product_id "
                "WHERE r.status = 'PENDING' "
                "ORDER BY r.date_requested"
            )
            reorders = cursor.fetchall()
            
            if not reorders:
                print("\nNo pending reorders found.")
                return
            
            print("\nPending Reorders:")
            # Prepare data for display
            table_data = []
            for reorder in reorders:
                table_data.append([
                    reorder['reorder_id'],
                    reorder['product_name'],
                    reorder['quantity'],
                    reorder['date_requested'].strftime('%Y-%m-%d %H:%M:%S'),
                    reorder['status']
                ])
            
            # Print the table
            headers = ["Reorder ID", "Product Name", "Quantity", "Date Requested", "Status"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")

def main():
    """Main function to display inventory information."""
    print("G2J Inventory Management System - Current Inventory Status")
    print("=" * 70)
    
    # Connect to the database
    connection = connect_to_database()
    
    try:
        # Display inventory status
        display_inventory(connection)
        
        # Display pending reorders
        display_pending_reorders(connection)
        
    finally:
        connection.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()