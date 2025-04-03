import polars as pl
from typing import List


def process_cdc_changes(cdc_changes: pl.DataFrame, indices: List[str]) -> pl.DataFrame:
    """Efficiently process CDC changes and merge them into the Delta file.
    A CDC Change consists of the following operations:

    - Deleted (__$operation = 1),
    - Inserted (__$operation = 2)
    - Updated Before (__$operation = 3)
    - Updated After (__$operation = 4)

    More info: https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-data-capture-sql-server?view=sql-server-ver16

    Example CDC:

    ```
    Column | Value
    -- | --
    __$start_lsn | 0x00000036000004280010
    -- | --
    __$seqval | 0x00000036000004280003
    __$operation | 1
    __$update_mask | ?
    CustomerID | 1
    FirstName | John
    LastName | Smith
    Email | john.smith.updated@example.com
    CreatedDate | 2025-03-31 07:04:02
    UpdatedDate | 2025-03-31 07:04:02
    ```

    We now perform a merge according to the Delta Lake merge operations (https://delta.io/blog/2023-02-14-delta-lake-merge/) to correctly merge those changes
    into the existing delta lake, reducing the amount of data taken into memory (avoiding a full load of the delta file when possible).

    Args:
        df_current (pl.DataFrame): Current state of Delta data
        cdc_changes (pl.DataFrame): CDC records with '__$operation' column (1=Delete, 2=Insert, 4=Update)
        primary_keys: List of column names comprising the primary key
    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple of DataFrames:
            - Upserts to be applied to the Delta table (inserts and updates)
            - Deletes to be applied to the Delta table
    """
    # Validate keys exist in both datasets
    missing_keys = [
        pk
        for pk in indices
        if pk not in df_current.columns or pk not in cdc_changes.columns
    ]
    if missing_keys:
        raise ValueError(f"Missing primary key columns: {missing_keys}")

    # Process latest state per entity (handling multiple operations)
    latest_changes = cdc_changes.unique(subset=indices, keep="last")

    # Split operations using efficient filtering
    delete_mask = pl.col("__$operation") == 1
    update_mask = pl.col("__$operation") == 4
    insert_mask = pl.col("__$operation") == 2

    deletes = latest_changes.filter(delete_mask)
    updates = latest_changes.filter(update_mask)
    inserts = latest_changes.filter(insert_mask)

    # Apply deletions using composite key anti-join
    current_after_deletes = df_current.join(
        deletes.select(indices), on=indices, how="anti"
    )

    # Process updates through coalesced left join
    if not updates.is_empty():
        update_columns = [col for col in df_current.columns if col not in indices]
        current_after_updates = current_after_deletes.join(
            updates, on=indices, how="left", suffix="_update"
        ).select(
            [
                *indices,
                *[
                    pl.coalesce(pl.col(f"{col}_update"), pl.col(col)).alias(col)
                    for col in update_columns
                ],
            ]
        )
    else:
        current_after_updates = current_after_deletes

    # Handle insert candidates (original inserts + unmatched updates)
    existing_ids = current_after_updates.select(indices)
    insert_candidates = pl.concat(
        [
            inserts.select(df_current.columns),
            updates.join(existing_ids, on=indices, how="anti").select(
                df_current.columns
            ),
        ]
    )

    return pl.concat([current_after_updates, insert_candidates], how="vertical")
