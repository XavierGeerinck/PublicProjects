# README

This repository demonstrates how to set up a SQL Server -> Apache Iceberg incremental data loading process using Debezium. To accomplish this, a custom Debezium sink is used (to eliminate the need for Apache Kafka) and an Apache Iceberg Catalog is implemented using the Iceberg REST Catalog Python API and persisted to a PostgreSQL database.

## Getting Started

```bash
docker-compose up -d

# Load the Notebook Server
http://localhost:8888

# Extra URLs
http://localhost:8080 # Trino
http://localhost:9000 # MinIO
http://localhost:9001 # MinIO UI
http://localhost:5432 # PostgreSQL
http://localhost:8000 # Iceberg REST Catalog
```

## Reference

https://binayakd.tech/posts/2024-08-30-exploring-iceberg/
https://github.com/binayakd/iceberg-rest-catalog/tree/f379de583216c08e7e46c6713865ebb1dcf9b63e