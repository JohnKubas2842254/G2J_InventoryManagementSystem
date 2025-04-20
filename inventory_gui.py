#!/usr/bin/env python3
"""
G2J Inventory Management System - GUI Application

This script provides a graphical user interface for the G2J Inventory
Management System, allowing users to search for products, update
product configurations, and view reports.
"""
import os
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pymysql #type: ignore
import subprocess
from collections import Counter

# Application Constants
APP_TITLE = "G2J Inventory Management System"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SALES_REPORTS_DIR = "/Users/kube/VSprojects/G2J_InventoryManagementSystem/SalesReports"
REORDER_LISTS_DIR = "/Users/kube/VSprojects/G2J_InventoryManagementSystem/ReOrder_Lists"

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
        for F in (DashboardFrame, ConfigurationFrame, ReportsFrame, ConfirmOrderFrame):
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

    def confirm_order_from_file(self, file_path):
        """
        Reads a file containing UPCs (one per line, each line = 1 case),
        calculates the total units received based on product case sizes,
        and updates the current_quantity in the products table.

        Args:
            file_path (str): The full path to the reorder file to process.

        Returns:
            tuple[bool, str]: (success_status, message)
        """
        if not self.db_connection:
            return False, "Database connection is not available."

        upc_counts = Counter()
        processed_count = 0
        updated_products = 0
        skipped_upcs = set()

        try:
            # --- 1. Read and count UPCs from the file ---
            with open(file_path, 'r') as f:
                for line in f:
                    upc = line.strip()
                    if upc: # Ignore empty lines
                        upc_counts[upc] += 1
                        processed_count += 1
            if not upc_counts:
                return False, f"File '{os.path.basename(file_path)}' is empty or contains no valid UPCs."

            # --- 2. Process each UPC ---
            with self.db_connection.cursor() as cursor:
                self.db_connection.begin() # Start transaction

                for upc, case_count in upc_counts.items():
                    # Get product details (case_size, product_id)
                    cursor.execute("SELECT product_id, case_size FROM products WHERE upc = %s", (upc,))
                    product_info = cursor.fetchone()

                    if not product_info:
                        print(f"Warning: UPC {upc} from file not found in database. Skipping.")
                        skipped_upcs.add(upc)
                        continue # Skip this UPC

                    product_id = product_info['product_id']
                    case_size = product_info['case_size']

                    if not isinstance(case_size, int) or case_size <= 0:
                         print(f"Warning: Invalid case size ({case_size}) for UPC {upc}. Skipping.")
                         skipped_upcs.add(upc)
                         continue # Skip this UPC

                    # Calculate quantity to add
                    quantity_to_add = case_count * case_size

                    # Update product quantity
                    update_sql = """
                        UPDATE products
                        SET current_quantity = current_quantity + %s
                        WHERE product_id = %s
                    """
                    rows_affected = cursor.execute(update_sql, (quantity_to_add, product_id))

                    if rows_affected > 0:
                        updated_products += 1
                        print(f"Updated UPC {upc}: Added {case_count} cases ({quantity_to_add} units).")
                    else:
                         # This shouldn't happen if we found the product_id, but good to check
                         print(f"Warning: Failed to update quantity for UPC {upc} (product_id {product_id}).")
                         skipped_upcs.add(upc)
                self.db_connection.commit() # Commit transaction

            # --- 3. Prepare summary message ---
            summary_lines = [f"Successfully processed file: {os.path.basename(file_path)}"]
            summary_lines.append(f" - Total lines/cases processed: {processed_count}")
            summary_lines.append(f" - Unique UPCs found in file: {len(upc_counts)}")
            summary_lines.append(f" - Products updated in database: {updated_products}")
            if skipped_upcs:
                summary_lines.append(f" - Skipped UPCs (not found or invalid data): {len(skipped_upcs)}")
                summary_lines.append(f"   Skipped list: {', '.join(skipped_upcs)}")

            return True, "\n".join(summary_lines)

        except FileNotFoundError:
            return False, f"Error: File not found at {file_path}"
        except pymysql.MySQLError as db_err:
            try:
                self.db_connection.rollback() # Rollback on error
            except Exception as rb_err:
                 print(f"Error during rollback: {rb_err}")
            return False, f"Database error occurred: {db_err}"
        except Exception as e:
            try:
                self.db_connection.rollback() # Rollback on unexpected error
            except Exception as rb_err:
                 print(f"Error during rollback: {rb_err}")
            return False, f"An unexpected error occurred: {e}"

