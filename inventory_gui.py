#!/usr/bin/env python3
"""
G2J Inventory Management System - GUI Application
Date: 2025-03-31

This script provides a graphical user interface for the G2J Inventory
Management System, allowing users to search for products, update
product configurations, and view reports.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pymysql
import re

# Application Constants
APP_TITLE = "G2J Inventory Management System"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
DB_CONFIG = {
    "host": "localhost",
    "user": "store_user",
    "password": "store_password",
    "database": "store_inventory",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

class InventoryApp(tk.Tk):
    """Main application class for the G2J Inventory Management System GUI."""
    
    def __init__(self):
        super().__init__()
        
        # Configure the main window
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(True, True)
        
        # Set app icon if available
        try:
            self.iconbitmap("assets/icon.ico")
        except:
            pass
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use 'clam' theme
        
        # Configure colors
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", 
                             background="#4a7abc", 
                             foreground="white", 
                             font=('Arial', 10, 'bold'),
                             borderwidth=0)
        self.style.map('TButton', 
                       background=[('active', '#5a8acc')],
                       foreground=[('active', 'white')])
        self.style.configure("TLabel", 
                             background="#f0f0f0", 
                             font=('Arial', 10))
        self.style.configure("Header.TLabel", 
                             font=('Arial', 16, 'bold'), 
                             background="#f0f0f0")
        self.style.configure("Subheader.TLabel", 
                             font=('Arial', 12, 'bold'), 
                             background="#f0f0f0")
        
        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize frames dictionary
        self.frames = {}
        
        # Create and add frames for different screens
        for F in (DashboardFrame, ConfigurationFrame, ReportsFrame):
            frame = F(self.main_container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure the main container's grid
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Show dashboard by default
        self.show_frame("DashboardFrame")
        
        # Connect to database
        self.db_connection = self.connect_to_database()
    
    def show_frame(self, frame_name):
        """Switch to the specified frame."""
        frame = self.frames[frame_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()
    
    def connect_to_database(self):
        """Establish a connection to the MySQL database."""
        try:
            connection = pymysql.connect(**DB_CONFIG)
            print("Successfully connected to the database.")
            return connection
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Connection Error", 
                                f"Error connecting to the database: {e}")
            return None
    
    def search_product(self, search_term):
        """Search for a product in the database."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "Not connected to database")
            return None
        
        try:
            with self.db_connection.cursor() as cursor:
                # Try to match UPC first
                cursor.execute(
                    "SELECT * FROM products WHERE upc = %s OR product_name LIKE %s LIMIT 1", 
                    (search_term, f"%{search_term}%")
                )
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error searching for product: {e}")
            return None
    
    def get_product(self, product_id):
        """Get a product by its ID."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "Not connected to database")
            return None
            
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error retrieving product: {e}")
            return None
    
    def update_product(self, product_id, data):
        """Update product information in the database."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "Not connected to database")
            return False
            
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                UPDATE products 
                SET product_name = %s, description = %s, category = %s,
                    current_quantity = %s, reorder_point = %s, 
                    reorder_quantity = %s, unit_price = %s
                WHERE product_id = %s
                """
                cursor.execute(query, (
                    data['product_name'], 
                    data['description'], 
                    data['category'],
                    data['current_quantity'], 
                    data['reorder_point'], 
                    data['reorder_quantity'], 
                    data['unit_price'],
                    product_id
                ))
                self.db_connection.commit()
                return True
        except pymysql.MySQLError as e:
            self.db_connection.rollback()
            messagebox.showerror("Database Error", f"Error updating product: {e}")
            return False
    
    def get_reports(self):
        """Get a list of available reports."""
        # In a real application, this would retrieve reports from a directory or database
        # For now, let's simulate some reports
        return [
            {"name": "Inventory Report", "date": "2025-03-31", "file": "inventory_report.txt"},
            {"name": "Reorder Report", "date": "2025-03-31", "file": "reorder_report.txt"},
            {"name": "Sales Report", "date": "2025-03-30", "file": "sales_report.txt"}
        ]


class DashboardFrame(ttk.Frame):
    """Dashboard Frame with search functionality."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure the frame
        self.configure(padding="20", style="TFrame")
        
        # Create header
        header_label = ttk.Label(self, text="G2J Inventory Management System",
                                style="Header.TLabel")
        header_label.pack(pady=(0, 20))
        
        # Search section
        search_frame = ttk.Frame(self)
        search_frame.pack(pady=(0, 30), fill=tk.X)
        
        search_label = ttk.Label(search_frame, 
                                text="Search for a product by UPC or name:",
                                style="Subheader.TLabel")
        search_label.pack(anchor=tk.W, pady=(0, 5))
        
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X)
        
        self.search_entry = ttk.Entry(search_input_frame, width=40, font=('Arial', 12))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        search_button = ttk.Button(search_input_frame, text="Search", 
                                  command=self.search_product)
        search_button.pack(side=tk.LEFT)
        
        # Bind Enter key to search_product function
        self.search_entry.bind("<Return>", lambda event: self.search_product())
        
        # Quick actions section
        actions_frame = ttk.Frame(self)
        actions_frame.pack(pady=(20, 0), fill=tk.BOTH, expand=True)
        
        actions_label = ttk.Label(actions_frame, 
                                 text="Quick Actions:",
                                 style="Subheader.TLabel")
        actions_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create a frame for buttons
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Reports button
        reports_button = ttk.Button(buttons_frame, 
                                   text="View Reports", 
                                   command=lambda: controller.show_frame("ReportsFrame"))
        reports_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Recent products section (this could be populated from the database)
        products_label = ttk.Label(self, text="Recent Products:",
                                  style="Subheader.TLabel")
        products_label.pack(anchor=tk.W, pady=(20, 10))
        
        # Create a treeview to display recent products
        self.products_tree = ttk.Treeview(self, columns=("ID", "UPC", "Name", "Quantity"), 
                                         show="headings", height=10)
        
        # Define headings
        self.products_tree.heading("ID", text="ID")
        self.products_tree.heading("UPC", text="UPC")
        self.products_tree.heading("Name", text="Product Name")
        self.products_tree.heading("Quantity", text="Quantity")
        
        # Configure columns
        self.products_tree.column("ID", width=50)
        self.products_tree.column("UPC", width=150)
        self.products_tree.column("Name", width=400)
        self.products_tree.column("Quantity", width=100)
        
        # Add scrollbar
        products_scrollbar = ttk.Scrollbar(self, orient="vertical", 
                                          command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.products_tree.pack(fill=tk.BOTH, expand=True)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event to open product configuration
        self.products_tree.bind("<Double-1>", self.open_product_config)
        
        # Load recent products when showing this frame
        self.load_recent_products()
    
    def on_show(self):
        """Called when this frame is shown."""
        # Refresh the products list
        self.load_recent_products()
    
    def search_product(self):
        """Search for a product and navigate to configuration screen if found."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showinfo("Search", "Please enter a UPC or product name")
            return
        
        # Call controller's search method
        product = self.controller.search_product(search_term)
        
        if product:
            # Set the current product in the configuration frame
            config_frame = self.controller.frames["ConfigurationFrame"]
            config_frame.load_product(product)
            
            # Show the configuration frame
            self.controller.show_frame("ConfigurationFrame")
        else:
            messagebox.showinfo("Search", "No product found with that UPC or name")
    
    def load_recent_products(self):
        """Load recent products into the treeview."""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Get recent products from database
        if not self.controller.db_connection:
            return
            
        try:
            with self.controller.db_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT product_id, upc, product_name, current_quantity FROM products "
                    "ORDER BY updated_at DESC LIMIT 10"
                )
                products = cursor.fetchall()
                
                # Add products to treeview
                for product in products:
                    self.products_tree.insert("", "end", values=(
                        product["product_id"],
                        product["upc"],
                        product["product_name"],
                        product["current_quantity"]
                    ))
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error loading products: {e}")
    
    def open_product_config(self, event):
        """Open the configuration screen for the selected product."""
        # Get selected item
        selection = self.products_tree.selection()
        if not selection:
            return
            
        # Get product ID from the selected item
        item = self.products_tree.item(selection[0])
        product_id = item["values"][0]
        
        # Get the product data
        product = self.controller.get_product(product_id)
        if product:
            # Set the product in the configuration frame
            config_frame = self.controller.frames["ConfigurationFrame"]
            config_frame.load_product(product)
            
            # Show the configuration frame
            self.controller.show_frame("ConfigurationFrame")


class ConfigurationFrame(ttk.Frame):
    """Product configuration frame."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_product = None
        
        # Configure the frame
        self.configure(padding="20", style="TFrame")
        
        # Create header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        back_button = ttk.Button(header_frame, text="← Back", 
                                command=lambda: controller.show_frame("DashboardFrame"))
        back_button.pack(side=tk.LEFT)
        
        header_label = ttk.Label(header_frame, text="Product Configuration",
                                style="Header.TLabel")
        header_label.pack(side=tk.LEFT, padx=20)
        
        # Product info frame
        self.product_frame = ttk.Frame(self)
        self.product_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create input fields with labels
        # Product ID (read-only)
        id_frame = ttk.Frame(self.product_frame)
        id_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(id_frame, text="Product ID:", width=15).pack(side=tk.LEFT)
        self.id_var = tk.StringVar()
        ttk.Entry(id_frame, textvariable=self.id_var, state="readonly", width=30).pack(side=tk.LEFT)
        
        # UPC/Barcode (read-only)
        upc_frame = ttk.Frame(self.product_frame)
        upc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(upc_frame, text="UPC:", width=15).pack(side=tk.LEFT)
        self.upc_var = tk.StringVar()
        ttk.Entry(upc_frame, textvariable=self.upc_var, state="readonly", width=30).pack(side=tk.LEFT)
        
        # Product Name
        name_frame = ttk.Frame(self.product_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Product Name:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=50).pack(side=tk.LEFT)
        
        # Description
        desc_frame = ttk.Frame(self.product_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(desc_frame, text="Description:", width=15).pack(side=tk.LEFT, anchor=tk.N)
        self.desc_text = tk.Text(desc_frame, height=3, width=50)
        self.desc_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Category
        category_frame = ttk.Frame(self.product_frame)
        category_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(category_frame, text="Category:", width=15).pack(side=tk.LEFT)
        self.category_var = tk.StringVar()
        ttk.Entry(category_frame, textvariable=self.category_var, width=30).pack(side=tk.LEFT)
        
        # Current Quantity
        qty_frame = ttk.Frame(self.product_frame)
        qty_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(qty_frame, text="Current Quantity:", width=15).pack(side=tk.LEFT)
        self.qty_var = tk.StringVar()
        ttk.Entry(qty_frame, textvariable=self.qty_var, width=10).pack(side=tk.LEFT)
        
        # Reorder Point
        reorder_point_frame = ttk.Frame(self.product_frame)
        reorder_point_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(reorder_point_frame, text="Reorder Point:", width=15).pack(side=tk.LEFT)
        self.reorder_point_var = tk.StringVar()
        ttk.Entry(reorder_point_frame, textvariable=self.reorder_point_var, width=10).pack(side=tk.LEFT)
        
        # Reorder Quantity
        reorder_qty_frame = ttk.Frame(self.product_frame)
        reorder_qty_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(reorder_qty_frame, text="Reorder Quantity:", width=15).pack(side=tk.LEFT)
        self.reorder_qty_var = tk.StringVar()
        ttk.Entry(reorder_qty_frame, textvariable=self.reorder_qty_var, width=10).pack(side=tk.LEFT)
        
        # Unit Price
        price_frame = ttk.Frame(self.product_frame)
        price_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(price_frame, text="Unit Price ($):", width=15).pack(side=tk.LEFT)
        self.price_var = tk.StringVar()
        ttk.Entry(price_frame, textvariable=self.price_var, width=10).pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.save_button = ttk.Button(buttons_frame, text="Save Changes", 
                                     command=self.save_product)
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0))
    
    def load_product(self, product):
        """Load product data into the form."""
        self.current_product = product
        
        # Set form values
        self.id_var.set(product["product_id"])
        self.upc_var.set(product["upc"])
        self.name_var.set(product["product_name"])
        
        # Clear and set description text
        self.desc_text.delete("1.0", tk.END)
        if product["description"]:
            self.desc_text.insert("1.0", product["description"])
            
        self.category_var.set(product["category"] or "")
        self.qty_var.set(product["current_quantity"])
        self.reorder_point_var.set(product["reorder_point"])
        self.reorder_qty_var.set(product["reorder_quantity"])
        self.price_var.set(product["unit_price"])
    
    def save_product(self):
        """Save the product changes to the database."""
        if not self.current_product:
            return
            
        # Validate inputs
        try:
            current_quantity = int(self.qty_var.get())
            reorder_point = int(self.reorder_point_var.get())
            reorder_quantity = int(self.reorder_qty_var.get())
            unit_price = float(self.price_var.get())
            
            if current_quantity < 0 or reorder_point < 0 or reorder_quantity < 0 or unit_price < 0:
                raise ValueError("Values cannot be negative")
                
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid numeric input: {e}")
            return
            
        # Prepare data for update
        product_data = {
            "product_name": self.name_var.get(),
            "description": self.desc_text.get("1.0", tk.END).strip(),
            "category": self.category_var.get(),
            "current_quantity": current_quantity,
            "reorder_point": reorder_point,
            "reorder_quantity": reorder_quantity,
            "unit_price": unit_price
        }
        
        # Update product
        success = self.controller.update_product(self.current_product["product_id"], product_data)
        
        if success:
            messagebox.showinfo("Success", "Product updated successfully")
            # Update the current product with new