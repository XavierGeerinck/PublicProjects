-- Insert additional customers
INSERT INTO Customers (FirstName, LastName, Email)
VALUES 
    ('Brave', 'Sunny', 'brave.sunny@example.com');
GO

DELETE FROM Customers
WHERE FirstName = 'Sarah' AND LastName = 'Johnson';