class DashboardFrame(ttk.Frame):
    """Dashboard Frame with search functionality and pending reorders.""" # Updated docstring

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure the frame
        self.configure(padding="20", style="TFrame")
        self.grid_columnconfigure(0, weight=1) # Allow content to expand horizontally

        # --- Header ---
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_label = ttk.Label(header_frame, text="Dashboard", style="Header.TLabel")
        header_label.pack(side=tk.LEFT)

        # --- Quick Action Buttons --- (Grouped buttons on the right)
        quick_actions_frame = ttk.Frame(header_frame) # Create a frame for the buttons
        quick_actions_frame.pack(side=tk.RIGHT) # Pack this frame to the right

        # Add buttons inside the quick_actions_frame, packing them to the right
        # The order they are packed determines their visual order (right-to-left)
        config_button = ttk.Button(quick_actions_frame, text="Configuration",
                                   command=lambda: controller.show_frame("ConfigurationFrame"))
        config_button.pack(side=tk.RIGHT, padx=(5, 0)) # Furthest right

        process_sales_button = ttk.Button(quick_actions_frame, text="Process Sales File",
                                    command=lambda: controller.show_frame("ReportsFrame"))
        process_sales_button.pack(side=tk.RIGHT, padx=(5, 0)) # Middle button

        confirm_order_button = ttk.Button(quick_actions_frame, text="Confirm Order File", # New Button
                                         command=lambda: controller.show_frame("ConfirmOrderFrame"))
        confirm_order_button.pack(side=tk.RIGHT, padx=(5, 0)) # Leftmost of the group

        # --- Search Section ---
        search_frame = ttk.LabelFrame(self, text="Product Search", padding="10")
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        search_label = ttk.Label(search_frame, text="Search by UPC or Name:")
        search_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        search_entry.bind("<Return>", self.perform_search) # Bind Enter key

        search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_button.grid(row=0, column=2)

        # --- Recent Products/Search Results Section ---
        results_frame = ttk.LabelFrame(self, text="Products", padding="10")
        # Use grid for this frame as well for consistency
        results_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Allow this section to expand vertically

        self.products_tree = ttk.Treeview(results_frame,
                                          columns=("ID", "UPC", "Name", "Quantity"), # Adjust columns if needed
                                          show="headings", height=8) # Adjust height as needed

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
        
        # --- ADD SCROLLBAR AND GRID PLACEMENT FOR products_tree ---
        products_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)

        self.products_tree.grid(row=0, column=0, sticky="nsew") # Place the tree in the results_frame grid
        products_scrollbar.grid(row=0, column=1, sticky="ns") # Place the scrollbar in the results_frame grid

        # Bind double-click event (if needed for this tree)
        self.products_tree.bind("<Double-1>", self.open_product_config)

        # --- Pending Reorders Section ---
        reorders_frame = ttk.LabelFrame(self, text="Pending Reorder Deliveries", padding="10")
        # Use grid for this frame
        reorders_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        reorders_frame.grid_rowconfigure(0, weight=1)
        reorders_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Allow this section also to expand vertically

        self.reorders_tree = ttk.Treeview(reorders_frame, # Parent is reorders_frame
                                          columns=("ReorderID", "UPC", "Name", "QtyCases", "CaseSize", "OrderDate"),
                                          show="headings", height=6)
        
        reorders_scrollbar = ttk.Scrollbar(reorders_frame, orient="vertical", command=self.reorders_tree.yview) # Parent is reorders_frame
        self.reorders_tree.configure(yscrollcommand=reorders_scrollbar.set)

        self.reorders_tree.grid(row=0, column=0, sticky="nsew") # Use grid inside reorders_frame
        reorders_scrollbar.grid(row=0, column=1, sticky="ns") # Use grid inside reorders_frame

        # Buttons for reorder confirmation (Now correctly placed inside reorders_frame)
        reorder_buttons_frame = ttk.Frame(reorders_frame) # Parent is reorders_frame
        reorder_buttons_frame.grid(row=1, column=0, columnspan=2, sticky="e", pady=(5, 0)) # Use grid

        refresh_reorders_button = ttk.Button(reorder_buttons_frame, text="Refresh List", # Parent is reorder_buttons_frame
                                             command=self.load_pending_reorders) # Ensure this method exists
        refresh_reorders_button.pack(side=tk.LEFT, padx=5) # pack is okay inside this sub-frame

        confirm_button = ttk.Button(reorder_buttons_frame, text="Confirm Selected Delivery", # Parent is reorder_buttons_frame
                                    command=self.confirm_selected_delivery) # Ensure this method exists
        confirm_button.pack(side=tk.LEFT) # pack is okay inside this sub-frame

        # --- Load initial data --- (Now after widgets are created)
        self.load_recent_products()
        self.load_pending_reorders() # Load pending reorders on init

        # Place this button logically, perhaps below the reorders section
        new_item_button = ttk.Button(self, text="Enter New Item", command=self.open_new_item_window) # Use self.open_new_item_window
        new_item_button.grid(row=4, column=0, pady=(10, 0), sticky="e") # Use grid, maybe align right.

    def load_pending_reorders(self): # Implementation
        """Fetch and display pending reorders from the database."""
        # Clear existing items
        for item in self.reorders_tree.get_children():
            self.reorders_tree.delete(item)

        if not self.controller.db_connection:
            # Don't show messagebox here, just log or skip
            print("Warning: No database connection for loading reorders.")
            self.reorders_tree.insert("", "end", values=("Database connection error.", "", "", "", "", ""))
            return

        try:
            with self.controller.db_connection.cursor() as cursor:
                # Fetch pending reorders along with product details
                sql = """
                    SELECT r.reorder_id, p.product_id, p.upc, p.product_name,
                           r.quantity, p.case_size, r.date_requested
                    FROM reorders r
                    JOIN products p ON r.product_id = p.product_id
                    WHERE r.status = 'pending'
                    ORDER BY r.date_requested ASC
                """
                cursor.execute(sql)
                pending_reorders = cursor.fetchall()

            if not pending_reorders:
                self.reorders_tree.insert("", "end", values=("No pending reorders.", "", "", "", "", ""))
            else:
                for reorder in pending_reorders:
                    # Format date for display
                    order_date_str = reorder['order_date'].strftime('%Y-%m-%d %H:%M') if reorder.get('order_date') else 'N/A'
                    # Store necessary data within the item's values for later retrieval
                    # Use reorder_id as item id (iid) for easy access
                    self.reorders_tree.insert("", "end", values=(
                        reorder['reorder_id'],
                        reorder['upc'],
                        reorder['product_name'],
                        reorder['quantity'],
                        reorder['case_size'],
                        order_date_str
                    ), iid=reorder['reorder_id'])

        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error fetching pending reorders: {e}")
            self.reorders_tree.insert("", "end", values=(f"Error: {e}", "", "", "", "", ""))
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred loading reorders: {e}")
             self.reorders_tree.insert("", "end", values=(f"Error: {e}", "", "", "", "", ""))


    def confirm_selected_delivery(self): # Implementation
        """Confirm delivery for the selected reorder in the reorders_tree."""
        selection = self.reorders_tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a pending reorder from the list to confirm.")
            return

        selected_item_id = selection[0] # This is the iid we set (reorder_id)
        try:
            # Retrieve values directly from the selected tree item
            item_values = self.reorders_tree.item(selected_item_id, "values")
            reorder_id = int(item_values[0])
            upc = item_values[1]
            product_name = item_values[2]
            quantity_ordered_cases = int(item_values[3])
            case_size = int(item_values[4])

        except (ValueError, IndexError) as e:
             messagebox.showerror("Data Error", f"Could not read data from selected reorder row: {e}")
             return

        # Ask for confirmation
        confirm = messagebox.askyesno("Confirm Delivery",
                                       f"Confirm delivery for Reorder ID {reorder_id}?\n\n"
                                       f"Product: {product_name} (UPC: {upc})\n"
                                       f"Quantity: {quantity_ordered_cases} cases ({quantity_ordered_cases * case_size} units)")

        if confirm:
            # Call the controller method to handle the database updates
            # We need product_id, which isn't in the tree. The controller method will need it.
            # Let's pass reorder_id, quantity_ordered_cases, and case_size.
            # The controller method will look up product_id.
            success = self.controller.confirm_reorder_delivery(
                reorder_id,
                quantity_ordered_cases,
                case_size
            )

            if success:
                messagebox.showinfo("Success", f"Delivery confirmed for reorder {reorder_id}.")
                # Refresh both lists
                self.load_pending_reorders()
                self.load_recent_products() # Refresh products as quantity changed
            # Else: The confirm_reorder_delivery method in the controller should show error messages

    def open_product_config(self, event=None, product_data=None): # Add product_data argument
        """Open the configuration screen for the selected product."""
        product = None
        if product_data:
            # If product data is passed directly (e.g., from search)
            product = product_data
            print(f"Opening config directly for product ID: {product.get('product_id')}")
        elif event:
            # If called by event (e.g., tree double-click)
            selection = self.products_tree.selection()
            if not selection:
                return # Nothing selected

            item_id = selection[0]
            item_values = self.products_tree.item(item_id, "values")

            if not item_values or len(item_values) < 1:
                 print("Error: Could not get product ID from selected tree item.")
                 return

            try:
                # Assuming the first column in products_tree is product_id
                product_id = int(item_values[0])
                print(f"Opening config from tree selection for product ID: {product_id}")

                # Retrieve the full product data using the product ID
                if not self.controller.db_connection:
                     messagebox.showerror("Database Error", "No database connection.")
                     return

                with self.controller.db_connection.cursor() as cursor:
                    # Fetch all relevant columns for the config screen
                    query = """
                        SELECT product_id, upc, product_name, description, current_quantity,
                               category, case_size, unit_price
                        FROM products
                        WHERE product_id = %s
                    """
                    cursor.execute(query, (product_id,))
                    product = cursor.fetchone() # Fetch as dictionary

            except (ValueError, IndexError):
                messagebox.showerror("Error", "Could not determine product ID from selection.")
                return
            except pymysql.MySQLError as e:
                messagebox.showerror("Database Error", f"Error retrieving product details: {e}")
                return
            except Exception as e:
                 messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                 return
        else:
             # Should not happen if called correctly
             print("Error: open_product_config called without event or product_data.")
             return

        # --- Load data into ConfigurationFrame ---
        if product:
            # Get the ConfigurationFrame instance
            config_frame = self.controller.frames.get("ConfigurationFrame")
            if config_frame:
                config_frame.load_product(product) # Load data into the config frame
                self.controller.show_frame("ConfigurationFrame") # Switch view
            else:
                messagebox.showerror("Error", "Configuration frame not found.")
        else:
             # Only show warning if triggered by event and product not found
             if event:
                 messagebox.showwarning("Not Found", f"Product with ID {product_id} not found in database.")

    # def open_new_item_window(self): # Implementation
    #     """Opens the modal window to add a new product."""
    #     # Create and display the NewItemWindow
    #     # Pass 'self.controller' so the window can interact with the main app/database
    #     new_item_window = NewItemWindow(self.controller)
    #     new_item_window.grab_set() # Make the new window modal

    def perform_search(self, event=None): # This is called by button/entry
        """Perform product search, display results, and handle navigation."""
        search_term = self.search_var.get().strip() # Use strip()
        if not search_term:
            self.load_recent_products() # Load recent if search is empty
            return

        # Call controller's search method
        products = self.controller.search_product(search_term)

        # Clear the main products tree first
        self.display_products([], is_search=True) # Clear tree, mark as search context

        if not products:
            # Display "No results" in the tree
            self.products_tree.insert("", "end", values=("", "No results found.", "", ""))
            # Optionally show a messagebox
            # messagebox.showinfo("Search", "No products found matching the search term")
            return

        if len(products) == 1:
            # If only one product is found, navigate directly to the configuration frame
            print("Only one product found. Navigating to configuration frame.")
            # Call the updated open_product_config with the product data
            self.open_product_config(product_data=products[0])
        else:
            # If multiple products are found, show a selection popup
            print(f"Multiple products found: {len(products)}. Showing selection popup.")
            self.show_product_selection_popup(products)

    def display_products(self, products, is_search=False):
        """Clear and populate the main products treeview."""
        # Find the correct products_tree (ensure it exists and is named self.products_tree)
        if not hasattr(self, 'products_tree'):
             print("Error: products_tree not found in DashboardFrame")
             return

        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Insert new items
        if products:
            for product in products:
                # Adjust the values based on the columns in your products_tree
                self.products_tree.insert("", "end", values=(
                    product.get('product_id', 'N/A'), # Example column
                    product.get('upc', 'N/A'),
                    product.get('product_name', 'N/A'),
                    product.get('current_quantity', 'N/A')
                    # Add other columns as needed
                ))
        elif is_search:
             # Optionally show a "No results" message in the tree
             self.products_tree.insert("", "end", values=("", "No results found.", "", ""))

    def open_new_item_window(self):
        """Open a window to add a new product."""
        NewItemWindow(self.controller)
    
    def on_show(self):
        """Called when this frame is shown."""
        # Refresh the products list
        self.load_recent_products()
    
    # def search_product(self):
    #     """Search for products and display matching results."""
    #     search_term = self.search_entry.get().strip()
    #     if not search_term:
    #         messagebox.showinfo("Search", "Please enter a UPC or product name")
    #         return
        
    #     # Call controller's search method
    #     products = self.controller.search_product(search_term)
        
    #     if not products:
    #         messagebox.showinfo("Search", "No products found matching the search term")
    #         return
        
    #     if len(products) == 1:
    #         # If only one product is found, navigate directly to the configuration frame
    #         print("Only one product found. Navigating to configuration frame.")
    #         self.open_product_config(products[0])
    #     else:
    #         # If multiple products are found, show a selection popup
    #         print(f"Multiple products found: {len(products)}. Showing selection popup.")
    #         self.show_product_selection_popup(products)
    
    def load_recent_products(self):
        """Load recent products into the treeview."""
        print("Attempting to load recent products...") # Debug
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Get recent products from database
        if not self.controller.db_connection:
            print("DB connection invalid in load_recent_products.") # Debug
            return
        try:
            with self.controller.db_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT product_id, upc, product_name, current_quantity FROM products "
                    "ORDER BY updated_at DESC LIMIT 10"
                )
                products = cursor.fetchall()
                print(f"Found {len(products)} recent products.") # Debug
                # print(products) # Optional: print the actual data

                # Add products to treeview
                if not products:
                     self.products_tree.insert("", "end", values=("No recent products found.", "", "", "")) # Add message if empty
                else:
                    for product in products:
                        self.products_tree.insert("", "end", values=(
                            product["product_id"],
                            product["upc"],
                            product["product_name"],
                            product["current_quantity"]
                        ))
        except pymysql.MySQLError as e:
            print(f"Database Error in load_recent_products: {e}") # Debug
            messagebox.showerror("Database Error", f"Error loading products: {e}")
        except Exception as e:
             print(f"Unexpected Error in load_recent_products: {e}") # Debug
             messagebox.showerror("Error", f"An unexpected error occurred loading products: {e}")
    
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
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a product")
            return

        item = tree.item(selection[0])
        try:
            product_id = int(item["values"][0]) # Get the product ID
        except (ValueError, IndexError):
             messagebox.showerror("Error", "Could not get product ID from popup selection.")
             popup.destroy() # Close popup on error
             return
        # Retrieve the full product data using the product ID
        product = None
        try:
            if not self.controller.db_connection:
                 messagebox.showerror("Database Error", "No database connection.")
                 popup.destroy()
                 return

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
            popup.destroy()
            return
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred retrieving product: {e}")
             popup.destroy()
             return

        # Close the popup BEFORE trying to open the config frame
        popup.destroy()

        if product:
            # Call the updated open_product_config with the retrieved data
            self.open_product_config(product_data=product)
        else:
             messagebox.showwarning("Not Found", f"Selected product (ID: {product_id}) not found in database.")

    # def open_product_config(self, product):
    #     """Open the configuration screen for the selected product."""
    #     config_frame = self.controller.frames["ConfigurationFrame"]
    #     config_frame.load_product(product)
    #     self.controller.show_frame("ConfigurationFrame")


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
    """Frame for listing and processing sales report files.""" # Updated docstring

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

        header_label = ttk.Label(header_frame, text="Process Sales Files", # Updated header text
                                style="Header.TLabel")
        header_label.pack(side=tk.LEFT, padx=20)

        # Sales files list frame
        files_frame = ttk.Frame(self) # Renamed variable for clarity
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create a treeview to display sales files
        self.files_tree = ttk.Treeview(files_frame, # Renamed variable
                                        columns=("Filename", "Date Modified"),
                                        show="headings",
                                        height=10)

        # Define headings
        self.files_tree.heading("Filename", text="Sales Filename") # Updated heading
        self.files_tree.heading("Date Modified", text="Date Modified")

        # Configure columns
        self.files_tree.column("Filename", width=400)
        self.files_tree.column("Date Modified", width=150)

        # Add scrollbar
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", # Renamed variable
                                        command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)

        # Pack the treeview and scrollbar
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click event to process sales file
        self.files_tree.bind("<Double-1>", self.process_selected_sales_file_event) # Updated binding and method name

        # Action buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))

        process_button = ttk.Button(buttons_frame, text="Process Selected Sales File", # Updated button text
                               command=self.process_selected_sales_file) # Updated command and method name
        process_button.pack(side=tk.RIGHT)

        # Load sales files when showing this frame
        self.load_sales_files() # Renamed method

    def on_show(self):
        """Called when this frame is shown."""
        # Refresh the sales files list
        self.load_sales_files() # Renamed method

    def load_sales_files(self): # Renamed method
        """Load sales report files from the directory into the treeview."""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        try:
            # Ensure the directory exists
            if not os.path.isdir(SALES_REPORTS_DIR): # Use new constant
                messagebox.showwarning("Directory Not Found", f"The directory {SALES_REPORTS_DIR} does not exist.") # Use new constant
                return

            # List files in the directory
            files = [f for f in os.listdir(SALES_REPORTS_DIR) if os.path.isfile(os.path.join(SALES_REPORTS_DIR, f)) and f.endswith('.txt')] # Use new constant

            # Sort files by modification time, newest first
            files.sort(key=lambda f: os.path.getmtime(os.path.join(SALES_REPORTS_DIR, f)), reverse=True) # Use new constant

            # Add files to treeview
            for filename in files:
                file_path = os.path.join(SALES_REPORTS_DIR, filename) # Use new constant
                try:
                    mod_time_timestamp = os.path.getmtime(file_path)
                    mod_time_str = datetime.fromtimestamp(mod_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except OSError:
                    mod_time_str = "N/A" # Handle potential errors getting mod time

                self.files_tree.insert("", "end", values=(
                    filename,
                    mod_time_str
                ), tags=(file_path,)) # Store full path in tags
        except Exception as e:
            messagebox.showerror("Error Loading Files", f"An error occurred while loading sales files: {e}") # Updated message


    def process_selected_sales_file(self): # Renamed method
        """Process the selected sales report file using reorder_generator.py."""
        # Get selected item
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a sales file to process") # Updated message
            return

        # Get the file path from tags
        file_path = self.files_tree.item(selection[0], "tags")[0]

        # Process the file using the reorder script
        self.run_reorder_script(file_path) # Keep using this method

    def process_selected_sales_file_event(self, event): # Renamed method
        """Handle double-click on a sales file item."""
        selection = self.files_tree.selection()
        if not selection:
            return

        # Get the file path from tags
        file_path = self.files_tree.item(selection[0], "tags")[0]

        # Process the file using the reorder script
        self.run_reorder_script(file_path) # Keep using this method

    def run_reorder_script(self, file_path): # No changes needed here, it takes the file path correctly
        """Run the reorder_generator.py script with the selected file."""
        script_path = os.path.join(os.path.dirname(__file__), "reorder_generator.py")
        command = [sys.executable, script_path, file_path]

        try:
            # Check if script exists
            if not os.path.exists(script_path):
                 messagebox.showerror("Error", f"Script not found: {script_path}")
                 return

            print(f"Running command: {' '.join(command)}")
            # Run the script and capture output
            result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(script_path))

            # Display success message and output
            output_message = f"Successfully processed sales file {os.path.basename(file_path)}.\n\nOutput:\n{result.stdout}" # Updated message
            messagebox.showinfo("Processing Complete", output_message)

            # Refresh the dashboard as inventory and reorders might have changed
            dashboard_frame = self.controller.frames.get("DashboardFrame")
            if dashboard_frame:
                # Check if the specific methods exist before calling
                if hasattr(dashboard_frame, 'load_recent_products'):
                    dashboard_frame.load_recent_products()
                if hasattr(dashboard_frame, 'load_pending_reorders'):
                    dashboard_frame.load_pending_reorders()


        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find Python executable or script: {command[0]}")
        except subprocess.CalledProcessError as e:
            # Display error message and output
            error_message = f"Error processing sales file {os.path.basename(file_path)}.\n\nExit Code: {e.returncode}\n\nError Output:\n{e.stderr}\n\nStandard Output:\n{e.stdout}" # Updated message
            messagebox.showerror("Processing Error", error_message)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while running the script: {e}")

