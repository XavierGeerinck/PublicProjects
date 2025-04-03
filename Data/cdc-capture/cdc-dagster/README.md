# CDC with Dagster and Apache Iceberg

## Prerequisites

### Python 3.12

```bash
# Install UV
# why UV? Because it's fast (see: https://codemaker2016.medium.com/introducing-uv-next-gen-python-package-manager-b78ad39c95d7)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure Python 3.12 with it
uv python install 3.12
```

### SQL Server

Create a SQL Server instance with a database named `main`

### pyodbc

```bash
# MacOS
brew install unixodbc
```

## Getting Started

### 1. Create DB Schema

Execute the schema SQL from `./1-schema.sql`

### 2. Enable CDC

Enable the Change Data Capture by executing the SQL in `./2-enable-cdc.sql`

### 3. Run Dagster

```bash
# Open the Dagster folder in a standalone VSCode instance
code cdc-dagster

# Download the dependencies
uv sync

# Activate env
source .venv/bin/activate

# Navigate to the dagster project
cd cdc_dagster/

# Copy the dagster config
cp dagster.yaml ~/.dagster/dagster.yaml

# Configure the database access
cp .env.example .env

# Start Dagster Locally
DAGSTER_HOME=~/.dagster dagster dev -f cdc_dagster/definitions.py
```
