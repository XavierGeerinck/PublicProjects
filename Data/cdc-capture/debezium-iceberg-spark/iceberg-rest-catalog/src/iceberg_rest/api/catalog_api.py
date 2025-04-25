from fastapi import APIRouter, Depends
from typing import Any, Dict, Optional, Union

from fastapi import Body, Path, Query
from pydantic import BaseModel, Field, StrictStr

from iceberg_rest.catalog import get_catalog
from iceberg_rest.exception import IcebergHTTPException
from pyiceberg.table import TableIdentifier
from pyiceberg.table.metadata import TableMetadata
from pyiceberg.exceptions import (
    TableAlreadyExistsError,
    NoSuchTableError,
    NamespaceAlreadyExistsError,
    NoSuchNamespaceError,
    NamespaceNotEmptyError,
    CommitFailedException,
)
from pyiceberg.table.sorting import UNSORTED_SORT_ORDER
from pyiceberg.typedef import Identifier

from iceberg_rest.models.config import CatalogConfig
from iceberg_rest.models.request import (
    CommitTableRequest,
    CommitTransactionRequest,
    CreateNamespaceRequest,
    CreateTableRequest,
    RegisterTableRequest,
    RenameTableRequest,
    UpdateNamespacePropertiesRequest,
)
from iceberg_rest.models.response import (
    CommitTableResponse,
    CreateNamespaceResponse,
    GetNamespaceResponse,
    ListNamespacesResponse,
    ListTablesResponse,
    UpdateNamespacePropertiesResponse,
)

from pyiceberg.catalog import Catalog


router = APIRouter(dependencies=[Depends(get_catalog)])


@router.get("/reset")
def reset(catalog: Catalog = Depends(get_catalog)):
    catalog.destroy_tables()
    catalog.create_tables()
    return {"status": "ok"}