class ConfirmOrderFrame(ttk.Frame):
    """Frame for confirming received orders by processing a reorder file."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure the frame
        self.configure(padding="20", style="TFrame")

        # --- Header ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        back_button = ttk.Button(header_frame, text="← Back",
                                command=lambda: controller.show_frame("DashboardFrame"))
        back_button.pack(side=tk.LEFT)

        header_label = ttk.Label(header_frame, text="Confirm Received Order from File",
                                style="Header.TLabel")
        header_label.pack(side=tk.LEFT, padx=20)

        # --- Reorder Files List ---
        files_frame = ttk.Frame(self)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.files_tree = ttk.Treeview(files_frame,
                                        columns=("Filename", "Date Modified"),
                                        show="headings",
                                        height=15) # Increased height a bit

        # Define headings
        self.files_tree.heading("Filename", text="Reorder Filename")
        self.files_tree.heading("Date Modified", text="Date Modified")

        # Configure columns
        self.files_tree.column("Filename", width=400)
        self.files_tree.column("Date Modified", width=150)

        # Add scrollbar
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical",
                                        command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)

        # Pack the treeview and scrollbar
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click event
        self.files_tree.bind("<Double-1>", self.process_selected_order_file_event)

        # --- Action Buttons ---
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))

        confirm_button = ttk.Button(buttons_frame, text="Confirm Selected Order File",
                               command=self.process_selected_order_file)
        confirm_button.pack(side=tk.RIGHT)

        # Load files on initialization
        self.load_reorder_files()

    def on_show(self):
        """Called when this frame is shown."""
        self.load_reorder_files() # Refresh the list when shown

    def load_reorder_files(self):
        """Load reorder list files from the directory into the treeview."""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        try:
            # Ensure the directory exists
            if not os.path.isdir(REORDER_LISTS_DIR):
                messagebox.showwarning("Directory Not Found", f"The directory {REORDER_LISTS_DIR} does not exist.")
                return

            # List files in the directory (assuming .txt, adjust if needed)
            files = [f for f in os.listdir(REORDER_LISTS_DIR) if os.path.isfile(os.path.join(REORDER_LISTS_DIR, f)) and f.endswith('.txt')]

            # Sort files by modification time, newest first
            files.sort(key=lambda f: os.path.getmtime(os.path.join(REORDER_LISTS_DIR, f)), reverse=True)

            # Add files to treeview
            if not files:
                 self.files_tree.insert("", "end", values=("No reorder files found.", ""))
            else:
                for filename in files:
                    file_path = os.path.join(REORDER_LISTS_DIR, filename)
                    try:
                        mod_time_timestamp = os.path.getmtime(file_path)
                        mod_time_str = datetime.fromtimestamp(mod_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    except OSError:
                        mod_time_str = "N/A"

                    self.files_tree.insert("", "end", values=(
                        filename,
                        mod_time_str
                    ), tags=(file_path,)) # Store full path in tags
        except Exception as e:
            messagebox.showerror("Error Loading Files", f"An error occurred while loading reorder files: {e}")

    def process_selected_order_file(self):
        """Process the selected reorder file to update inventory."""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a reorder file to confirm.")
            return

        file_path = self.files_tree.item(selection[0], "tags")[0]
        filename = os.path.basename(file_path)

        confirm = messagebox.askyesno("Confirm Order Update",
                                      f"Are you sure you want to update inventory based on the file:\n{filename}?\n\n"
                                      "This will read UPCs from the file, assume each line represents ONE CASE received, "
                                      "and increase the product quantity accordingly.")
        if confirm:
            success, message = self.controller.confirm_order_from_file(file_path)
            if success:
                messagebox.showinfo("Update Complete", message)
                # Refresh dashboard lists
                dashboard_frame = self.controller.frames.get("DashboardFrame")
                if dashboard_frame:
                    if hasattr(dashboard_frame, 'load_recent_products'):
                        dashboard_frame.load_recent_products()
                    if hasattr(dashboard_frame, 'load_pending_reorders'):
                        dashboard_frame.load_pending_reorders() # Also refresh pending orders
            else:
                messagebox.showerror("Update Failed", message)

    def process_selected_order_file_event(self, event):
        """Handle double-click on a reorder file item."""
        # Check if the click was actually on an item
        item_id = self.files_tree.identify_row(event.y)
        if not item_id:
            return # Click was not on an item

        # Check if the item has tags (our indicator of a valid file row)
        tags = self.files_tree.item(item_id, "tags")
        if not tags:
             return # Click was likely on the "No files found" message

        self.process_selected_order_file() # Call the main processing method

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