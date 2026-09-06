from collections import defaultdict

from jjuza_db.schema import TableInfo


MAX_PARENT_RECORDS = 20


def build_generation_plan(
    generation_order: list[str],
    tables: dict[str, TableInfo],
    target_table: str,
    target_count: int,
) -> dict[str, int]:

    plan = defaultdict(int)

    # -----------------------------------
    # Target
    # -----------------------------------

    plan[target_table] = target_count

    # -----------------------------------
    # Resolve dependencies
    # -----------------------------------

    for table_name in reversed(
        generation_order
    ):

        required_count = plan[
            table_name
        ]

        if required_count <= 0:
            continue

        table_info = tables[
            table_name
        ]

        for fk in table_info.foreign_keys:

            parent_table = (
                fk.referenced_table
            )

            # Find the actual FK column
            column = next(
                (
                    c
                    for c in table_info.columns
                    if c.name == fk.column
                ),
                None,
            )

            if column is None:
                continue

            # --------------------------------
            # UNIQUE foreign key
            # --------------------------------

            if fk.unique:

                if column.nullable:

                    # Because the FK can be NULL,
                    # we don't necessarily need
                    # one parent for every child.

                    required_parents = min(
                        required_count,
                        MAX_PARENT_RECORDS,
                    )

                else:

                    # UNIQUE + NOT NULL means every
                    # child needs a different parent.

                    required_parents = (
                        required_count
                    )

            # --------------------------------
            # Normal foreign key
            # --------------------------------

            else:

                # Parent records can be reused.

                required_parents = min(
                    required_count,
                    MAX_PARENT_RECORDS,
                )

            # --------------------------------
            # Multiple children may depend on
            # the same parent.
            # --------------------------------

            plan[parent_table] = max(
                plan[parent_table],
                required_parents,
            )

    # -----------------------------------
    # Preserve generation order
    # -----------------------------------

    return {
        table_name: plan[table_name]
        for table_name in generation_order
    }