# /v1/config
@router.get(
    "/v1/config",
    tags=["Configuration API"],
    summary="List all catalog configuration settings",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def get_config(
    warehouse: str = Query(
        None,
        description="Warehouse location or identifier to request from the service",
        alias="warehouse",
    ),
) -> CatalogConfig:
    """All REST clients should first call this route to get catalog configuration properties from the server to configure the catalog and its HTTP client. Configuration from the server consists of two sets of key/value pairs. - defaults -  properties that should be used as default configuration; applied before client configuration - overrides - properties that should be used to override client configuration; applied after defaults and client configuration  Catalog configuration is constructed by setting the defaults, then client- provided configuration, and finally overrides. The final property set is then used to configure the catalog.  For example, a default configuration property might set the size of the client pool, which can be replaced with a client-specific setting. An override might be used to set the warehouse location, which is stored on the server rather than in client configuration.  Common catalog configuration settings are documented at https://iceberg.apache.org/docs/latest/configuration/#catalog-properties"""
    return CatalogConfig(overrides={}, defaults={})


# /v1/{prefix}/namespaces
@router.post(
    "/v1/namespaces",
    tags=["Catalog API"],
    summary="Create a namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def create_namespace(
    create_namespace_request: CreateNamespaceRequest = Body(None, description=""),
    catalog: Catalog = Depends(get_catalog),
) -> CreateNamespaceResponse:
    """Create a namespace, with an optional set of properties. The server might also add properties, such as &#x60;last_modified_time&#x60; etc."""
    namespace = tuple(create_namespace_request.namespace)
    properties = create_namespace_request.properties
    try:
        catalog.create_namespace(namespace, properties)
    except NamespaceAlreadyExistsError:
        raise IcebergHTTPException(
            status_code=409, detail=f"Namespace already exists: {namespace}"
        )
    return CreateNamespaceResponse(namespace=namespace, properties=properties)


@router.get(
    "/v1/namespaces",
    tags=["Catalog API"],
    summary="List namespaces, optionally providing a parent namespace to list underneath",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def list_namespaces(
    parent: str = Query(
        None,
        description="An optional namespace, underneath which to list namespaces. If not provided or empty, all top-level namespaces should be listed. If parent is a multipart namespace, the parts must be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
        alias="parent",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> ListNamespacesResponse:
    """List all namespaces at a certain level, optionally starting from a given parent namespace. If table accounting.tax.paid.info exists, using &#39;SELECT NAMESPACE IN accounting&#39; would translate into &#x60;GET /namespaces?parent&#x3D;accounting&#x60; and must return a namespace, [\&quot;accounting\&quot;, \&quot;tax\&quot;] only. Using &#39;SELECT NAMESPACE IN accounting.tax&#39; would translate into &#x60;GET /namespaces?parent&#x3D;accounting%1Ftax&#x60; and must return a namespace, [\&quot;accounting\&quot;, \&quot;tax\&quot;, \&quot;paid\&quot;]. If &#x60;parent&#x60; is not provided, all top-level namespaces should be listed."""
    try:
        namespaces = catalog.list_namespaces(parent)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {parent}"
        )
    return ListNamespacesResponse(namespaces=namespaces)


# /v1/{prefix}/namespaces/{namespace}
@router.get(
    "/v1/namespaces/{namespace}",
    tags=["Catalog API"],
    summary="Load the metadata properties for a namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def load_namespace_metadata(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> GetNamespaceResponse:
    """Return all stored metadata properties for a given namespace"""
    namespace_tuple = (namespace,)
    try:
        properties = catalog.load_namespace_properties(namespace=namespace_tuple)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace_tuple}"
        )
    return GetNamespaceResponse(namespace=namespace_tuple, properties=properties)


@router.delete(
    "/v1/namespaces/{namespace}",
    tags=["Catalog API"],
    summary="Drop a namespace from the catalog. Namespace must be empty.",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def drop_namespace(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> None:
    namespace_tuple = (namespace,)
    try:
        catalog.drop_namespace(namespace_tuple)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace_tuple}"
        )
    except NamespaceNotEmptyError:
        raise IcebergHTTPException(
            status_code=409, detail=f"Namespace is not empty: {namespace_tuple}"
        )


@router.head(
    "/v1/namespaces/{namespace}",
    tags=["Catalog API"],
    summary="Check if a namespace exists",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def namespace_exists(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> None:
    """Check if a namespace exists. The response does not contain a body."""
    try:
        catalog.load_namespace_properties(namespace=namespace)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace}"
        )


# /v1/{prefix}/namespaces/{namespace}/properties
@router.post(
    "/v1/namespaces/{namespace}/properties",
    tags=["Catalog API"],
    summary="Set or remove properties on a namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def update_namespace_properties(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    update_namespace_properties_request: UpdateNamespacePropertiesRequest = Body(
        None, description=""
    ),
    catalog: Catalog = Depends(get_catalog),
) -> UpdateNamespacePropertiesResponse:
    """Set and/or remove properties on a namespace. The request body specifies a list of properties to remove and a map of key value pairs to update. Properties that are not in the request are not modified or removed by this call. Server implementations are not required to support namespace properties."""
    namespace_tuple = (namespace,)
    try:
        summary = catalog.update_namespace_properties(
            namespace=namespace_tuple,
            removals=set(update_namespace_properties_request.removals),
            updates=update_namespace_properties_request.updates,
        )
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace_tuple}"
        )
    return UpdateNamespacePropertiesResponse(
        updated=sorted(summary.updated),
        removed=sorted(summary.removed),
        missing=sorted(summary.missing),
    )


# /v1/{prefix}/namespaces/{namespace}/tables
@router.get(
    "/v1/namespaces/{namespace}/tables",
    tags=["Catalog API"],
    summary="List all table identifiers underneath a given namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def list_tables(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> ListTablesResponse:
    """Return all table identifiers under this namespace"""
    try:
        identifiers = catalog.list_tables(namespace=namespace)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace}"
        )
    table_identifiers = [
        TableIdentifier(namespace=[identifier[0]], name=identifier[1])
        for identifier in identifiers
    ]
    return ListTablesResponse(identifiers=table_identifiers)


