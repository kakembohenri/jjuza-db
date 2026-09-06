import pyfiglet
import questionary

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table


console = Console()


def show_banner():

    title_art = pyfiglet.figlet_format("jjuza db", font="banner3-D")

    console.print(
        Panel(
            f"[bold purple]{title_art}[/bold purple]\n"
            "[dim]SQL Server Edition[/dim]",
            border_style="cyan",
        )
    )

def show_generation_preview(
    target_table: str,
    target_count: int,
    generation_order: list[str],
    records_per_table: dict[str, int],
):

    table = Table(
        title="Generation Preview"
    )

    table.add_column(
        "Table",
        style="cyan",
    )

    table.add_column(
        "Type",
    )

    table.add_column(
        "Records",
        justify="right",
    )

    for table_name in generation_order:

        if table_name == target_table:

            table_type = "[bold green]TARGET[/bold green]"

        else:

            table_type = "[yellow]DEPENDENCY[/yellow]"

        table.add_row(
            table_name,
            table_type,
            str(
                records_per_table[
                    table_name
                ]
            ),
        )

    total = sum(
        records_per_table.values()
    )

    table.add_section()

    table.add_row(
        "[bold]TOTAL[/bold]",
        "",
        f"[bold]{total}[/bold]",
    )

    console.print()
    console.print(table)

    console.print()

    console.print(
        f"[bold]Target:[/bold] "
        f"{target_table}"
    )

    console.print(
        f"[bold]Requested records:[/bold] "
        f"{target_count}"
    )

    console.print()

    console.print(
        "[dim]No database changes have been made yet.[/dim]"
    )

def select_option(
    message: str,
    choices: list[str],
):

    return questionary.select(
        message,
        choices=choices,
    ).ask()


def ask_record_count():

    return questionary.text(
        "How many records?",
        validate=lambda value:
            value.isdigit()
            and 1 <= int(value) <= 20
            or "Enter a number between 1 and 20.",
    ).ask()


def show_tables(tables):

    table = Table(
        title="Available Tables"
    )

    table.add_column("Table")

    for name in tables:
        table.add_row(name)

    console.print(table)


def show_generation(
    table_name: str,
    total: int,
):

    console.print(
        f"\n[bold cyan]"
        f"Generating {total} records "
        f"for {table_name}"
        f"[/bold cyan]\n"
    )


def show_success(message: str):

    console.print(
        f"\n[bold green]✓ {message}[/bold green]"
    )


def show_error(message: str):

    console.print(
        f"\n[bold red]✗ {message}[/bold red]"
    )

def show_table_schema(table_info):

    table = Table(
        title=f"Schema: {table_info.name}"
    )

    table.add_column("Column")
    table.add_column("Type")
    table.add_column("Nullable")
    table.add_column("PK")
    table.add_column("FK")
    table.add_column("Identity")
    table.add_column("Is Unique")
    table.add_column("Has Default value")
    table.add_column("Composite Unique")

    for column in table_info.columns:

        table.add_row(
            column.name,
            column.data_type,
            "Yes" if column.nullable else "No",
            "Yes" if column.primary_key else "",
            "Yes" if column.foreign_key else "",
            "Yes" if column.identity else "",
            "Yes" if column.name in table_info.unique_columns else "",
            "Yes" if column.has_default else "",
            "Yes" if any(column.name in constraint for constraint in table_info.composite_unique_constraints) else "",

        )

    console.print(table)

def show_dependencies(
    generation_order: list[str],
    target_table: str,
):

    console.print(
        "\n[bold cyan]Generation Plan[/bold cyan]"
    )

    for index, table in enumerate(
        generation_order,
        start=1,
    ):

        marker = (
            "[bold green]TARGET[/bold green]"
            if table == target_table
            else "[dim]dependency[/dim]"
        )

        console.print(
            f"  {index}. {table} {marker}"
        )

def confirm_generation():

    return questionary.confirm(
        "Proceed with generation?"
    ).ask()

def update_generation_status(
    progress,
    task_id,
    status: str,
):

    progress.update(
        task_id,
        status=status,
    )

def generation_progress(
    generation_order: list[str],
    records_per_table: dict[str, int],
):

    progress = Progress(
        SpinnerColumn(),
        TextColumn(
            "[progress.description]{task.description}"
        ),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn(
            "[dim]{task.fields[status]}[/dim]"
        ),
    )

    tasks = {}

    for table_name in generation_order:

        total = records_per_table.get(
            table_name,
            0,
        )

        tasks[table_name] = progress.add_task(
            f"[cyan]{table_name}",
            total=total,
            status="waiting",
        )

    return progress, tasks

def show_generated_record(
    table_name: str,
    record: dict,
):

    table = Table(
        title=f"Generated: {table_name}"
    )

    table.add_column("Column")
    table.add_column("Value")

    for column, value in record.items():

        table.add_row(
            column,
            str(value),
        )

    console.print(table)

def show_summary(
    generated_counts: dict[str, int],
):

    table = Table(
        title="Generation Summary"
    )

    table.add_column("Table")
    table.add_column("Records")

    total = 0

    for table_name, count in (
        generated_counts.items()
    ):

        table.add_row(
            table_name,
            str(count),
        )

        total += count

    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total}[/bold]",
    )

    console.print(table)

def show_relationships(
    tables: dict,
    generation_order: list[str],
):

    console.print(
        "\n[bold cyan]Relationships[/bold cyan]"
    )

    found = False

    for table_name in generation_order:

        table_info = tables[
            table_name
        ]

        for fk in table_info.foreign_keys:

            found = True

            console.print(
                f"  [cyan]{table_name}.{fk.column}[/cyan]"
                f" → "
                f"[yellow]"
                f"{fk.referenced_table}"
                f".{fk.referenced_column}"
                f"[/yellow]"
            )

    if not found:

        console.print(
            "  [dim]No foreign-key relationships.[/dim]"
        )

def confirm_generation():

    return questionary.confirm(
        "This will insert records into your database. Continue?"
    ).ask()