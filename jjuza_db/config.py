from pathlib import Path
import os
import sys
from rich.console import Console

from dotenv import load_dotenv


def get_app_dir() -> Path:
    """
    Get the directory where configuration should be stored.

    Development:
        Project root

    PyInstaller:
        Directory containing the executable
    """

    if getattr(sys, "frozen", False):
        # Running as a PyInstaller executable
        return Path(sys.executable).resolve().parent

    # Running normally from source
    return Path(__file__).resolve().parent.parent


APP_DIR = get_app_dir()
ENV_FILE = APP_DIR / ".env"

console = Console()

def load_configuration() -> bool:
    """
    Load environment variables from .env if it exists.
    """

    console.print("[bold cyan]Loading configurations...[/bold cyan]\n")

    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        console.print("[bold cyan]Configurations have been loaded[/bold cyan]\n")
        return True

    return False


def get_connection_string() -> str | None:
    """
    Get the configured SQL Server connection string.
    """

    return os.getenv("CONNECTION")

def store_configuration(
    connection: str | None = None,
    verbose: bool | None = None,
    **extra_settings,   
):
    """
    Store configuration settings like --verbose, --connection to an env file
    """

    console.print("[bold blue]Storing configurations[/bold blue]\n",)

    updates = {}

    if connection is not None:
        updates["CONNECTION"] = connection

    if verbose is not None:
        updates["VERBOSE"] = "true" if verbose else "false"

    for key, value in extra_settings.items():
        if value is not None:
            updates[key.upper()] = str(value)

    if not updates:
        return

    existing_lines = []
    if ENV_FILE.exists():
        existing_lines = ENV_FILE.read_text().splitlines()

    existing_keys_seen = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" not in stripped:
            new_lines.append(line)
            continue

        key, _, _ = stripped.partition("=")
        key = key.strip()

        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            existing_keys_seen.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in existing_keys_seen:
            new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n")

    console.print("[bold green]Configurations have been stored[/bold green]\n",)
        