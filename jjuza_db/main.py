import argparse
import sys

from jjuza_db.config import (
    load_configuration,
    get_connection_string,
    store_configuration,
)

from jjuza_db.database import (
    create_database_engine,
    test_connection,
)

from jjuza_db.schema import (
    get_tables,
    inspect_table,
    discover_dependencies,
)

from jjuza_db.dependency import (
    build_dependency_graph,
    get_generation_order,
)

from jjuza_db.generator import (
    generate_record,
)

from jjuza_db.inserter import (
    insert_record,
)

from jjuza_db.ui import (
    show_banner,
    select_option,
    ask_record_count,
    show_relationships,
    show_success,
    show_error,
    show_table_schema,
    show_dependencies,
    confirm_generation,
    generation_progress,
    show_summary,
    show_generation_preview,
)

from jjuza_db.planner import (
    build_generation_plan,
)


MAX_RECORDS = 20

generated_ids = {}

used_fk_values = {}

used_unique_values= {}

generated_counts = {}


def get_primary_key(table_info):

    for column in table_info.columns:

        if column.primary_key:
            return column.name

    return None


def generate_table_records(
    connection,
    table_info,
    count,
    generated_ids,
    progress,
    task_id,
    used_fk_values,
    used_unique_values
) -> int:

    primary_key = get_primary_key(
        table_info
    )

    generated_count = 0

    for _ in range(count):

        record = generate_record(
            table_info,
            generated_ids,
            used_fk_values,
            used_unique_values
        )

        generated_pk = insert_record(
            connection,
            table_info.name,
            record,
            primary_key=primary_key,
        )

        if (
            primary_key
            and generated_pk is not None
        ):

            generated_ids.setdefault(
                table_info.name,
                [],
            ).append(
                generated_pk
            )

        generated_count += 1

        progress.update(
            task_id,
            advance=1,
            status=f"{generated_count}/{count}",
        )

    return generated_count


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="jjuza_db",
        description=(
            "Generate realistic fake data "
            "for SQL Server databases."
        ),
    )

    parser.add_argument(
        "-c",
        "--connection",
        help=(
            "SQL Server connection string. "
            "If omitted, configuration will be "
            "loaded from the environment."
        ),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed generation information.",
    )

    return parser.parse_args()

def main():

    args = parse_arguments()

    show_banner()

    # ===================================
    # Configuration
    # ===================================

    if args.connection or args.verbose:
        store_configuration(
            args.connection,
            args.verbose
        )

    is_configuration = load_configuration()

    if not is_configuration:
        show_error(
            "No database connection configured. Please configure one by adding the connection string --connection to the command jjuza_db"
        )

        sys.exit(1)

    connection_string = (
        args.connection or 
        get_connection_string()
    )

    # ===================================
    # Database connection
    # ===================================

    try:

        engine = create_database_engine(
            connection_string
        )

        test_connection(engine)

    except Exception as exc:

        show_error(
            f"Could not connect to SQL Server:\n{exc}"
        )

        sys.exit(1)

    show_success(
        "Connected to SQL Server."
    )

    # ===================================
    # Table selection
    # ===================================

    try:

        tables = get_tables(engine)

    except Exception as exc:

        show_error(
            f"Could not retrieve tables:\n{exc}"
        )

        sys.exit(1)

    if not tables:

        show_error(
            "No tables found."
        )

        sys.exit(1)

    selected_table = select_option(
        "Select the table you want to populate:",
        tables,
    )

    if not selected_table:
        return

    # ===================================
    # Record count
    # ===================================

    count = ask_record_count()

    if not count:
        return

    count = int(count)

    if count > MAX_RECORDS:

        show_error(
            f"Maximum allowed records is "
            f"{MAX_RECORDS}."
        )

        return

    # ===================================
    # Inspect selected table
    # ===================================

    try:

        target_info = inspect_table(
            engine,
            selected_table,
        )

        show_success(
            f"Analysed table: {selected_table}"
        )

        show_table_schema(
            target_info
        )

    except Exception as exc:

        show_error(
            f"Could not analyse table:{selected_table}\nError: {exc}"
        )

        sys.exit(1)

    # ===================================
    # Discover dependencies
    # ===================================

    try:

        all_tables = discover_dependencies(
            engine,
            selected_table,
        )

        graph = build_dependency_graph(
            engine,
            all_tables,
        )

        generation_order = (
            get_generation_order(
                graph,
                selected_table,
            )
        )

    except Exception as exc:

        show_error(
            f"Dependency analysis failed:\n{exc}"
        )

        sys.exit(1)

    # ===================================
    # Show generation plan
    # ===================================

    show_dependencies(
        generation_order,
        selected_table,
    )


    # ===================================
    # Generate
    # ===================================

    generated_ids = {}

    generated_counts = {}

    # Dependencies should generally receive
    # enough records to satisfy the target.
    #
    # First version: generate `count` for
    # every dependency table.

    records_per_table = build_generation_plan(
        generation_order=generation_order,
        tables=all_tables,
        target_table=selected_table,
        target_count=count,
    )

    show_generation_preview(
        target_table=selected_table,
        target_count=count,
        generation_order=generation_order,
        records_per_table=records_per_table,
    )

    show_relationships(
        all_tables,
        generation_order,
    )

    # ===================================
    # Confirm
    # ===================================

    if not confirm_generation():

        show_error(
            "Generation cancelled."
        )

        return

    try:

        progress, tasks =  generation_progress(
            generation_order,
            records_per_table,
        )
        with engine.begin() as connection:
            with progress:

                for table_name in generation_order:

                    task_id = tasks[table_name]

                    progress.update(
                        task_id,
                        status="generating",
                    )

                    table_info = all_tables[
                        table_name
                    ]

                    table_count = records_per_table[
                        table_name
                    ]

                    generated_count = (
                        generate_table_records(
                            connection,
                            table_info,
                            table_count,
                            generated_ids,
                            progress,
                            task_id,
                            used_fk_values,
                            used_unique_values
                        )
                    )

                    generated_counts[
                        table_name
                    ] = generated_count

                    progress.update(
                        task_id,
                        status="complete",
                    )
                
        show_success("Transaction committed successfully.✅")
    except Exception as exc:

        show_error(
            f"Generation failed:\n{exc}"
        )

        sys.exit(1)

    # ===================================
    # Summary
    # ===================================

    show_summary(
        generated_counts
    )

    show_success(
        "Database generation completed."
    )

if __name__ == "__main__":
    main()