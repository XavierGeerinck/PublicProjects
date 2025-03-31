import polars as pl


def process_cdc_changes(
    df_current: pl.DataFrame, cdc_changes: pl.DataFrame
) -> pl.DataFrame:
    """Process CDC changes on the current dataframe and return an updated dataframe.
    Ideally we will process a beautiful merge (todo: https://github.com/ASML-Labs/dagster-delta/issues/23#issuecomment-2766547141)

    Example CDC:

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

    Args:
        df_current (pl.DataFrame): The current dataframe.
        cdc_changes (pl.DataFrame): The CDC changes dataframe.
    Returns:
        pl.DataFrame: The updated dataframe.
    """
    try:
        df_new = df_current.clone()

        # Primary Keys (find them)
        primary_key_columns = [
            col for col in df_current.columns if col.startswith("__$")
        ]

        for _, change in cdc_changes.iterrows():
            if change["__$operation"] == 1:  # Delete
                df_current = df_current[df_current[primary_key] != change[primary_key]]
            elif change["__$operation"] == 2:  # Insert
                current_data = pl.concat(
                    [current_data, change.to_frame().T], ignore_index=True
                )
            elif change["__$operation"] in (3, 4):  # Update
                current_data = current_data[
                    current_data[primary_key] != change[primary_key]
                ]
                current_data = pl.concat(
                    [current_data, change.to_frame().T], ignore_index=True
                )
        write_delta_table(current_data, delta_path)
    except Exception as e:
        raise RuntimeError(f"Error during upsert operation: {e}")

    # for _, change in cdc_df.iterrows():
    #     operation = change["__$operation"]
    #     customer_id = change["CustomerID"]

    #     if operation == 1:  # Delete
    #         if not current_data.empty:
    #             current_data = current_data[current_data["CustomerID"] != customer_id]

    #     elif operation == 2:  # Insert
    #         # Create a new row from the CDC change
    #         new_row = {
    #             col: change[col] for col in change.index if not col.startswith("__$")
    #         }
    #         current_data = pd.concat(
    #             [current_data, pd.DataFrame([new_row])], ignore_index=True
    #         )

    #     elif operation in (3, 4):  # Update (before or after)
    #         if operation == 4:  # After update
    #             # Remove the old record
    #             if not current_data.empty:
    #                 current_data = current_data[
    #                     current_data["CustomerID"] != customer_id
    #                 ]
    #             # Add the new record
    #             new_row = {
    #                 col: change[col]
    #                 for col in change.index
    #                 if not col.startswith("__$")
    #             }
    #             current_data = pd.concat(
    #                 [current_data, pd.DataFrame([new_row])], ignore_index=True
    #             )

    # def update_delta_table(
    #     self,
    #     context: AssetExecutionContext,
    #     changes_df: pl.DataFrame,
    #     current_data: pl.DataFrame,
    # ):
    #     """Process CDC changes and update the Delta table."""
    #     # Convert Polars DataFrame to pandas for easier row iteration
    #     changes_pd = changes_df.to_pandas()

    #     for _, change in changes_pd.iterrows():
    #         operation = change["__$operation"]

    #         # Create filter condition for primary key matching
    #         filter_condition = None
    #         for pk_col in self.primary_key_columns:
    #             pk_value = change[pk_col]
    #             col_condition = current_data[pk_col] == pk_value
    #             if filter_condition is None:
    #                 filter_condition = col_condition
    #             else:
    #                 filter_condition = filter_condition & col_condition

    #         if operation == 1:  # Delete
    #             if filter_condition is not None:
    #                 current_data = current_data.filter(~filter_condition)

    #         elif operation == 2:  # Insert
    #             new_row = self.extract_row(change)
    #             current_data = pl.concat(
    #                 [current_data, pl.DataFrame([new_row])], how="diagonal"
    #             )

    #         elif operation in (3, 4):  # Update (before or after)
    #             if operation == 4:  # After update
    #                 if filter_condition is not None:
    #                     current_data = current_data.filter(~filter_condition)
    #                 new_row = self.extract_row(change)
    #                 current_data = pl.concat(
    #                     [current_data, pl.DataFrame([new_row])], how="diagonal"
    #                 )

    #     return current_data
