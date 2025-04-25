from typing import Dict, List, Optional
from pydantic import BaseModel, Field, StrictStr

from pyiceberg.table import TableIdentifier
from pyiceberg.table.metadata import TableMetadata


class CreateNamespaceResponse(BaseModel):
    """
    CreateNamespaceResponse
    """  # noqa: E501

    namespace: List[StrictStr] = Field(
        description="Reference to one or more levels of a namespace"
    )
    properties: Optional[Dict[str, StrictStr]] = Field(
        default=None,
        description="Properties stored on the namespace, if supported by the server.",
    )


class ListNamespacesResponse(BaseModel):
    """
    ListNamespacesResponse
    """  # noqa: E501

    # next_page_token: Optional[StrictStr] = Field(default=None, description="An opaque token which allows clients to make use of pagination for a list API (e.g. ListTables). Clients will initiate the first paginated request by sending an empty `pageToken` e.g. `GET /tables?pageToken` or `GET /tables?pageToken=` signaling to the service that the response should be paginated. Servers that support pagination will recognize `pageToken` and return a `next-page-token` in response if there are more results available. After the initial request, it is expected that the value of `next-page-token` from the last response is used in the subsequent request. Servers that do not support pagination will ignore `next-page-token` and return all results.", alias="next-page-token")
    namespaces: Optional[List[List[StrictStr]]] = None


class GetNamespaceResponse(BaseModel):
    """
    GetNamespaceResponse
    """  # noqa: E501

    namespace: List[StrictStr] = Field(
        description="Reference to one or more levels of a namespace"
    )
    properties: Optional[Dict[str, StrictStr]] = Field(
        default=None,
        description="Properties stored on the namespace, if supported by the server. If the server does not support namespace properties, it should return null for this field. If namespace properties are supported, but none are set, it should return an empty object.",
    )


class UpdateNamespacePropertiesResponse(BaseModel):
    """
    UpdateNamespacePropertiesResponse
    """  # noqa: E501

    updated: List[StrictStr] = Field(
        description="List of property keys that were added or updated"
    )
    removed: List[StrictStr] = Field(description="List of properties that were removed")
    missing: Optional[List[StrictStr]] = Field(
        default=None,
        description="List of properties requested for removal that were not found in the namespace's properties. Represents a partial success response. Server's do not need to implement this.",
    )


class ListTablesResponse(BaseModel):
    """
    ListTablesResponse
    """  # noqa: E501

    next_page_token: Optional[StrictStr] = Field(
        default=None,
        description="An opaque token which allows clients to make use of pagination for a list API (e.g. ListTables). Clients will initiate the first paginated request by sending an empty `pageToken` e.g. `GET /tables?pageToken` or `GET /tables?pageToken=` signaling to the service that the response should be paginated. Servers that support pagination will recognize `pageToken` and return a `next-page-token` in response if there are more results available. After the initial request, it is expected that the value of `next-page-token` from the last response is used in the subsequent request. Servers that do not support pagination will ignore `next-page-token` and return all results.",
        alias="next-page-token",
    )
    identifiers: Optional[List[TableIdentifier]] = None


class CommitTableResponse(BaseModel):
    """
    CommitTableResponse
    """  # noqa: E501

    metadata_location: StrictStr = Field()
    metadata: TableMetadata
