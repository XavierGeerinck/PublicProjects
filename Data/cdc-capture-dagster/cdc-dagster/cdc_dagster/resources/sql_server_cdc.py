from dagster import resource, EnvVar, Config
import polars as pl
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from contextlib import contextmanager
from cdc_dagster.constants import LSN_DEFAULT
from typing import List


class SQLServerCDCConfig(Config):
    """Configuration for SQL Server CDC connection.
    Note: use EnvVar to keep them secret in the UI."""

    host: EnvVar = EnvVar("SQL_SERVER_HOST")
    user: EnvVar = EnvVar("SQL_SERVER_USER")
    password: EnvVar = EnvVar("SQL_SERVER_PASSWORD")
    database: EnvVar = EnvVar("SQL_SERVER_DATABASE")

    last_lsn: str = LSN_DEFAULT

    def get_connection_string(self):
        """Construct the connection string for SQLAlchemy."""
        pass_escaped = quote_plus(self.password.get_value())
        user_escaped = quote_plus(self.user.get_value())
        driver_escaped = quote_plus("ODBC Driver 18 for SQL Server")
        return f"mssql+pyodbc://{user_escaped}:{pass_escaped}@{self.host.get_value()}/{self.database.get_value()}?driver={driver_escaped}"


class SQLServerCDCResource:
    """Resource to handle SQL Server CDC operations using native CDC functions."""

    def __init__(self, config: SQLServerCDCConfig):
        self.config = config
        self.engine = sa.create_engine(self.config.get_connection_string())

    @contextmanager
    def get_connection(self):
        """Get a database connection using context manager for automatic cleanup."""
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    def get_primary_key_columns(self, table_name: str) -> List[str]:
        """Get the primary key columns for a CDC-enabled table."""
        with self.get_connection() as connection:
            instance = self.get_capture_instance_name("dbo", table_name)

            query = sa.text("""
            SELECT column_name FROM cdc.index_columns WHERE object_id = (
                SELECT object_id FROM cdc.change_tables WHERE capture_instance = :capture_instance_name
            )
            """)

            result = connection.execute(query, {"capture_instance_name": instance})
            primary_key_columns = [row[0] for row in result]
            return primary_key_columns

    def is_cdc_enabled_for_database(self):
        """Check if CDC is enabled for the database."""
        with self.get_connection() as connection:
            query = sa.text("""
                SELECT is_cdc_enabled 
                FROM sys.databases 
                WHERE name = :db_name
            """)
            result = connection.execute(
                query, {"db_name": self.config.database.get_value()}
            ).scalar()
            return bool(result)

    def is_cdc_enabled_for_table(self, schema_name, table_name):
        """Check if CDC is enabled for the specified table."""
        with self.get_connection() as connection:
            capture_instance_name = self.get_capture_instance_name(
                schema_name, table_name
            )

            query = sa.text(f"""
                SELECT 1
                FROM cdc.change_tables
                WHERE capture_instance = '{capture_instance_name}'
            """)

            result = connection.execute(
                query, {"schema_name": schema_name, "table_name": table_name}
            ).scalar()

            return bool(result)

    def get_capture_instance_name(self, schema_name, table_name):
        """Get the CDC capture instance name for a table."""
        return f"dbo_{table_name}"

    def get_current_lsn(self):
        """Get the current maximum LSN from SQL Server using native function."""
        with self.get_connection() as connection:
            query = sa.text("SELECT sys.fn_cdc_get_max_lsn()")
            return connection.execute(query).scalar()

    def get_min_lsn(self, capture_instance=None):
        """Get the minimum available LSN for a capture instance."""
        with self.get_connection() as connection:
            query = sa.text("SELECT sys.fn_cdc_get_min_lsn(:capture_instance)")
            return connection.execute(
                query, {"capture_instance": capture_instance}
            ).scalar()

    def hex_string_to_lsn(self, lsn_hex):
        """Convert a hexadecimal LSN string to binary for SQL Server functions."""
        with self.get_connection() as connection:
            if not lsn_hex or not isinstance(lsn_hex, str):
                # Return minimum LSN if input is invalid
                query = sa.text("SELECT sys.fn_cdc_get_min_lsn(NULL)")
                return connection.execute(query).scalar()

            if not lsn_hex.startswith("0x"):
                lsn_hex = f"0x{lsn_hex}"

            query = sa.text("SELECT CAST(:lsn_hex AS BINARY(10))")
            result = connection.execute(query, {"lsn_hex": lsn_hex}).scalar()

            if result is None:
                query = sa.text("SELECT sys.fn_cdc_get_min_lsn(NULL)")
                return connection.execute(query).scalar()

            return result

    def lsn_to_hex_string(self, lsn_bytes):
        """Convert a binary LSN to a hex string format."""
        if lsn_bytes is None:
            return LSN_DEFAULT

        return f"0x{lsn_bytes.hex().upper()}"

    def get_table_changes(
        self, table_name, last_lsn=None, schema_name="dbo", chunksize=10000
    ) -> tuple[pl.DataFrame, str]:
        """Get changes from a CDC-enabled table since the last LSN.
        Uses the native SQL Server CDC function fn_cdc_get_all_changes.

        Args:
            table_name (str): The name of the table to query.
            last_lsn (str, optional): The last processed LSN. If None, a full copy is performed.
            schema_name (str, optional): The schema name of the table. Defaults to 'dbo'.
            chunksize (int, optional): Number of rows to fetch per query. Defaults to 10000.

        Returns:
            tuple: A tuple containing the DataFrame of changes and the current LSN.
        """
        try:
            with self.get_connection() as connection:
                # Check if CDC is enabled for the database and table
                if not self.is_cdc_enabled_for_database():
                    raise ValueError(
                        f"CDC is not enabled for database {self.config.database.get_value()}"
                    )

                if not self.is_cdc_enabled_for_table(schema_name, table_name):
                    raise ValueError(
                        f"CDC not enabled for table {schema_name}.{table_name}"
                    )

                # Get the capture instance name
                capture_instance = self.get_capture_instance_name(
                    schema_name, table_name
                )
                if not capture_instance:
                    raise ValueError(
                        f"Could not find CDC capture instance for {schema_name}.{table_name}"
                    )

                # Get current maximum LSN
                current_lsn = self.get_current_lsn()

                # If no last_lsn provided, we should first take a first copy of the table
                if last_lsn is None or last_lsn == LSN_DEFAULT:
                    raise ValueError(
                        f"Initial copy required for table {schema_name}.{table_name}"
                    )

                # Convert LSN hex strings to binary
                from_lsn_hex = last_lsn
                to_lsn_hex = f"0x{current_lsn.hex()}"

                # Use the native CDC function with parameterized query
                # Process in chunks to avoid memory issues with large tables
                query = sa.text(f"""
                    DECLARE @from_lsn BINARY(10), @to_lsn BINARY(10)
                    SET @from_lsn = CONVERT(BINARY(10), :from_lsn, 1)
                    SET @to_lsn = CONVERT(BINARY(10), :to_lsn, 1)
       
                    SELECT * FROM cdc.fn_cdc_get_all_changes_{capture_instance}(
                        @from_lsn, @to_lsn, 'all'
                    )
                """)

                # Use chunksize to process large result sets in batches
                changes_df = pl.read_database(
                    query,
                    connection,
                    execute_options={
                        "parameters": {"from_lsn": from_lsn_hex, "to_lsn": to_lsn_hex}
                    },
                )

                # Convert binary LSN to hex string for storage
                current_lsn_hex = self.lsn_to_hex_string(current_lsn)

                return changes_df, current_lsn_hex

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error when getting CDC changes: {str(e)}"
            ) from e

    def get_full_table_data(self, table_name):
        """Get the entire table data (used for initial load) with memory optimization."""
        schema_name = "dbo"  # Default schema
        try:
            with self.get_connection() as connection:
                # Use chunking to handle large tables
                query = sa.text(f"SELECT * FROM {schema_name}.{table_name}")

                # Read the table
                full_df = pl.read_database(
                    query,
                    connection,
                )

                return full_df

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error when getting full table data: {str(e)}"
            ) from e

    # def enable_cdc_for_database(self):
    #     """Enable CDC for the database if not already enabled using native procedure."""
    #     try:
    #         with self.get_connection() as connection:
    #             if self.is_cdc_enabled_for_database():
    #                 return

    #             # Use native CDC stored procedure
    #             connection.execute(sa.text("EXEC sys.sp_cdc_enable_db"))
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(
    #             f"Database error when enabling CDC for database: {str(e)}"
    #         ) from e

    # def enable_cdc_for_table(
    #     self,
    #     schema_name,
    #     table_name,
    #     role_name=None,
    #     capture_instance=None,
    #     supports_net_changes=None,
    #     index_name=None,
    #     captured_column_list=None,
    #     filegroup_name=None,
    #     allow_partition_switch=None,
    # ):
    #     """Enable CDC for a specific table using native CDC stored procedure."""
    #     try:
    #         with self.get_connection() as connection:
    #             # Ensure CDC is enabled for the database
    #             if not self.is_cdc_enabled_for_database():
    #                 self.enable_cdc_for_database()

    #             # Check if CDC is already enabled for this table
    #             if self.is_cdc_enabled_for_table(schema_name, table_name):
    #                 return

    #             # Build the command with parameters for the stored procedure
    #             cmd_parts = [f"EXEC sys.sp_cdc_enable_table"]
    #             cmd_parts.append(f"@source_schema = N'{schema_name}'")
    #             cmd_parts.append(f"@source_name = N'{table_name}'")

    #             if role_name is not None:
    #                 cmd_parts.append(f"@role_name = N'{role_name}'")
    #             if capture_instance is not None:
    #                 cmd_parts.append(f"@capture_instance = N'{capture_instance}'")
    #             if supports_net_changes is not None:
    #                 cmd_parts.append(
    #                     f"@supports_net_changes = {1 if supports_net_changes else 0}"
    #                 )
    #             if index_name is not None:
    #                 cmd_parts.append(f"@index_name = N'{index_name}'")
    #             if captured_column_list is not None:
    #                 cmd_parts.append(
    #                     f"@captured_column_list = N'{captured_column_list}'"
    #                 )
    #             if filegroup_name is not None:
    #                 cmd_parts.append(f"@filegroup_name = N'{filegroup_name}'")
    #             if allow_partition_switch is not None:
    #                 cmd_parts.append(
    #                     f"@allow_partition_switch = {1 if allow_partition_switch else 0}"
    #                 )

    #             # Execute the stored procedure
    #             cmd = "\n".join(cmd_parts)
    #             connection.execute(sa.text(cmd))
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(
    #             f"Database error when enabling CDC for table: {str(e)}"
    #         ) from e

    # def disable_cdc_for_table(self, schema_name, table_name, capture_instance=None):
    #     """Disable CDC for a specific table using native CDC stored procedure."""
    #     try:
    #         with self.get_connection() as connection:
    #             if capture_instance is None:
    #                 capture_instance = self.get_capture_instance_name(
    #                     schema_name, table_name
    #                 )

    #                 if not capture_instance:
    #                     return  # CDC not enabled for this table

    #             # Build the command for the stored procedure
    #             cmd_parts = [f"EXEC sys.sp_cdc_disable_table"]
    #             cmd_parts.append(f"@source_schema = N'{schema_name}'")
    #             cmd_parts.append(f"@source_name = N'{table_name}'")

    #             if capture_instance:
    #                 cmd_parts.append(f"@capture_instance = N'{capture_instance}'")

    #             # Execute the stored procedure
    #             cmd = "\n".join(cmd_parts)
    #             connection.execute(sa.text(cmd))
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(
    #             f"Database error when disabling CDC for table: {str(e)}"
    #         ) from e

    # def start_cdc_job(self, job_type="capture"):
    #     """Start a CDC job (capture or cleanup) using native stored procedure."""
    #     try:
    #         with self.get_connection() as connection:
    #             connection.execute(
    #                 sa.text(f"EXEC sys.sp_cdc_start_job @job_type = N'{job_type}'")
    #             )
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(f"Database error when starting CDC job: {str(e)}") from e

    # def stop_cdc_job(self, job_type="capture"):
    #     """Stop a CDC job (capture or cleanup) using native stored procedure."""
    #     try:
    #         with self.get_connection() as connection:
    #             connection.execute(
    #                 sa.text(f"EXEC sys.sp_cdc_stop_job @job_type = N'{job_type}'")
    #             )
    #     except SQLAlchemyError as e:
    #         raise RuntimeError(f"Database error when stopping CDC job: {str(e)}") from e


@resource
def sql_server_cdc_resource(init_context):
    """Dagster resource for SQL Server CDC operations."""
    return SQLServerCDCResource(init_context.resource_config)
