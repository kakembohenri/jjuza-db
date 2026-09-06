from dataclasses import dataclass
from typing import Any

from sqlalchemy import CHAR, inspect
from sqlalchemy.engine import Engine
from rich.console import Console

console = Console()

@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    foreign_key: bool
    identity: bool
    has_default: bool
    computed: bool
    unique: bool
    max_length: int|None
    is_uuid: bool
    is_constraint: bool
    constraint_definition: str | None

@dataclass
class ForeignKeyInfo:
    column: str
    referenced_table: str
    referenced_column: str
    unique: bool


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKeyInfo]
    unique_columns: set[str]
    composite_unique_constraints: list[tuple[str, ...]]


def get_tables(engine: Engine) -> list[str]:
    inspector = inspect(engine)

    return inspector.get_table_names()

def is_uuid_column(column, primary_key: bool) -> bool:
    column_type = column["type"]

    if not primary_key:
        return False

    return (
        isinstance(column_type, CHAR)
        and column_type.length == 32
    )

def is_json_column(column_name, check_constraints):
    for constraint in check_constraints:
        sqltext = constraint["sqltext"].lower()

        if (
            "isjson" in sqltext
            and column_name.lower() in sqltext
        ):
            return True

    return False

from sqlalchemy import text

def get_check_constraints(engine, table_name):
    query = text("""
        SELECT
            cc.name AS constraint_name,
            cc.definition AS definition
        FROM sys.check_constraints cc
        INNER JOIN sys.tables t
            ON cc.parent_object_id = t.object_id
        WHERE t.name = :table_name
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"table_name": table_name}
        )

        return [
            {
                "name": row.constraint_name,
                "definition": row.definition,
            }
            for row in result
        ]

def get_constraint_definition(
    column_name: str,
    constraints: list[dict],
) -> str | None:
    column_name = column_name.lower()

    for constraint in constraints:
        definition = constraint["definition"]

        if f"[{column_name}]" in definition.lower():
            return definition

    return None

def inspect_table(
    engine: Engine,
    table_name: str,
) -> TableInfo:

    inspector = inspect(engine)

    constraints = get_check_constraints(engine, table_name)

    columns = []

    pk_constraint = inspector.get_pk_constraint(
        table_name
    )

    primary_keys = pk_constraint.get("constrained_columns", [])

    foreign_keys = inspector.get_foreign_keys(
        table_name
    )

    fk_columns = {
        column
        for fk in foreign_keys
        for column in fk.get("constrained_columns", [])
    }

    # -----------------------------------
    # Unique constraints
    # -----------------------------------

    unique_columns, composite_unique_columns = get_unique_columns(
        inspector,
        table_name
    )

    column_data = inspector.get_columns(table_name)

    for column in column_data:

        computed = bool(
            column.get("computed")
        )

        identity = bool(
            column.get("identity")
        )

        has_default = (
            column.get("default") is not None
        )

        constraint_definition = get_constraint_definition(
            column["name"],
            constraints,
        )

        columns.append(
            ColumnInfo(
                name=column["name"],
                data_type=str(column["type"]),
                nullable=column["nullable"],
                primary_key=column["name"] in primary_keys,
                foreign_key=column["name"] in fk_columns,
                identity=identity,
                has_default=has_default,
                computed=computed,
                unique=column["name"] in unique_columns,
                max_length=getattr(column["type"], "length", None),
                is_uuid=is_uuid_column(
                    column,
                    column["name"] in primary_keys,
                ),
                is_constraint=constraint_definition is not None,
                constraint_definition=constraint_definition,
            )
        )

    fk_info = []

    for fk in foreign_keys:

        constrained = fk.get(
            "constrained_columns",
            []
        )

        referred = fk.get(
            "referred_columns",
            []
        )

        referred_table = fk.get(
            "referred_table"
        )

        for column, ref_column in zip(
            constrained,
            referred
        ):
            fk_info.append(
                ForeignKeyInfo(
                    column=column,
                    referenced_table=referred_table,
                    referenced_column=ref_column,
                    unique=column in unique_columns,
                )
            )

    return TableInfo(
        name=table_name,
        columns=columns,
        foreign_keys=fk_info,
        unique_columns=unique_columns,
        composite_unique_constraints = composite_unique_columns
    )

def discover_dependencies(
    engine: Engine,
    target_table: str,
) -> dict[str, TableInfo]:

    discovered: dict[str, TableInfo] = {}

    def visit(table_name: str):

        if table_name in discovered:
            return

        table_info = inspect_table(
            engine,
            table_name,
        )

        discovered[table_name] = table_info

        for fk in table_info.foreign_keys:
            if fk.referenced_table == table_name:
                continue
            visit(fk.referenced_table)

    visit(target_table)

    return discovered

def get_unique_columns(
    inspector,
    table_name: str,
) -> tuple[set, list]:

    unique_columns = set()
    composite_unique_columns = []

    # UNIQUE indexes
    for index in inspector.get_indexes(
        table_name
    ):

        if index.get("unique"):

            columns = index.get(
                "column_names",
                [],
            )

            if len(columns) == 1:
                unique_columns.add(
                    columns[0]
                )

            elif len(columns) > 1:
                composite_unique_columns.append(
                    tuple(columns)
                )

    return (unique_columns,  composite_unique_columns)
   