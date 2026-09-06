import json
import random
import re
import uuid

from faker import Faker

from jjuza_db.schema import TableInfo


fake = Faker()


def limit_string(
    value: str,
    max_length: int | None,
) -> str:

    if max_length is None:
        return value

    return value[:max_length]


def generate_value(
    column_name: str,
    data_type: str,
    max_length: int | None = None,
    is_uuid: bool = False,
    is_constraint: bool = False,
    constraint_definition: str|None = None,
):
    """
    Generate a fake value based on the
    column name and SQL Server type.
    """

    name = column_name.lower()
    dtype = data_type.lower()

    # --------------------------------
    # Name-based generation
    # --------------------------------

    # For primary keys using uuids
    if is_uuid:
        return uuid.uuid4().hex

    if is_constraint:
        definition = constraint_definition.lower()
        if "isjson" in definition:
            return json.dumps([])

    if "email" in name:
        return limit_string(
            fake.email(),
            max_length,
        )

    if "first_name" in name:
        return limit_string(
            fake.first_name(),
            max_length,
        )

    if "last_name" in name:
        return limit_string(
            fake.last_name(),
            max_length,
        )

    if "phone" in name or "mobile" in name:
        return limit_string(
            fake.phone_number(),
            max_length,
        )

    if "address" in name:
        return limit_string(
            fake.address(),
            max_length,
        )

    if "city" in name:
        return limit_string(
            fake.city(),
            max_length,
        )

    if "country" in name:
        return limit_string(
            fake.country(),
            max_length,
        )

    # if column_name == "password":
    #     return ""

    # --------------------------------
    # Data-type generation
    # --------------------------------

    if "uniqueidentifier" in dtype:
        return fake.uuid4()

    if "datetime" in dtype:
        return fake.date_time()

    if "date" in dtype:
        return fake.date()

    if "tinyint" in dtype:
        return fake.random_int(min=0, max=255)

    if "smallint" in dtype:
        return fake.random_int(
            min=0,
            max=32_767,
        )

    if "int" in dtype:
        return fake.random_int(
            min=0,
            max=2_147_483_647,
        )

    if "bigint" in dtype:
        return fake.random_int(
            min=-9_223_372_036_854_775_808,
            max=9_223_372_036_854_775_807,
        )

    if dtype.startswith(("decimal", "numeric")):
        match = re.search(r"\((\d+),\s*(\d+)\)", dtype)
        if match:
            max_digits = int(match.group(1))
            decimal_places = int(match.group(2))

            left_digits = max_digits - decimal_places
            right_digits = decimal_places

            return fake.pydecimal(
                left_digits=left_digits,
                right_digits=right_digits,
                positive=True,
            )

    if "decimal" in dtype:
        return fake.pydecimal(
            left_digits=6,
            right_digits=2,
            positive=True,
        )

    if "float" in dtype:
        return fake.pyfloat(
            positive=True,
        )

    if "bit" in dtype:
        return fake.boolean()

    if (
        "varchar" in dtype
        or "nvarchar" in dtype
        or "char" in dtype
        or "text" in dtype
    ):

        if max_length and max_length < 5:
            return fake.lexify(
                text="?" * max_length
            )
    
        value = fake.text(
            max_nb_chars=max_length or 20
        )

        return limit_string(
            value,
            max_length,
        )

    return fake.word()


def generate_unique_value(
    column_name: str,
    data_type: str,
    existing_values: set,
    max_length: int | None = None,
    is_uuid: bool = False,
    is_constraint: bool = False,
    constraint_definition: str | None = None,
):
    """
    Generate a value that does not already
    exist in existing_values.
    """

    for _ in range(100):

        value = generate_value(
            column_name,
            data_type,
            max_length,
            is_uuid,
            is_constraint,
            constraint_definition
        )

        if value not in existing_values:

            existing_values.add(value)

            return value

    raise ValueError(
        f"Could not generate a unique value "
        f"for {column_name}."
    )


def generate_record(
    table_info: TableInfo,
    generated_ids: dict[str, list],
    used_fk_values: dict[str, set] | None = None,
    used_unique_values: dict[str, set] | None = None,
) -> dict:

    data = {}

    if used_fk_values is None:
        used_fk_values = {}

    if used_unique_values is None:
        used_unique_values = {}

    foreign_keys = {
        fk.column: fk
        for fk in table_info.foreign_keys
    }

    for column in table_info.columns:

        # --------------------------------
        # SQL Server generated columns
        # --------------------------------

        if column.identity:
            continue

        if column.computed:
            continue

        if column.has_default:
            continue

        # --------------------------------
        # Foreign key
        # --------------------------------

        if column.name in foreign_keys:

            fk = foreign_keys[
                column.name
            ]

            # Self-referencing FK
            if fk.referenced_table == table_info.name:
                data[column.name] = None
                continue

            parent_ids = generated_ids.get(
                fk.referenced_table,
                [],
            )

            if not parent_ids:

                raise ValueError(
                    f"Self-referencing foreign key "
                    f"{table_info.name}.{column.name} "
                    f"is not nullable."
                )

            # --------------------------------
            # UNIQUE foreign key
            # --------------------------------

            if fk.unique:

                key = (
                    f"{table_info.name}."
                    f"{column.name}"
                )

                used_parent_ids = (
                    used_fk_values.setdefault(
                        key,
                        set(),
                    )
                )

                available_parent_ids = [
                    parent_id
                    for parent_id in parent_ids
                    if parent_id not in used_parent_ids
                ]

                if not available_parent_ids:

                    raise ValueError(
                        f"Not enough unique parent "
                        f"records for "
                        f"{table_info.name}."
                        f"{column.name}."
                    )

                selected_id = random.choice(
                    available_parent_ids
                )

                used_parent_ids.add(
                    selected_id
                )

                data[column.name] = selected_id

            # --------------------------------
            # Normal foreign key
            # --------------------------------

            else:

                data[column.name] = random.choice(
                    parent_ids
                )

            continue

        # --------------------------------
        # UNIQUE normal column
        # --------------------------------

        if column.unique:

            key = (
                f"{table_info.name}."
                f"{column.name}"
            )

            existing_values = (
                used_unique_values.setdefault(
                    key,
                    set(),
                )
            )

            data[column.name] = (
                generate_unique_value(
                    column.name,
                    column.data_type,
                    existing_values,
                    column.max_length,
                    column.is_uuid,
                    column.is_constraint,
                    column.constraint_definition
                )
            )

            continue

        # --------------------------------
        # Normal column
        # --------------------------------

        data[column.name] = generate_value(
            column.name,
            column.data_type,
            column.max_length,
            column.is_uuid,
            column.is_constraint,
            column.constraint_definition
        )

    return data
