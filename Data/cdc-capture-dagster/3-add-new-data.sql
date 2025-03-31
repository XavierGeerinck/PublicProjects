-- Insert additional customers
INSERT INTO Customers (FirstName, LastName, Email)
VALUES 
    ('Michael', 'Taylor', 'michael.taylor@example.com'),
    ('Sarah', 'Johnson', 'sarah.johnson@example.com'),
    ('David', 'Miller', 'david.miller@example.com'),
    ('Emma', 'Wilson', 'emma.wilson@example.com'),
    ('Thomas', 'Anderson', 'thomas.anderson@example.com');
GO

-- Insert additional orders
INSERT INTO Orders (CustomerID, TotalAmount, Status)
VALUES 
    (3, 199.99, 'Shipped'),
    (5, 67.50, 'Processing'),
    (2, 145.75, 'Completed'),
    (4, 320.00, 'Pending'),
    (6, 88.25, 'Processing'),
    (7, 150.49, 'Completed'),
    (8, 210.75, 'Shipped'),
    (9, 45.99, 'Pending'),
    (10, 175.25, 'Processing');
GO

-- Update some existing records to generate CDC events
UPDATE Customers
SET Email = 'john.smith.updated@example.com'
WHERE FirstName = 'John' AND LastName = 'Smith';

UPDATE Orders
SET Status = 'Delivered'
WHERE Status = 'Shipped';
GO

-- Delete a record to generate CDC delete event
DELETE FROM Orders
WHERE CustomerID = 5 AND TotalAmount < 70.00;
GO