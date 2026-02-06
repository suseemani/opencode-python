"""Bun compatibility layer for OpenCode."""

import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "bun"})


class BunFile:
    """Represents a file with Bun-like interface."""
    
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
    
    def exists(self) -> bool:
        """Check if file exists."""
        return self.path.exists()
    
    async def text(self) -> str:
        """Read file as text."""
        return self.path.read_text(encoding="utf-8")
    
    async def json(self) -> Any:
        """Read file as JSON."""
        import json
        return json.loads(self.path.read_text())
    
    def write(self, content: str) -> None:
        """Write text to file."""
        self.path.write_text(content, encoding="utf-8")
    
    def writer(self):
        """Get a file writer."""
        return open(self.path, "a", encoding="utf-8")


class BunGlob:
    """Glob pattern matching like Bun.Glob."""
    
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
    
    async def scan(self, options: dict[str, Any] | None = None) -> list[str]:
        """Scan for files matching pattern."""
        opts = options or {}
        cwd = Path(opts.get("cwd", "."))
        absolute = opts.get("absolute", False)
        only_files = opts.get("onlyFiles", True)
        
        import fnmatch
        
        matches = []
        for root, dirs, files in os.walk(cwd):
            # Check if we should include directories
            if not only_files:
                for d in dirs:
                    if fnmatch.fnmatch(d, self.pattern):
                        path = Path(root) / d
                        if absolute:
                            matches.append(str(path.absolute()))
                        else:
                            matches.append(str(path.relative_to(cwd)))
            
            # Check files
            for f in files:
                if fnmatch.fnmatch(f, self.pattern):
                    path = Path(root) / f
                    if absolute:
                        matches.append(str(path.absolute()))
                    else:
                        matches.append(str(path.relative_to(cwd)))
        
        return matches


class BunRegistry:
    """Bun registry interface."""
    
    def __init__(self) -> None:
        self._url = "https://registry.npmjs.org"
    
    async def resolve(self, package: str, version: str | None = None) -> str | None:
        """Resolve package to URL."""
        # Simplified implementation
        ver = version or "latest"
        return f"{self._url}/{package}/{ver}"


# Bun-like $ function for running commands
async def bun_shell(
    command: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    quiet: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    """Execute a shell command like Bun.$."""
    log.info("Executing shell command", {"command": command[:100], "cwd": cwd})
    
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE if not quiet else subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE if not quiet else subprocess.DEVNULL,
        cwd=cwd,
        env={**os.environ, **(env or {})},
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"Command timed out after {timeout}s")
    
    return subprocess.CompletedProcess(
        args=command,
        returncode=proc.returncode or 0,
        stdout=stdout.decode() if stdout else "",
        stderr=stderr.decode() if stderr else "",
    )


# File function like Bun.file
def file(path: str | Path) -> BunFile:
    """Create a BunFile instance."""
    return BunFile(path)


# Glob function like new Bun.Glob
def glob(pattern: str) -> BunGlob:
    """Create a BunGlob instance."""
    return BunGlob(pattern)


# which function
def which(cmd: str) -> str | None:
    """Find command in PATH."""
    return shutil.which(cmd)


# exec function
async def exec(
    *args: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Execute a command."""
    log.info("Executing", {"args": args, "cwd": cwd})
    
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env={**os.environ, **(env or {})},
    )
    
    stdout, stderr = await proc.communicate()
    
    return subprocess.CompletedProcess(
        args=list(args),
        returncode=proc.returncode or 0,
        stdout=stdout.decode() if stdout else "",
        stderr=stderr.decode() if stderr else "",
    )
