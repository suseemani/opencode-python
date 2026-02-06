"""Command module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class CommandInfo(BaseModel):
    """Command information."""
    name: str = Field(description="Command name")
    description: str = Field(description="Command description")
    template: str = Field(description="Command template")


_commands: dict[str, CommandInfo] = {}


async def load(name: str) -> CommandInfo | None:
    """Load a command by name."""
    return _commands.get(name)


async def register(command: CommandInfo) -> None:
    """Register a command."""
    _commands[command.name] = command


async def list_commands() -> list[CommandInfo]:
    """List all commands."""
    return list(_commands.values())


async def execute(name: str, **kwargs: Any) -> Any:
    """Execute a command."""
    command = await load(name)
    if not command:
        raise ValueError(f"Command not found: {name}")
    
    # Execute command logic here
    return None
