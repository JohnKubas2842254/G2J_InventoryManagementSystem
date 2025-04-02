#!/usr/bin/env python3
"""
G2J Inventory Management System - GUI Application

This script provides a graphical user interface for the G2J Inventory
Management System, allowing users to search for products, update
product configurations, and view reports.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pymysql #type: ignore
import re

# Application Constants
APP_TITLE = "G2J Inventory Management System"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "2842254K",
    "database": "G2J_InventoryManagement",
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
        
        # Connect to database
        self.db_connection = self.connect_to_database()
        
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
        
    def get_reports(self):
        """Retrieve reports from the database."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "No database connection available.")
            return []
        
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT report_name AS name, report_date AS date, report_file AS file FROM reports")
                reports = cursor.fetchall()
                return reports
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error retrieving reports: {e}")
            return []
        
    def search_product(self, search_term):
        """Search for products by UPC or name."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "No database connection available.")
            return []
        
        try:
            with self.db_connection.cursor() as cursor:
                # Search for products by UPC or name
                query = """
                    SELECT product_id, upc, product_name, description, current_quantity, 
                           category, case_size, unit_price
                    FROM products 
                    WHERE upc LIKE %s OR product_name LIKE %s
                """
                cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
                products = cursor.fetchall()
                
                # Debug: Print the results to the terminal
                print(f"Search results for '{search_term}': \n {products}")
                
                return products
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error searching for products: {e}")
            return []
        
    def update_product(self, product_id, product_data):
        """Update product details in the database."""
        if not self.db_connection:
            messagebox.showerror("Database Error", "No database connection available.")
            return False
        
        try:
            with self.db_connection.cursor() as cursor:
                # Prepare SQL update statement
                sql = """
                    UPDATE products 
                    SET product_name = %s, description = %s, category = %s, 
                        current_quantity = %s, case_size = %s, unit_price = %s 
                    WHERE product_id = %s
                """
                cursor.execute(sql, (
                    product_data["product_name"],
                    product_data["description"],
                    product_data["category"],
                    product_data["current_quantity"],
                    product_data["case_size"],
                    product_data["unit_price"],
                    product_id
                ))
                self.db_connection.commit()
                return True
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error updating product: {e}")
            return False


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
        
        # Recent products section (this should be populated from the database)
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
        
        # Pack the treeview
        self.products_tree.pack(fill=tk.BOTH, expand=True)

        
        # Bind double-click event to open product configuration
        self.products_tree.bind("<Double-1>", self.open_product_config)
        
        # Load recent products when showing this frame
        self.load_recent_products()

        # Add "Enter New Item" button
        new_item_button = ttk.Button(self, text="Enter New Item", command=self.open_new_item_window)
        new_item_button.pack(pady=(10, 0))  # Add some padding below the button

    def open_new_item_window(self):
        """Open a window to add a new product."""
        NewItemWindow(self.controller)
        
    
    def on_show(self):
        """Called when this frame is shown."""
        # Refresh the products list
        self.load_recent_products()
    
    def search_product(self):
        """Search for products and display matching results."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showinfo("Search", "Please enter a UPC or product name")
            return
        
        # Call controller's search method
        products = self.controller.search_product(search_term)
        
        if not products:
            messagebox.showinfo("Search", "No products found matching the search term")
            return
        
        if len(products) == 1:
            # If only one product is found, navigate directly to the configuration frame
            print("Only one product found. Navigating to configuration frame.")
            self.open_product_config(products[0])
        else:
            # If multiple products are found, show a selection popup
            print(f"Multiple products found: {len(products)}. Showing selection popup.")
            self.show_product_selection_popup(products)
    
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
    
    def show_product_selection_popup(self, products):
        """Show a popup window to select a product from the search results."""
        popup = tk.Toplevel(self)
        popup.title("Select a Product")
        popup.geometry("600x400")  # Set a larger default size for the popup window
        
        # Add a label
        label = ttk.Label(popup, text="Select a product from the list below:")
        label.pack(pady=10)
        
        # Create a treeview to display the products
        tree = ttk.Treeview(popup, columns=("ID", "UPC", "Name", "Quantity"), show="headings", height=10)
        tree.heading("ID", text="ID")
        tree.heading("UPC", text="UPC")
        tree.heading("Name", text="Product Name")
        tree.heading("Quantity", text="Quantity")
        
        tree.column("ID", width=50)
        tree.column("UPC", width=100)
        tree.column("Name", width=300)
        tree.column("Quantity", width=100)
        
        # Add products to the treeview
        for product in products:
            tree.insert("", "end", values=(
                product["product_id"],
                product["upc"],
                product["product_name"],
                product["current_quantity"]
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a button to confirm selection
        select_button = ttk.Button(popup, text="Select", command=lambda: self.select_product_from_popup(tree, popup))
        select_button.pack(pady=10)

    def select_product_from_popup(self, tree, popup):
        """Handle product selection from the popup."""
        # Get the selected item
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a product")
            return
        
        # Get product data from the selected item
        item = tree.item(selection[0])
        product_id = item["values"][0]  # Get the product ID from the selected row
        
        # Retrieve the full product data using the product ID
        try:
            with self.controller.db_connection.cursor() as cursor:
                query = """
                    SELECT product_id, upc, product_name, description, current_quantity, 
                           category, case_size, unit_price
                    FROM products 
                    WHERE product_id = %s
                """
                cursor.execute(query, (product_id,))
                product = cursor.fetchone()
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error retrieving product: {e}")
            return
        
        if product:
            # Open the product configuration frame
            self.open_product_config(product)
        
        # Close the popup
        popup.destroy()

    def open_product_config(self, product):
        """Open the configuration screen for the selected product."""
        config_frame = self.controller.frames["ConfigurationFrame"]
        config_frame.load_product(product)
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
        
        # Case Size
        case_size_frame = ttk.Frame(self.product_frame)
        case_size_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(case_size_frame, text="Case Size:", width=15).pack(side=tk.LEFT)
        self.case_size_var = tk.StringVar()
        ttk.Entry(case_size_frame, textvariable=self.case_size_var, width=10).pack(side=tk.LEFT)
        
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
        self.case_size_var.set(product["case_size"])
        self.price_var.set(product["unit_price"])
    
    def save_product(self):
        """Save the product changes to the database."""
        if not self.current_product:
            return
            
        # Validate inputs
        try:
            current_quantity = int(self.qty_var.get())
            case_size = int(self.case_size_var.get())
            unit_price = float(self.price_var.get())
            
            if current_quantity < 0 or case_size < 1 or unit_price < 0:
                raise ValueError("Values cannot be negative and case size must be at least 1")
                
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid numeric input: {e}")
            return
            
        # Prepare data for update
        product_data = {
            "product_name": self.name_var.get(),
            "description": self.desc_text.get("1.0", tk.END).strip(),
            "category": self.category_var.get(),
            "current_quantity": current_quantity,
            "case_size": case_size,
            "unit_price": unit_price
        }
        
        # Update product
        success = self.controller.update_product(self.current_product["product_id"], product_data)
        
        if success:
            messagebox.showinfo("Success", "Product updated successfully")
            # Update the current product with new values
            self.current_product.update(product_data)


class ReportsFrame(ttk.Frame):
    """Reports viewing frame."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure the frame
        self.configure(padding="20", style="TFrame")
        
        # Create header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        back_button = ttk.Button(header_frame, text="← Back", 
                                command=lambda: controller.show_frame("DashboardFrame"))
        back_button.pack(side=tk.LEFT)
        
        header_label = ttk.Label(header_frame, text="Reports",
                                style="Header.TLabel")
        header_label.pack(side=tk.LEFT, padx=20)
        
        # Reports list frame
        reports_frame = ttk.Frame(self)
        reports_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a treeview to display reports
        self.reports_tree = ttk.Treeview(reports_frame, 
                                        columns=("Name", "Date"), 
                                        show="headings", 
                                        height=10)
        
        # Define headings
        self.reports_tree.heading("Name", text="Report Name")
        self.reports_tree.heading("Date", text="Date")
        
        # Configure columns
        self.reports_tree.column("Name", width=400)
        self.reports_tree.column("Date", width=150)
        
        # Add scrollbar
        reports_scrollbar = ttk.Scrollbar(reports_frame, orient="vertical", 
                                        command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=reports_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.reports_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reports_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event to view report
        self.reports_tree.bind("<Double-1>", self.view_report)
        
        # Action buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        view_button = ttk.Button(buttons_frame, text="View Report", 
                               command=self.view_selected_report)
        view_button.pack(side=tk.RIGHT)
        
        # Load reports when showing this frame
        self.load_reports()
    
    def on_show(self):
        """Called when this frame is shown."""
        # Refresh the reports list
        self.load_reports()
    
    def load_reports(self):
        """Load reports into the treeview."""
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        # Get reports from controller
        reports = self.controller.get_reports()
        
        # Add reports to treeview
        for report in reports:
            self.reports_tree.insert("", "end", values=(
                report["name"],
                report["date"]
            ), tags=(report["file"],))
    
    def view_selected_report(self):
        """View the selected report."""
        # Get selected item
        selection = self.reports_tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a report to view")
            return
            
        # Get the report file
        item = self.reports_tree.item(selection[0])
        report_file = self.reports_tree.item(selection[0], "tags")[0]
        
        # View the report
        self.view_report_file(report_file)
    
    def view_report(self, event):
        """Handle double-click on a report item."""
        selection = self.reports_tree.selection()
        if not selection:
            return
            
        # Get the report file
        report_file = self.reports_tree.item(selection[0], "tags")[0]
        
        # View the report
        self.view_report_file(report_file)
    
    def view_report_file(self, report_file):
        """Open a window to display the report content."""
        try:
            # Check if the file exists
            if os.path.exists(report_file):
                with open(report_file, "r") as f:
                    content = f.read()
            else:
                # For demo purposes, create sample content
                content = f"This is a sample {report_file} content.\n\n"
                content += "Generated on: 2025-03-31\n\n"
                
                if "inventory" in report_file.lower():
                    content += "Inventory Status:\n"
                    content += "----------------\n"
                    content += "1. Milk (1 gallon) - 50 units\n"
                    content += "2. Bread (White) - 35 units\n"
                    content += "3. Eggs (dozen) - 20 units\n"
                    content += "4. Bananas - 45 units\n"
                    content += "5. Ground Beef - 12 units\n"
                    content += "6. Chicken Breast - 18 units\n"
                    content += "7. Pasta (1 lb) - 40 units\n"
                    content += "8. Tomato Sauce - 25 units\n"
                elif "reorder" in report_file.lower():
                    content += "Items to Reorder:\n"
                    content += "----------------\n"
                    content += "1. Ground Beef - Current: 12, Case Size: 15\n"
                    content += "2. Chicken Breast - Current: 18, Case Size: 20\n"
                else:
                    content += "Sales Summary:\n"
                    content += "-------------\n"
                    content += "1. Milk (1 gallon) - 20 units sold\n"
                    content += "2. Bread (White) - 15 units sold\n"
                    content += "3. Eggs (dozen) - 10 units sold\n"
                    content += "4. Bananas - 30 units sold\n"
            
            # Create a new window
            report_window = tk.Toplevel(self)
            report_window.title(f"Report: {report_file}")
            report_window.geometry("600x400")
            
            # Add a text widget to display the content
            text_widget = tk.Text(report_window, wrap="word", padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(text_widget, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Insert content
            text_widget.insert("1.0", content)
            text_widget.configure(state="disabled")  # Make it read-only
            
        except Exception as e:
            messagebox.showerror("Error", f"Error viewing report: {e}")

class NewItemWindow(tk.Toplevel):
    """Window for entering a new product into the database."""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Enter New Item")
        self.geometry("400x400")
        
        # Create input fields for product details
        ttk.Label(self, text="UPC:").pack(pady=5, anchor=tk.W)
        self.upc_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.upc_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Product Name:").pack(pady=5, anchor=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Description:").pack(pady=5, anchor=tk.W)
        self.desc_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.desc_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Category:").pack(pady=5, anchor=tk.W)
        self.category_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.category_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Current Quantity:").pack(pady=5, anchor=tk.W)
        self.qty_var = tk.IntVar()
        ttk.Entry(self, textvariable=self.qty_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Case Size:").pack(pady=5, anchor=tk.W)
        self.case_size_var = tk.IntVar(value=1)  # Default case size is 1
        ttk.Entry(self, textvariable=self.case_size_var).pack(fill=tk.X, padx=10)
        
        ttk.Label(self, text="Unit Price ($):").pack(pady=5, anchor=tk.W)
        self.price_var = tk.DoubleVar()
        ttk.Entry(self, textvariable=self.price_var).pack(fill=tk.X, padx=10)
        
        # Add Save button
        save_button = ttk.Button(self, text="Save", command=self.save_new_item)
        save_button.pack(pady=20)
    
    def save_new_item(self):
        """Save the new product to the database."""
        # Get input values
        product_data = {
            "upc": self.upc_var.get(),
            "product_name": self.name_var.get(),
            "description": self.desc_var.get(),
            "category": self.category_var.get(),
            "current_quantity": self.qty_var.get(),
            "case_size": self.case_size_var.get(),
            "unit_price": self.price_var.get()
        }
        
        # Validate inputs
        if not product_data["upc"] or not product_data["product_name"]:
            messagebox.showerror("Input Error", "UPC and Product Name are required.")
            return
        
        if product_data["case_size"] < 1:
            messagebox.showerror("Input Error", "Case size must be at least 1.")
            return
        
        try:
            with self.controller.db_connection.cursor() as cursor:
                # Insert the new product into the database
                query = """
                    INSERT INTO products (upc, product_name, description, category, 
                                          current_quantity, case_size, unit_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    product_data["upc"],
                    product_data["product_name"],
                    product_data["description"],
                    product_data["category"],
                    product_data["current_quantity"],
                    product_data["case_size"],
                    product_data["unit_price"]
                ))
                self.controller.db_connection.commit()
                messagebox.showinfo("Success", "New product added successfully.")
                self.destroy()  # Close the window
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error adding product: {e}")

# Run the application if this script is executed directly
if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()