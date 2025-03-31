# dagster-cdc Project

This project implements Change Data Capture (CDC) from SQL Server to Delta Lake using Dagster. It provides a framework for tracking changes in specified tables and efficiently updating Delta tables, which can then be published to Power BI.

## Project Structure

- **dagster_cdc/**: Main package containing all the functionality.
  - **assets/**: Contains the implementation of CDC assets.
    - **delta_assets.py**: Implements CDC assets for managing changes from SQL Server to Delta Lake.
  - **resources/**: Contains resources for managing connections and data retrieval.
    - **sql_server_cdc.py**: Defines the SQLServerCDCResource class for connecting to SQL Server and retrieving changes.
  - **utils/**: Contains utility functions for working with Delta Lake.
    - **delta_helpers.py**: Provides helper functions for reading and writing Delta tables.
  - **definitions.py**: Defines the Dagster asset definitions and configurations.

- **configs/**: Contains configuration files.
  - **default_config.yaml**: Default configuration settings for database connections and Delta Lake paths.

- **setup.py**: Setup script for the project, defining package metadata and dependencies.

- **pyproject.toml**: Configuration file for Python packaging.

## Usage

1. Configure your database connection settings in `configs/default_config.yaml`.
2. Use the provided assets in `dagster_cdc/assets/delta_assets.py` to track changes in the Customers and Orders tables.
3. Run the Dagster pipeline to process the CDC updates and write them to Delta Lake.