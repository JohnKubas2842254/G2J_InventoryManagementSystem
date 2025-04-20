USE G2J_InventoryManagement;
-- SQL commands to update the reorders table
ALTER TABLE reorders
ADD COLUMN quantity_ordered_cases INT NOT NULL DEFAULT 1,
ADD COLUMN order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN received_date DATETIME NULL,
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'; -- e.g., 'pending', 'received', 'cancelled'

-- Optional: Add an index on status for faster lookups
ALTER TABLE reorders ADD INDEX idx_status (status);-- SQL commands to update the reorders table
ALTER TABLE reorders
ADD COLUMN quantity_ordered_cases INT NOT NULL DEFAULT 1,
ADD COLUMN order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN received_date DATETIME NULL,
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'; -- e.g., 'pending', 'received', 'cancelled'

-- Optional: Add an index on status for faster lookups
ALTER TABLE reorders ADD INDEX idx_status (status);