from typing import Dict, List, Optional
from pydantic import BaseModel, Field, StrictBool, StrictStr

from pyiceberg.table import TableIdentifier, TableRequirement, TableUpdate
from pyiceberg.schema import Schema
from pyiceberg.partitioning import PartitionSpec
from pyiceberg.table.sorting import SortOrder


class CreateNamespaceRequest(BaseModel):
    """
    CreateNamespaceRequest
    """  # noqa: E501

    namespace: List[StrictStr] = Field(
        description="Reference to one or more levels of a namespace"
    )
    properties: Optional[Dict[str, StrictStr]] = Field(
        default=None,
        description="Configured string to string map of properties for the namespace",
    )


class UpdateNamespacePropertiesRequest(BaseModel):
    """
    UpdateNamespacePropertiesRequest
    """  # noqa: E501

    removals: Optional[List[StrictStr]] = None
    updates: Optional[Dict[str, StrictStr]] = None


class CreateTableRequest(BaseModel):
    """
    CreateTableRequest
    """  # noqa: E501

    name: StrictStr
    location: Optional[StrictStr] = None
    schema: Schema = Field(alias="schema")
    partition_spec: Optional[PartitionSpec] = Field(
        default=None, alias="partition-spec"
    )
    write_order: Optional[SortOrder] = Field(default=None, alias="write-order")
    stage_create: Optional[StrictBool] = Field(default=None, alias="stage-create")
    properties: Optional[Dict[str, StrictStr]] = None


class RegisterTableRequest(BaseModel):
    """
    RegisterTableRequest
    """  # noqa: E501

    name: StrictStr
    metadata_location: StrictStr = Field()


class CommitTableRequest(BaseModel):
    """
    CommitTableRequest
    """  # noqa: E501

    identifier: Optional[TableIdentifier] = None
    requirements: List[TableRequirement]
    updates: List[TableUpdate]


class CommitTransactionRequest(BaseModel):
    """
    CommitTransactionRequest
    """  # noqa: E501

    table_changes: List[CommitTableRequest] = Field(alias="table-changes")


class RenameTableRequest(BaseModel):
    """
    RenameTableRequest
    """  # noqa: E501

    source: TableIdentifier
    destination: TableIdentifier
