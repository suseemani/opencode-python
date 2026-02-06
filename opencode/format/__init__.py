"""Format module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class Formatter(BaseModel):
    """Code formatter."""
    name: str = Field(description="Formatter name")
    command: list[str] = Field(description="Formatter command")
    extensions: list[str] = Field(description="File extensions")


_formatters: dict[str, Formatter] = {}


def init() -> None:
    """Initialize formatters."""
    pass


async def format_file(file: str, formatter: str | None = None) -> str:
    """Format a file."""
    # Implement formatting logic
    return file


async def register(formatter: Formatter) -> None:
    """Register a formatter."""
    _formatters[formatter.name] = formatter


def get_formatter(name: str) -> Formatter | None:
    """Get a formatter by name."""
    return _formatters.get(name)
