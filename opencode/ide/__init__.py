"""IDE integration module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class IdeConfig(BaseModel):
    """IDE configuration."""
    name: str = Field(description="IDE name")
    command: str = Field(description="IDE command")


async def open_file(file: str, line: int | None = None, column: int | None = None) -> None:
    """Open a file in the IDE."""
    import subprocess
    
    # Simplified implementation
    cmd = ["code", file]
    if line is not None:
        cmd.extend(["-g", f"{file}:{line}:{column or 0}"])
    
    subprocess.Popen(cmd)


async def get_config() -> IdeConfig | None:
    """Get the current IDE configuration."""
    return IdeConfig(name="vscode", command="code")
