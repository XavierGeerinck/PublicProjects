#!/bin/bash
# Start the containers
echo "Starting containers..."
docker-compose up -d

# Wait for everything to initialize
echo "Waiting for services to initialize (2 minutes)..."
sleep 120

# Initialize SQL Server
echo "Initializing SQL Server..."
docker-compose exec sqlserver /bin/bash -c "/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'Password!23' -i /scripts/init.sql"

# Wait for CDC events to be processed by Debezium
echo "Waiting for CDC events to be processed (30 seconds)..."
sleep 30

# Add more data to demonstrate ongoing CDC
echo "Adding more customer data..."
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "Password!23" -Q "
  USE testdb;
  INSERT INTO customers (id, first_name, last_name, email, updated_at)
  VALUES 
    (4, 'Alice', 'Williams', 'alice.williams@example.com', GETDATE()),
    (5, 'Charlie', 'Brown', 'charlie.brown@example.com', GETDATE());
  UPDATE customers SET last_name = 'Doe-Smith', updated_at = GETDATE() WHERE id = 1;
  DELETE FROM customers WHERE id = 3;
"

# Wait for new CDC events to be processed
echo "Waiting for more CDC events to be processed (30 seconds)..."
sleep 30

# Run Spark query script
echo "Running Spark query script..."
docker-compose exec spark spark-submit \
  --jars /opt/spark/jars/iceberg-spark-runtime-3.3_2.13-1.3.1.jar,/opt/spark/jars/hadoop-aws-3.3.2.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.367.jar \
  /opt/spark/scripts/query_iceberg.py

echo "Demo completed!"
