"""Filesystem utilities."""

import shutil
from pathlib import Path
from typing import Any


async def copy(src: Path | str, dst: Path | str) -> None:
    """Copy a file from src to dst."""
    shutil.copy2(str(src), str(dst))


async def remove(path: Path | str, recursive: bool = False) -> None:
    """Remove a file or directory."""
    p = Path(path)
    if not p.exists():
        return

    if p.is_dir() and recursive:
        shutil.rmtree(p)
    else:
        p.unlink()


async def exists(path: Path | str) -> bool:
    """Check if a path exists."""
    return Path(path).exists()


async def mkdir(path: Path | str, parents: bool = False) -> None:
    """Create a directory."""
    Path(path).mkdir(parents=parents, exist_ok=True)


async def read_file(path: Path | str, encoding: str = "utf-8") -> str:
    """Read a file as text."""
    return Path(path).read_text(encoding=encoding)


async def write_file(path: Path | str, content: str, encoding: str = "utf-8") -> None:
    """Write text to a file."""
    Path(path).write_text(content, encoding=encoding)


async def read_json(path: Path | str) -> Any:
    """Read and parse a JSON file."""
    import json

    content = await read_file(path)
    return json.loads(content)


async def write_json(path: Path | str, data: Any, indent: int = 2) -> None:
    """Write data to a JSON file."""
    import json

    content = json.dumps(data, indent=indent, default=str)
    await write_file(path, content)
