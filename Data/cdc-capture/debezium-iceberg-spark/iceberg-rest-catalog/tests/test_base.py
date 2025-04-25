#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
# pylint:disable=redefined-outer-name


from pathlib import PosixPath
from typing import (
    Union,
)

import pyarrow as pa
import pytest
import requests
from iceberg_rest.settings import settings
from pydantic_core import ValidationError
from pyiceberg.catalog import (
    Catalog,
    PropertiesUpdateSummary,
)
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import (
    NamespaceAlreadyExistsError,
    NamespaceNotEmptyError,
    NoSuchNamespaceError,
    NoSuchTableError,
    TableAlreadyExistsError,
)
from pyiceberg.io import WAREHOUSE
from pyiceberg.partitioning import (
    PartitionField,
    PartitionSpec,
)
from pyiceberg.schema import Schema
from pyiceberg.table import (
    AddSchemaUpdate,
    CommitTableRequest,
    Namespace,
    SetCurrentSchemaUpdate,
    Table,
    TableIdentifier,
)
from pyiceberg.transforms import IdentityTransform
from pyiceberg.typedef import EMPTY_DICT, Properties
from pyiceberg.types import IntegerType, LongType, NestedField
from pytest_lazyfixture import lazy_fixture

# To run this test, you need to start the REST server in terminal,
# CATALOG_CONFIG='{"warehouse": "file:///tmp/warehouse"}' fastapi dev main.py
REST_ENDPOINT = "http://127.0.0.1:8000/"
DEFAULT_WAREHOUSE_LOCATION = "file:///tmp/warehouse"


@pytest.fixture
def catalog(tmp_path: PosixPath):
    catalog = RestCatalog(
        # (TODO): this needs to be the same as the REST server name because the catalog name is part of the identifier
        settings.CATALOG_NAME,
        **{
            "uri": REST_ENDPOINT,
            WAREHOUSE: settings.CATALOG_WAREHOUSE,
            "test.key": "test.value",
        },
    )
    yield catalog
    # reset the catalog for each test
    requests.get(f"{REST_ENDPOINT}/reset")


TEST_TABLE_IDENTIFIER = (settings.CATALOG_NAME, "my_table")
TEST_TABLE_NAMESPACE = (settings.CATALOG_NAME,)
TEST_TABLE_NAME = "my_table"
TEST_TABLE_SCHEMA = Schema(
    NestedField(1, "x", LongType(), required=True),
    NestedField(2, "y", LongType(), doc="comment", required=True),
    NestedField(3, "z", LongType(), required=True),
)
TEST_TABLE_PARTITION_SPEC = PartitionSpec(
    PartitionField(name="x", transform=IdentityTransform(), source_id=1, field_id=1000)
)
TEST_TABLE_PROPERTIES = {"key1": "value1", "key2": "value2"}
NO_SUCH_TABLE_ERROR = "Table does not exist: \\('default', 'my_table'\\)"
TABLE_ALREADY_EXISTS_ERROR = "Table already exists: \\('default', 'my_table'\\)"
NAMESPACE_ALREADY_EXISTS_ERROR = "Namespace already exists: \\('default',\\)"
NO_SUCH_NAMESPACE_ERROR = "Namespace does not exist: \\('default',\\)"
NAMESPACE_NOT_EMPTY_ERROR = "Namespace is not empty: \\('default',\\)"


def given_catalog_has_a_table(
    catalog: Catalog,
    properties: Properties = EMPTY_DICT,
) -> Table:
    catalog.create_namespace(TEST_TABLE_NAMESPACE)
    return catalog.create_table(
        identifier=TEST_TABLE_IDENTIFIER,
        schema=TEST_TABLE_SCHEMA,
        partition_spec=TEST_TABLE_PARTITION_SPEC,
        properties=properties or TEST_TABLE_PROPERTIES,
    )


def test_namespace_from_tuple() -> None:
    # Given
    identifier = ("com", "organization", "department", "my_table")
    # When
    namespace_from = Catalog.namespace_from(identifier)
    # Then
    assert namespace_from == ("com", "organization", "department")