class LoadTableResult(BaseModel):
    """
    Result used when a table is successfully loaded.   The table metadata JSON is returned in the `metadata` field. The corresponding file location of table metadata should be returned in the `metadata-location` field, unless the metadata is not yet committed. For example, a create transaction may return metadata that is staged but not committed. Clients can check whether metadata has changed by comparing metadata locations after the table has been created.   The `config` map returns table-specific configuration for the table's resources, including its HTTP client and FileIO. For example, config may contain a specific FileIO implementation class for the table depending on its underlying storage.   The following configurations should be respected by clients:  ## General Configurations  - `token`: Authorization bearer token to use for table requests if OAuth2 security is enabled   ## AWS Configurations  The following configurations should be respected when working with tables stored in AWS S3  - `client.region`: region to configure client for making requests to AWS  - `s3.access-key-id`: id for for credentials that provide access to the data in S3  - `s3.secret-access-key`: secret for credentials that provide access to data in S3   - `s3.session-token`: if present, this value should be used for as the session token   - `s3.remote-signing-enabled`: if `true` remote signing should be performed as described in the `s3-signer-open-api.yaml` specification
    """  # noqa: E501

    metadata_location: Optional[StrictStr] = Field(
        default=None,
        description="May be null if the table is staged as part of a transaction",
    )
    metadata: TableMetadata
    config: Optional[Dict[str, StrictStr]] = None


@router.post(
    "/v1/namespaces/{namespace}/tables",
    tags=["Catalog API"],
    summary="Create a table in the given namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def create_table(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    create_table_request: CreateTableRequest = Body(None, description=""),
    catalog: Catalog = Depends(get_catalog),
) -> LoadTableResult:
    """Create a table or start a create transaction, like atomic CTAS.  If &#x60;stage-create&#x60; is false, the table is created immediately.  If &#x60;stage-create&#x60; is true, the table is not created, but table metadata is initialized and returned. The service should prepare as needed for a commit to the table commit endpoint to complete the create transaction. The client uses the returned metadata to begin a transaction. To commit the transaction, the client sends all create and subsequent changes to the table commit route. Changes from the table create operation include changes like AddSchemaUpdate and SetCurrentSchemaUpdate that set the initial table state."""
    identifier = (namespace, create_table_request.name)
    if create_table_request.stage_create:
        return _stage_create_table(catalog, identifier, create_table_request)
    else:
        return _create_table(catalog, identifier, create_table_request)


def _stage_create_table(
    catalog: Catalog,
    identifier: Union[str, Identifier],
    create_table_request: CreateTableRequest,
) -> LoadTableResult:
    try:
        sort_order = (
            create_table_request.write_order
            if create_table_request.write_order is not None
            else UNSORTED_SORT_ORDER
        )
        tbl = catalog.create_table(
            identifier=identifier,
            schema=create_table_request.schema,
            location=create_table_request.location,
            partition_spec=create_table_request.partition_spec,
            sort_order=sort_order,
            properties=create_table_request.properties,
        )
        # (TODO): temp fix, create/then remove table
        catalog.drop_table(identifier)
    except TableAlreadyExistsError:
        raise IcebergHTTPException(
            status_code=409, detail=f"Table already exists: {identifier}"
        )
    return LoadTableResult(
        metadata_location=tbl.metadata_location,
        metadata=tbl.metadata,
        config=tbl.properties,
    )


def _create_table(
    catalog: Catalog,
    identifier: Union[str, Identifier],
    create_table_request: CreateTableRequest,
) -> LoadTableResult:
    try:
        sort_order = (
            create_table_request.write_order
            if create_table_request.write_order is not None
            else UNSORTED_SORT_ORDER
        )
        tbl = catalog.create_table(
            identifier=identifier,
            schema=create_table_request.schema,
            location=create_table_request.location,
            partition_spec=create_table_request.partition_spec,
            sort_order=sort_order,
            properties=create_table_request.properties,
        )
    except TableAlreadyExistsError:
        raise IcebergHTTPException(
            status_code=409, detail=f"Table already exists: {identifier}"
        )
    return LoadTableResult(
        metadata_location=tbl.metadata_location,
        metadata=tbl.metadata,
        config=tbl.properties,
    )


# /v1/{prefix}/namespaces/{namespace}/register
@router.post(
    "/v1/namespaces/{namespace}/register",
    tags=["Catalog API"],
    summary="Register a table in the given namespace using given metadata file location",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def register_table(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    register_table_request: RegisterTableRequest = Body(None, description=""),
    catalog: Catalog = Depends(get_catalog),
) -> LoadTableResult:
    """Register a table using given metadata file location."""
    try:
        tbl = catalog.register_table(
            identifier=(namespace, register_table_request.name),
            metadata_location=register_table_request.metadata_location,
        )
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {namespace}"
        )
    except TableAlreadyExistsError:
        raise IcebergHTTPException(
            status_code=409,
            detail=f"Table already exists: {(namespace, register_table_request.name)}",
        )
    return LoadTableResult(
        metadata_location=tbl.metadata_location,
        metadata=tbl.metadata,
        config=tbl.properties,
    )


