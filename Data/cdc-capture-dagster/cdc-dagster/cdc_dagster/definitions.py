from dagster import Definitions
from dagster_delta import (
    LocalConfig,
    WriteMode,
    MergeConfig,
    MergeType,
    DeltaLakePolarsIOManager,
)
from cdc_dagster.assets.delta_assets import CustomersDelta, OrdersDelta
from cdc_dagster.resources.sql_server_cdc import (
    SQLServerCDCResource,
    SQLServerCDCConfig,
)
from cdc_dagster.constants import PATH_DELTA


defs = Definitions(
    assets=[CustomersDelta, OrdersDelta],
    resources={
        "sql_server_cdc": SQLServerCDCResource(SQLServerCDCConfig()),
        "delta_io_manager": DeltaLakePolarsIOManager(
            root_uri=PATH_DELTA,
            storage_options=LocalConfig(),
            # We use a community package, but it will go to main
            # it's also backed by the delta-rs maintainer
            # https://github.com/dagster-io/dagster/issues/27744
            #
            # Opened issue for example:
            # https://github.com/ASML-Labs/dagster-delta/issues/23
            mode=WriteMode.merge,
            merge_config=MergeConfig(
                # Delete unmatched rows in the target table
                # this is thus a full compare
                merge_type=MergeType.replace_delete_unmatched,
                # The predicate to match (note: extra ones will be added based on partition)
                # predicate="target.id = source.id",
            ),
        ),
    },
)
