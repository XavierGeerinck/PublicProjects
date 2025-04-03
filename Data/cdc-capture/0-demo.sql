SELECT * FROM cdc.change_tables WHERE capture_instance = 'dbo_Customers';

-- Get the index columns
SELECT * FROM cdc.index_columns

-- Get the ndex column for the capture instance
SELECT column_name FROM cdc.index_columns WHERE object_id = (SELECT object_id FROM cdc.change_tables WHERE capture_instance = 'dbo_Customers')