# /v1/{prefix}/namespaces/{namespace}/tables/{table}
@router.get(
    "/v1/namespaces/{namespace}/tables/{table}",
    tags=["Catalog API"],
    summary="Load a table from the catalog",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def load_table(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    table: str = Path(..., description="A table name"),
    catalog: Catalog = Depends(get_catalog),
) -> LoadTableResult:
    """Load a table from the catalog.  The response contains both configuration and table metadata. The configuration, if non-empty is used as additional configuration for the table that overrides catalog configuration. For example, this configuration may change the FileIO implementation to be used for the table.  The response also contains the table&#39;s full metadata, matching the table metadata JSON file.  The catalog configuration may contain credentials that should be used for subsequent requests for the table. The configuration key \&quot;token\&quot; is used to pass an access token to be used as a bearer token for table requests. Otherwise, a token may be passed using a RFC 8693 token type as a configuration key. For example, \&quot;urn:ietf:params:oauth:token-type:jwt&#x3D;&lt;JWT-token&gt;\&quot;."""
    try:
        identifier = (namespace, table)
        tbl = catalog.load_table(identifier=identifier)
    except NoSuchTableError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Table does not exist: {identifier}"
        )
    return LoadTableResult(
        metadata_location=tbl.metadata_location,
        metadata=tbl.metadata,
        config=tbl.properties,
    )


@router.post(
    "/v1/namespaces/{namespace}/tables/{table}",
    tags=["Catalog API"],
    summary="Commit updates to a table",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def update_table(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    table: str = Path(..., description="A table name"),
    commit_table_request: CommitTableRequest = Body(None, description=""),
    catalog: Catalog = Depends(get_catalog),
) -> CommitTableResponse:
    """Commit updates to a table.  Commits have two parts, requirements and updates. Requirements are assertions that will be validated before attempting to make and commit changes. For example, &#x60;assert-ref-snapshot-id&#x60; will check that a named ref&#39;s snapshot ID has a certain value.  Updates are changes to make to table metadata. For example, after asserting that the current main ref is at the expected snapshot, a commit may add a new child snapshot and set the ref to the new snapshot id.  Create table transactions that are started by createTable with &#x60;stage-create&#x60; set to true are committed using this route. Transactions should include all changes to the table, including table initialization, like AddSchemaUpdate and SetCurrentSchemaUpdate. The &#x60;assert-create&#x60; requirement is used to ensure that the table was not created concurrently."""
    try:
        if commit_table_request.identifier is None:
            commit_table_request.identifier = TableIdentifier(
                namespace=[namespace], name=table
            )
        resp = catalog._commit_table(commit_table_request)
    except NoSuchTableError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Table does not exist: {(namespace, table)}"
        )
    except CommitFailedException as e:
        raise IcebergHTTPException(
            status_code=409, detail=f"Commit failed: {(namespace, table)}, Error: {e}"
        )
    return resp


@router.delete(
    "/v1/namespaces/{namespace}/tables/{table}",
    tags=["Catalog API"],
    summary="Drop a table from the catalog",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def drop_table(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    table: str = Path(..., description="A table name"),
    catalog: Catalog = Depends(get_catalog),
) -> None:
    """Remove a table from the catalog"""
    try:
        catalog.drop_table(identifier=(namespace, table))
    except NoSuchTableError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Table does not exist: {(namespace, table)}"
        )


@router.head(
    "/v1/namespaces/{namespace}/tables/{table}",
    tags=["Catalog API"],
    summary="Check if a table exists",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def table_exists(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    table: str = Path(..., description="A table name"),
    catalog: Catalog = Depends(get_catalog),
) -> None:
    """Check if a table exists within a given namespace. The response does not contain a body."""
    try:
        catalog.load_table(identifier=(namespace, table))
    except NoSuchTableError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Table does not exist: {(namespace, table)}"
        )


