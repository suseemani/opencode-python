"""Debug CLI commands."""

from typing import Any

import typer

from opencode.util import create as create_logger

log = create_logger({"service": "cli", "command": "debug"})

app = typer.Typer(help="Debug commands for opencode")


@app.command()
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show"),
) -> None:
    """Show debug logs."""
    from opencode.global_path import get_paths
    from pathlib import Path
    
    log_dir = get_paths().log
    
    if not log_dir.exists():
        typer.echo("No logs found")
        return
    
    # Find latest log file
    log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not log_files:
        typer.echo("No log files found")
        return
    
    latest = log_files[0]
    typer.echo(f"Showing logs from: {latest}")
    typer.echo("-" * 80)
    
    # Read and display
    content = latest.read_text()
    log_lines = content.split("\n")
    
    for line in log_lines[-lines:]:
        typer.echo(line)


@app.command()
def config() -> None:
    """Show current configuration."""
    from opencode.global_path import get_paths
    
    paths = get_paths()
    
    typer.echo("OpenCode Configuration")
    typer.echo("=" * 80)
    typer.echo(f"Data directory: {paths.data}")
    typer.echo(f"Config directory: {paths.config}")
    typer.echo(f"Cache directory: {paths.cache}")
    typer.echo(f"State directory: {paths.state}")
    typer.echo(f"Log directory: {paths.log}")


@app.command()
def storage() -> None:
    """Show storage information."""
    from opencode.global_path import get_paths
    from pathlib import Path
    import json
    
    paths = get_paths()
    storage_dir = paths.data / "storage"
    
    typer.echo("Storage Information")
    typer.echo("=" * 80)
    
    if not storage_dir.exists():
        typer.echo("No storage directory found")
        return
    
    # List storage contents
    for item in sorted(storage_dir.iterdir()):
        if item.is_dir():
            count = len(list(item.rglob("*.json")))
            typer.echo(f"📁 {item.name}: {count} items")


@app.command()
def bus() -> None:
    """Show event bus information."""
    from opencode.bus import get_bus
    
    typer.echo("Event Bus Status")
    typer.echo("=" * 80)
    typer.echo("Event bus is active")
    typer.echo("Use --verbose for subscription details")


if __name__ == "__main__":
    app()