def test_namespace_from_str() -> None:
    # Given
    identifier = "com.organization.department.my_table"
    # When
    namespace_from = Catalog.namespace_from(identifier)
    # Then
    assert namespace_from == ("com", "organization", "department")


def test_name_from_tuple() -> None:
    # Given
    identifier = ("com", "organization", "department", "my_table")
    # When
    name_from = Catalog.table_name_from(identifier)
    # Then
    assert name_from == "my_table"


def test_name_from_str() -> None:
    # Given
    identifier = "com.organization.department.my_table"
    # When
    name_from = Catalog.table_name_from(identifier)
    # Then
    assert name_from == "my_table"


def test_create_table(catalog: Catalog) -> None:
    catalog.create_namespace(TEST_TABLE_NAMESPACE)
    table = catalog.create_table(
        identifier=TEST_TABLE_IDENTIFIER,
        schema=TEST_TABLE_SCHEMA,
        partition_spec=TEST_TABLE_PARTITION_SPEC,
        properties=TEST_TABLE_PROPERTIES,
    )
    assert catalog.load_table(TEST_TABLE_IDENTIFIER) == table


def test_create_table_location_override(catalog: Catalog) -> None:
    catalog.create_namespace(TEST_TABLE_NAMESPACE)
    new_location = (
        f"{catalog.properties.get(WAREHOUSE, DEFAULT_WAREHOUSE_LOCATION)}/new_location"
    )
    table = catalog.create_table(
        identifier=TEST_TABLE_IDENTIFIER,
        schema=TEST_TABLE_SCHEMA,
        location=new_location,
        partition_spec=TEST_TABLE_PARTITION_SPEC,
        properties=TEST_TABLE_PROPERTIES,
    )
    assert catalog.load_table(TEST_TABLE_IDENTIFIER) == table
    assert table.location() == new_location


def test_create_table_removes_trailing_slash_from_location(catalog: Catalog) -> None:
    catalog.create_namespace(TEST_TABLE_NAMESPACE)
    new_location = (
        f"{catalog.properties.get(WAREHOUSE, DEFAULT_WAREHOUSE_LOCATION)}/new_location"
    )
    table = catalog.create_table(
        identifier=TEST_TABLE_IDENTIFIER,
        schema=TEST_TABLE_SCHEMA,
        location=f"{new_location}/",
        partition_spec=TEST_TABLE_PARTITION_SPEC,
        properties=TEST_TABLE_PROPERTIES,
    )
    assert catalog.load_table(TEST_TABLE_IDENTIFIER) == table
    assert table.location() == new_location


@pytest.mark.parametrize(
    "schema,expected",
    [
        (
            lazy_fixture("pyarrow_schema_simple_without_ids"),
            lazy_fixture("iceberg_schema_simple_no_ids"),
        ),
        (lazy_fixture("iceberg_schema_simple"), lazy_fixture("iceberg_schema_simple")),
        (lazy_fixture("iceberg_schema_nested"), lazy_fixture("iceberg_schema_nested")),
        (
            lazy_fixture("pyarrow_schema_nested_without_ids"),
            lazy_fixture("iceberg_schema_nested_no_ids"),
        ),
    ],
)
def test_convert_schema_if_needed(
    schema: Union[Schema, pa.Schema],
    expected: Schema,
    catalog: Catalog,
) -> None:
    assert expected == catalog._convert_schema_if_needed(schema)


def test_create_table_pyarrow_schema(
    catalog: Catalog, pyarrow_schema_simple_without_ids: pa.Schema
) -> None:
    catalog.create_namespace(TEST_TABLE_NAMESPACE)
    table = catalog.create_table(
        identifier=TEST_TABLE_IDENTIFIER,
        schema=pyarrow_schema_simple_without_ids,
        properties=TEST_TABLE_PROPERTIES,
    )
    assert catalog.load_table(TEST_TABLE_IDENTIFIER) == table


