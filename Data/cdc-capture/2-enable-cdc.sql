USE main;
GO

-- Enable CDC for the database
EXEC sys.sp_cdc_enable_db;
GO

-- Enable CDC for Customers table
EXEC sys.sp_cdc_enable_table
@source_schema = N'dbo',
@source_name = N'Customers',
@role_name = NULL,
@supports_net_changes = 1;
GO

-- Enable CDC for Orders table
EXEC sys.sp_cdc_enable_table
@source_schema = N'dbo',
@source_name = N'Orders',
@role_name = NULL,
@supports_net_changes = 1;
GO

-- Verify CDC is enabled for the database
SELECT name, is_cdc_enabled
FROM sys.databases 
WHERE name = 'main';

-- Verify CDC is enabled for the tables
SELECT name, is_tracked_by_cdc
FROM sys.tables
WHERE name IN ('Customers', 'Orders');
GO