# /v1/{prefix}/transactions/commit
@router.post(
    "/v1/{prefix}/transactions/commit",
    tags=["Catalog API"],
    summary="Commit updates to multiple tables in an atomic operation",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def commit_transaction(
    commit_transaction_request: CommitTransactionRequest = Body(
        None,
        description="Commit updates to multiple tables in an atomic operation  A commit for a single table consists of a table identifier with requirements and updates. Requirements are assertions that will be validated before attempting to make and commit changes. For example, &#x60;assert-ref-snapshot-id&#x60; will check that a named ref&#39;s snapshot ID has a certain value.  Updates are changes to make to table metadata. For example, after asserting that the current main ref is at the expected snapshot, a commit may add a new child snapshot and set the ref to the new snapshot id.",
    ),
) -> None: ...


# /v1/{prefix}/tables/rename
@router.post(
    "/v1/tables/rename",
    tags=["Catalog API"],
    summary="Rename a table from its current name to a new name",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def rename_table(
    rename_table_request: RenameTableRequest = Body(
        None,
        description="Current table identifier to rename and new table identifier to rename to",
    ),
    catalog: Catalog = Depends(get_catalog),
) -> None:
    """Rename a table from one identifier to another. It&#39;s valid to move a table across namespaces, but the server implementation is not required to support it."""
    source = (
        ".".join(rename_table_request.source.namespace.root),
        rename_table_request.source.name,
    )
    destination = (
        ".".join(rename_table_request.destination.namespace.root),
        rename_table_request.destination.name,
    )
    try:
        catalog.rename_table(source, destination)
    except NoSuchNamespaceError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Namespace does not exist: {source}"
        )
    except NoSuchTableError:
        raise IcebergHTTPException(
            status_code=404, detail=f"Table does not exist: {source}"
        )
    except TableAlreadyExistsError:
        raise IcebergHTTPException(
            status_code=409, detail=f"Table already exists: {destination}"
        )


# /v1/{prefix}/namespaces/{namespace}/tables/{table}/metrics
@router.post(
    "/v1/namespaces/{namespace}/tables/{table}/metrics",
    tags=["Catalog API"],
    summary="Send a metrics report to this endpoint to be processed by the backend",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def report_metrics(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    table: str = Path(..., description="A table name"),
    report_metrics_request: Any = Body(
        None, description="The request containing the metrics report to be sent"
    ),
) -> None: ...


# /v1/oauth/tokens
# /v1/{prefix}/namespaces/{namespace}/views
@router.get(
    "/v1/namespaces/{namespace}/views",
    tags=["Catalog API"],
    summary="List all view identifiers underneath a given namespace",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def list_views(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
) -> ListTablesResponse:
    # (TODO): implement this!
    """Return all view identifiers under this namespace"""
    namespace_tuple = (namespace,)
    raise IcebergHTTPException(
        status_code=404, detail=f"Namespace does not exist: {namespace_tuple}"
    )


# /v1/{prefix}/namespaces/{namespace}/views/{view}
@router.get(
    "/v1/namespaces/{namespace}/views/{view}",
    tags=["Catalog API"],
    summary="Load a view from the catalog",
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def load_view(
    namespace: str = Path(
        ...,
        description="A namespace identifier as a single string. Multipart namespace parts should be separated by the unit separator (&#x60;0x1F&#x60;) byte.",
    ),
    view: str = Path(..., description="A view name"),
) -> None:
    # (TODO): implement this! should return LoadViewResult
    namespace_tuple = (namespace,)
    """Load a view from the catalog.  The response contains both configuration and view metadata. The configuration, if non-empty is used as additional configuration for the view that overrides catalog configuration.  The response also contains the view&#39;s full metadata, matching the view metadata JSON file.  The catalog configuration may contain credentials that should be used for subsequent requests for the view. The configuration key \&quot;token\&quot; is used to pass an access token to be used as a bearer token for view requests. Otherwise, a token may be passed using a RFC 8693 token type as a configuration key. For example, \&quot;urn:ietf:params:oauth:token-type:jwt&#x3D;&lt;JWT-token&gt;\&quot;."""
    raise IcebergHTTPException(
        status_code=404, detail=f"Namespace does not exist: {namespace_tuple}"
    )


# /v1/{prefix}/views/rename
