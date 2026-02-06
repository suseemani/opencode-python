"""Bun compatibility module for opencode."""

import asyncio
import shutil
from pathlib import Path


async def which() -> str | None:
    """Get the Bun executable path."""
    return shutil.which("bun")


async def run(args: list[str], cwd: str | None = None) -> None:
    """Run a Bun command."""
    bun = await which()
    if not bun:
        raise RuntimeError("Bun not found")
    
    proc = await asyncio.create_subprocess_exec(
        bun,
        *args,
        cwd=cwd,
    )
    await proc.wait()


async def resolve(module: str, cwd: str | None = None) -> str | None:
    """Resolve a module path."""
    # Simplified implementation
    return None
