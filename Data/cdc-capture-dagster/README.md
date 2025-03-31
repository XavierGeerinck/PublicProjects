# README

This is an example of a CDC (Capture Data Change) pipeline using Delta, Dagster and SQL Server.

The example will demonstrate a pipeline where:
1. We read changes from SQL Server through CDC
2. Process the changes and provide them back to the Dagster Delta IO Manager for Merging
3. The merge process will UPSERT existing records

> TODO: Validate the below, we should figure out a solution for this
> Note: We are upserting, this DELETE records won't happen. To delete, we can simply set an `is_deleted` flag


## Reference

https://pola.rs/
https://github.com/ASML-Labs/dagster-delta/issues/23

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
code dagster-cdc

# Download the dependencies
uv sync

# Start Dagster Locally
dagster dev -f dagster_cdc/definitions.py
```

## Troubleshooting

### Invalid peer certificate: UnknownIssuer

This is because the SSL Certificate File is not being found. Set it manually through the below:

```bash
# This file is created automatically through `sudo update-ca-certificates`
# if you are missing your CA, add it in `/usr/local/share/ca-certificates/`
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

### Can't open lib 'ODBC Driver 18 for SQL Server' : file not found (0) (SQLDriverConnect)

Install the driver as per [Documentation (Linux)](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15&tabs=alpine18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline#18) or [Documentation (macOS)](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver15)