def test_create_table_raises_error_when_table_already_exists(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # When
    with pytest.raises(TableAlreadyExistsError, match=TABLE_ALREADY_EXISTS_ERROR):
        catalog.create_table(
            identifier=TEST_TABLE_IDENTIFIER,
            schema=TEST_TABLE_SCHEMA,
        )


def test_load_table(catalog: Catalog) -> None:
    # Given
    given_table = given_catalog_has_a_table(catalog)
    # When
    table = catalog.load_table(TEST_TABLE_IDENTIFIER)
    # Then
    assert table == given_table


def test_load_table_from_self_identifier(catalog: Catalog) -> None:
    # Given
    given_table = given_catalog_has_a_table(catalog)
    # When
    intermediate = catalog.load_table(TEST_TABLE_IDENTIFIER)
    table = catalog.load_table(intermediate.identifier)
    # Then
    assert table == given_table


def test_table_raises_error_on_table_not_found(catalog: Catalog) -> None:
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_table_exists(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # Then
    assert catalog.table_exists(TEST_TABLE_IDENTIFIER)


def test_table_exists_on_table_not_found(catalog: Catalog) -> None:
    assert not catalog.table_exists(TEST_TABLE_IDENTIFIER)


def test_drop_table(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # When
    catalog.drop_table(TEST_TABLE_IDENTIFIER)
    # Then
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_drop_table_from_self_identifier(catalog: Catalog) -> None:
    # Given
    table = given_catalog_has_a_table(catalog)
    # When
    catalog.drop_table(table.identifier)
    # Then
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(table.identifier)
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_drop_table_that_does_not_exist_raise_error(catalog: Catalog) -> None:
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_purge_table(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # When
    catalog.purge_table(TEST_TABLE_IDENTIFIER)
    # Then
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_rename_table(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)

    # When
    # (TODO): namespace can be hierarchical
    new_namespace = ("new_namespace",)
    new_table = ("new_namespace", "new_table")
    catalog.create_namespace(new_namespace)
    table = catalog.rename_table(TEST_TABLE_IDENTIFIER, new_table)

    # Then
    # (TODO): get rid of catalog name in identifier
    assert table.identifier[1:] == Catalog.identifier_to_tuple(new_table)

    # And
    table = catalog.load_table(new_table)
    assert table.identifier[1:] == Catalog.identifier_to_tuple(new_table)

    # And
    assert new_namespace in catalog.list_namespaces()

    # And
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_rename_table_from_self_identifier(catalog: Catalog) -> None:
    # Given
    table = given_catalog_has_a_table(catalog)

    # When
    new_namespace = ("new_namespace",)
    new_table_name = ("new_namespace", "new_table")
    catalog.create_namespace(new_namespace)
    new_table = catalog.rename_table(TEST_TABLE_IDENTIFIER, new_table_name)

    # Then
    assert new_table.identifier[1:] == Catalog.identifier_to_tuple(new_table_name)

    # And
    new_table = catalog.load_table(new_table.identifier)
    assert new_table.identifier[1:] == Catalog.identifier_to_tuple(new_table_name)

    # And
    assert new_namespace in catalog.list_namespaces()

    # And
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(table.identifier)
    with pytest.raises(NoSuchTableError, match=NO_SUCH_TABLE_ERROR):
        catalog.load_table(TEST_TABLE_IDENTIFIER)


def test_create_namespace(catalog: Catalog) -> None:
    # When
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)

    # Then
    assert TEST_TABLE_NAMESPACE in catalog.list_namespaces()
    assert TEST_TABLE_PROPERTIES == catalog.load_namespace_properties(
        TEST_TABLE_NAMESPACE
    )


def test_create_namespace_raises_error_on_existing_namespace(catalog: Catalog) -> None:
    # Given
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)
    # When
    with pytest.raises(
        NamespaceAlreadyExistsError, match=NAMESPACE_ALREADY_EXISTS_ERROR
    ):
        catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)


def test_get_namespace_metadata_raises_error_when_namespace_does_not_exist(
    catalog: Catalog,
) -> None:
    with pytest.raises(NoSuchNamespaceError, match=NO_SUCH_NAMESPACE_ERROR):
        catalog.load_namespace_properties(TEST_TABLE_NAMESPACE)


def test_list_namespaces(catalog: Catalog) -> None:
    # Given
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)
    # When
    namespaces = catalog.list_namespaces()
    # Then
    assert TEST_TABLE_NAMESPACE in namespaces


