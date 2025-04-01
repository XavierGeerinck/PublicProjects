from dagster import asset, AssetExecutionContext
import polars as pl
import os
from dagster_cdc.constants import PATH_DELTA, LSN_DEFAULT
from dagster_cdc.resources.sql_server_cdc import SQLServerCDCResource
from dagster_cdc.utils.delta_helpers import process_cdc_changes
import dagster as dg


class BaseDeltaAsset:
    """Abstract base class for managing CDC updates to Delta tables."""

    def __init__(self, table_name: str, sql_server_cdc: SQLServerCDCResource):
        self.table_name = table_name
        self.sql_server_cdc = sql_server_cdc
        self.primary_key_columns = sql_server_cdc.get_primary_key_columns(table_name)

    def get_last_lsn(self, context: AssetExecutionContext):
        """Get the last processed LSN from metadata."""
        try:
            # Try to get the dynamic partition using the current API
            partition_key = f"{context.asset_key.path[-1]}_lsn"
            partitions = context.instance.get_dynamic_partitions(partition_key)
            return partitions[0] if partitions else LSN_DEFAULT
        except TypeError:
            # Fallback for older Dagster versions
            context.log.warning("Using fallback method for LSN tracking")
            return LSN_DEFAULT

    def extract_row(self, change):
        """Extract relevant columns from the change DataFrame."""
        return {col: change[col] for col in change.index if not col.startswith("__$")}

    # Remove the get_primary_key method as it's no longer needed


def delta_load_full(
    context: AssetExecutionContext,
    sql_server_cdc: SQLServerCDCResource,
    table_name,
    delta_path,
    last_lsn,
):
    """Load the full table from SQL Server into Delta Lake."""
    context.log.info(
        f"Performing full copy of `dbo.{table_name}` (last_lsn='{last_lsn}', delta_path='{delta_path}')"
    )

    full_df = sql_server_cdc.get_full_table_data(table_name)

    # Get the current LSN after the full load
    current_lsn = sql_server_cdc.lsn_to_hex_string(sql_server_cdc.get_current_lsn())

    # Store the LSN with the correct partition key
    partition_key = f"{context.asset_key.path[-1]}_lsn"
    try:
        context.instance.add_dynamic_partitions(partition_key, [str(current_lsn)])
    except Exception as e:
        context.log.warning(f"Failed to store LSN: {e}")

    # # Convert timestamp columns to compatible format for Delta Lake
    # for col in full_df.select_dtypes(include=["datetime64[ns]"]).columns:
    #     full_df[col] = full_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    context.log.info(f"Initial load complete for {table_name} with {len(full_df)} rows")

    return full_df


def delta_load_upsert(
    context: AssetExecutionContext,
    sql_server_cdc: SQLServerCDCResource,
    table_name,
    delta_path,
    last_lsn,
):
    context.log.info(
        f"Upserting changes of `dbo.{table_name}` into delta_path='{delta_path}' (last_lsn='{last_lsn}')"
    )

    # Load the existing data
    current_data = pl.read_delta(delta_path)

    # Only get changes if we have an existing delta file
    cdc_df, current_lsn = sql_server_cdc.get_table_changes(table_name, last_lsn)

    # If no changes, skip
    if cdc_df.is_empty():
        context.log.info(f"No changes found for {table_name}")
        return pl.read_delta(delta_path)

    if "__$operation" not in cdc_df.columns:
        context.log.info(f"No changes found for {table_name}")
        return pl.read_delta(delta_path)

    # Process CDC changes, create a new DF of changes and merge them into the delta file.
    # this merge operation happens through the IO Manager, thus we just return the DF with our changes.
    # @todo: what about DELETE operations here? This is practically an UPSERT
    new_data = process_cdc_changes(current_data, cdc_df)

    # Update the last processed LSN
    context.instance.add_dynamic_partitions(
        partition_key="last_lsn",
        partitions=[str(current_lsn)],
    )

    # Store the updated LSN with the correct partition key
    partition_key = f"{context.asset_key.path[-1]}_lsn"
    try:
        context.instance.add_dynamic_partitions(partition_key, [str(current_lsn)])
    except Exception as e:
        context.log.warning(f"Failed to store LSN: {e}")

    return new_data


def create_delta_asset(table_name):
    """Factory function to create delta assets for different tables."""

    @asset(
        name=f"{table_name.lower()}_delta",
        group_name="cdc",
        io_manager_key="delta_io_manager",
        required_resource_keys={"sql_server_cdc"},
    )
    def delta_asset(context: AssetExecutionContext):
        """Asset that tracks changes to the table and writes to Delta Lake."""
        # Get the sql_server_cdc from resources
        sql_server_cdc = context.resources.sql_server_cdc
        delta_asset = BaseDeltaAsset(table_name, sql_server_cdc)

        last_lsn = delta_asset.get_last_lsn(context)
        context.log.info(f"Processing changes for {table_name} since LSN: {last_lsn}")

        res = pl.DataFrame()

        try:
            delta_path = f"{PATH_DELTA}/public/{table_name.lower()}_delta"

            # If the table is empty or the Delta table doesn't exist, perform an initial load
            if last_lsn == LSN_DEFAULT or not os.path.exists(delta_path):
                res = delta_load_full(
                    context, sql_server_cdc, table_name, delta_path, last_lsn
                )
            else:
                res = delta_load_upsert(
                    context, sql_server_cdc, table_name, delta_path, last_lsn
                )

        except Exception as e:
            raise e

        # context.add_output_metadata({"merge_predicate_2": "s.CustomerID = t.CustomerID"})

        return dg.Output(
            value=res,
            metadata={"merge_predicate": "s.CustomerID = t.CustomerID"},
        )

    return delta_asset


# Create assets with their primary keys
CustomersDelta = create_delta_asset("Customers")
OrdersDelta = create_delta_asset("Orders")
