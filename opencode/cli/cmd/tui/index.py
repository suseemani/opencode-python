"""TUI CLI commands."""

from typing import Any

import typer

from opencode.util import create as create_logger

log = create_logger({"service": "cli", "command": "tui"})

app = typer.Typer(help="TUI (Terminal User Interface) commands")


@app.command()
def start(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
    session: str | None = typer.Option(None, "--session", "-s", help="Session ID to resume"),
) -> None:
    """Start the TUI interface."""
    typer.echo("Starting OpenCode TUI...")
    typer.echo(f"Project: {project}")
    if session:
        typer.echo(f"Session: {session}")
    
    # TUI implementation would go here
    # For now, just show a message
    typer.echo("\nTUI mode is not yet implemented in Python version.")
    typer.echo("Use the web interface or CLI commands instead.")


@app.command()
def attach(
    session_id: str = typer.Argument(..., help="Session ID to attach to"),
) -> None:
    """Attach to a running TUI session."""
    typer.echo(f"Attaching to session: {session_id}")
    
    # Attach implementation would go here
    typer.echo("\nSession attachment is not yet implemented.")


@app.command()
def list_sessions() -> None:
    """List active TUI sessions."""
    typer.echo("Active TUI Sessions")
    typer.echo("=" * 80)
    
    # List sessions implementation would go here
    typer.echo("No active sessions found.")


if __name__ == "__main__":
    app()