def test_drop_namespace(catalog: Catalog) -> None:
    # Given
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)
    # When
    catalog.drop_namespace(TEST_TABLE_NAMESPACE)
    # Then
    assert TEST_TABLE_NAMESPACE not in catalog.list_namespaces()


def test_drop_namespace_raises_error_when_namespace_does_not_exist(
    catalog: Catalog,
) -> None:
    with pytest.raises(NoSuchNamespaceError, match=NO_SUCH_NAMESPACE_ERROR):
        catalog.drop_namespace(TEST_TABLE_NAMESPACE)


def test_drop_namespace_raises_error_when_namespace_not_empty(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # When
    with pytest.raises(NamespaceNotEmptyError, match=NAMESPACE_NOT_EMPTY_ERROR):
        catalog.drop_namespace(TEST_TABLE_NAMESPACE)


def test_list_tables(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    # When
    # (TODO): list_tables should handle without any namespace
    tables = catalog.list_tables(TEST_TABLE_NAMESPACE)
    # Then
    assert tables
    assert TEST_TABLE_IDENTIFIER in tables


def test_list_tables_under_a_namespace(catalog: Catalog) -> None:
    # Given
    given_catalog_has_a_table(catalog)
    new_namespace = "new_namespace"
    catalog.create_namespace(new_namespace)
    # When
    all_tables = catalog.list_tables(TEST_TABLE_NAMESPACE)
    new_namespace_tables = catalog.list_tables(new_namespace)
    # Then
    assert all_tables
    assert TEST_TABLE_IDENTIFIER in all_tables
    assert new_namespace_tables == []


def test_update_namespace_metadata(catalog: Catalog) -> None:
    # Given
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)

    # When
    new_metadata = {"key3": "value3", "key4": "value4"}
    summary = catalog.update_namespace_properties(
        TEST_TABLE_NAMESPACE, updates=new_metadata
    )

    # Then
    assert TEST_TABLE_NAMESPACE in catalog.list_namespaces()
    assert (
        new_metadata.items()
        <= catalog.load_namespace_properties(TEST_TABLE_NAMESPACE).items()
    )
    assert summary == PropertiesUpdateSummary(
        removed=[], updated=["key3", "key4"], missing=[]
    )


def test_update_namespace_metadata_removals(catalog: Catalog) -> None:
    # Given
    catalog.create_namespace(TEST_TABLE_NAMESPACE, TEST_TABLE_PROPERTIES)

    # When
    new_metadata = {"key3": "value3", "key4": "value4"}
    remove_metadata = {"key1"}
    summary = catalog.update_namespace_properties(
        TEST_TABLE_NAMESPACE, remove_metadata, new_metadata
    )

    # Then
    assert TEST_TABLE_NAMESPACE in catalog.list_namespaces()
    assert (
        new_metadata.items()
        <= catalog.load_namespace_properties(TEST_TABLE_NAMESPACE).items()
    )
    assert remove_metadata.isdisjoint(
        catalog.load_namespace_properties(TEST_TABLE_NAMESPACE).keys()
    )
    assert summary == PropertiesUpdateSummary(
        removed=["key1"], updated=["key3", "key4"], missing=[]
    )


def test_update_namespace_metadata_raises_error_when_namespace_does_not_exist(
    catalog: Catalog,
) -> None:
    with pytest.raises(NoSuchNamespaceError, match=NO_SUCH_NAMESPACE_ERROR):
        catalog.update_namespace_properties(
            TEST_TABLE_NAMESPACE, updates=TEST_TABLE_PROPERTIES
        )


def test_commit_table(catalog: Catalog) -> None:
    # Given
    given_table = given_catalog_has_a_table(catalog)
    #
    new_schema = Schema(
        NestedField(1, "x", LongType()),
        NestedField(2, "y", LongType(), doc="comment"),
        NestedField(3, "z", LongType()),
        NestedField(4, "add", LongType()),
    )

    # When
    response = given_table.catalog._commit_table(  # pylint: disable=W0212
        CommitTableRequest(
            identifier=TableIdentifier(
                namespace=Namespace(given_table.identifier[:-1]),
                name=given_table.identifier[-1],
            ),
            updates=[
                AddSchemaUpdate(
                    schema=new_schema, last_column_id=new_schema.highest_field_id
                ),
                SetCurrentSchemaUpdate(schema_id=-1),
            ],
        )
    )

    # Then
    assert response.metadata.table_uuid == given_table.metadata.table_uuid
    assert len(response.metadata.schemas) == 2
    assert response.metadata.schemas[1] == new_schema
    assert response.metadata.current_schema_id == new_schema.schema_id


def test_add_column(catalog: Catalog) -> None:
    given_table = given_catalog_has_a_table(catalog)

    given_table.update_schema().add_column(
        path="new_column1", field_type=IntegerType()
    ).commit()

    assert given_table.schema() == Schema(
        NestedField(field_id=1, name="x", field_type=LongType(), required=True),
        NestedField(
            field_id=2, name="y", field_type=LongType(), required=True, doc="comment"
        ),
        NestedField(field_id=3, name="z", field_type=LongType(), required=True),
        NestedField(
            field_id=4, name="new_column1", field_type=IntegerType(), required=False
        ),
        identifier_field_ids=[],
    )
    assert given_table.schema().schema_id == 1

    transaction = given_table.transaction()
    transaction.update_schema().add_column(
        path="new_column2", field_type=IntegerType(), doc="doc"
    ).commit()
    transaction.commit_transaction()

    assert given_table.schema() == Schema(
        NestedField(field_id=1, name="x", field_type=LongType(), required=True),
        NestedField(
            field_id=2, name="y", field_type=LongType(), required=True, doc="comment"
        ),
        NestedField(field_id=3, name="z", field_type=LongType(), required=True),
        NestedField(
            field_id=4, name="new_column1", field_type=IntegerType(), required=False
        ),
        NestedField(
            field_id=5,
            name="new_column2",
            field_type=IntegerType(),
            required=False,
            doc="doc",
        ),
        identifier_field_ids=[],
    )
    assert given_table.schema().schema_id == 2


def test_add_column_with_statement(catalog: Catalog) -> None:
    given_table = given_catalog_has_a_table(catalog)

    with given_table.update_schema() as tx:
        tx.add_column(path="new_column1", field_type=IntegerType())

    assert given_table.schema() == Schema(
        NestedField(field_id=1, name="x", field_type=LongType(), required=True),
        NestedField(
            field_id=2, name="y", field_type=LongType(), required=True, doc="comment"
        ),
        NestedField(field_id=3, name="z", field_type=LongType(), required=True),
        NestedField(
            field_id=4, name="new_column1", field_type=IntegerType(), required=False
        ),
        identifier_field_ids=[],
    )
    assert given_table.schema().schema_id == 1

    with given_table.transaction() as tx:
        tx.update_schema().add_column(
            path="new_column2", field_type=IntegerType(), doc="doc"
        ).commit()

    assert given_table.schema() == Schema(
        NestedField(field_id=1, name="x", field_type=LongType(), required=True),
        NestedField(
            field_id=2, name="y", field_type=LongType(), required=True, doc="comment"
        ),
        NestedField(field_id=3, name="z", field_type=LongType(), required=True),
        NestedField(
            field_id=4, name="new_column1", field_type=IntegerType(), required=False
        ),
        NestedField(
            field_id=5,
            name="new_column2",
            field_type=IntegerType(),
            required=False,
            doc="doc",
        ),
        identifier_field_ids=[],
    )
    assert given_table.schema().schema_id == 2


def test_catalog_repr(catalog: Catalog) -> None:
    s = repr(catalog)
    assert s == "default (<class 'pyiceberg.catalog.rest.RestCatalog'>)"


def test_table_properties_int_value(catalog: Catalog) -> None:
    # table properties can be set to int, but still serialized to string
    property_with_int = {"property_name": 42}
    given_table = given_catalog_has_a_table(catalog, properties=property_with_int)
    assert isinstance(given_table.properties["property_name"], str)


def test_table_properties_raise_for_none_value(catalog: Catalog) -> None:
    property_with_none = {"property_name": None}
    with pytest.raises(ValidationError) as exc_info:
        _ = given_catalog_has_a_table(catalog, properties=property_with_none)
    assert "None type is not a supported value in properties: property_name" in str(
        exc_info.value
    )
