-- Active: 1743404444784@@vdadbxaviertest.database.windows.net@1433@main
USE main;
GO

-- Create a sample customers table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY IDENTITY(1,1),
    FirstName NVARCHAR(50),
    LastName NVARCHAR(50),
    Email NVARCHAR(100),
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create a sample orders table
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
    OrderDate DATETIME DEFAULT GETDATE(),
    TotalAmount DECIMAL(10, 2),
    Status NVARCHAR(20)
);
GO

-- Insert sample data into Customers
INSERT INTO Customers (FirstName, LastName, Email)
VALUES 
    ('John', 'Smith', 'john.smith@example.com'),
    ('Jane', 'Doe', 'jane.doe@example.com'),
    ('Bob', 'Johnson', 'bob.johnson@example.com'),
    ('Alice', 'Williams', 'alice.williams@example.com'),
    ('Charlie', 'Brown', 'charlie.brown@example.com');
GO

-- Insert sample data into Orders
INSERT INTO Orders (CustomerID, TotalAmount, Status)
VALUES 
    (1, 125.50, 'Completed'),
    (2, 89.99, 'Processing'),
    (3, 45.25, 'Shipped'),
    (1, 250.00, 'Pending'),
    (4, 75.30, 'Completed');
GO
