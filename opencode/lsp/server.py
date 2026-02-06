"""LSP server definitions for opencode."""

from pathlib import Path
from typing import Any, Callable, Coroutine

from pydantic import BaseModel, Field

from opencode.project import instance
from opencode.util import filesystem
from opencode.util import log


logger = log.create({"service": "lsp.server"})


class Handle(BaseModel):
    """LSP server handle."""
    process: Any = Field(description="Server process")
    initialization: dict[str, Any] | None = Field(default=None, description="Initialization options")


RootFunction = Callable[[str], Coroutine[Any, Any, str | None]]


def nearest_root(
    include_patterns: list[str],
    exclude_patterns: list[str] | None = None,
) -> RootFunction:
    """Create a root function that finds nearest matching directory."""
    async def root(file: str) -> str | None:
        if exclude_patterns:
            # Check for excluded patterns
            for pattern in exclude_patterns:
                matches = filesystem.up({
                    "targets": [pattern],
                    "start": Path(file).parent,
                    "stop": instance.get_directory(),
                })
                async for match in matches:
                    if match:
                        return None
        
        # Find included patterns
        for pattern in include_patterns:
            matches = filesystem.up({
                "targets": [pattern],
                "start": Path(file).parent,
                "stop": instance.get_directory(),
            })
            async for match in matches:
                if match:
                    return str(Path(match).parent)
        
        return instance.get_directory()
    
    return root


class ServerInfo(BaseModel):
    """LSP server information."""
    id: str = Field(description="Server ID")
    extensions: list[str] = Field(description="File extensions")
    global_: bool | None = Field(default=None, alias="global", description="Global server")
    root: RootFunction = Field(description="Root function")
    spawn: Callable[[str], Coroutine[Any, Any, Handle | None]] = Field(description="Spawn function")

    class Config:
        arbitrary_types_allowed = True


# Predefined servers
Typescript = ServerInfo(
    id="typescript",
    extensions=[".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"],
    root=nearest_root(
        ["package-lock.json", "bun.lockb", "bun.lock", "pnpm-lock.yaml", "yarn.lock"],
        ["deno.json", "deno.jsonc"],
    ),
    spawn=lambda root: _spawn_typescript(root),
)

Pyright = ServerInfo(
    id="pyright",
    extensions=[".py", ".pyi"],
    root=nearest_root([
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "pyrightconfig.json",
    ]),
    spawn=lambda root: _spawn_pyright(root),
)

Gopls = ServerInfo(
    id="gopls",
    extensions=[".go"],
    root=nearest_root(["go.mod", "go.sum", "go.work"]),
    spawn=lambda root: _spawn_gopls(root),
)

RustAnalyzer = ServerInfo(
    id="rust",
    extensions=[".rs"],
    root=nearest_root(["Cargo.toml", "Cargo.lock"]),
    spawn=lambda root: _spawn_rust_analyzer(root),
)


async def _spawn_typescript(root: str) -> Handle | None:
    """Spawn TypeScript language server."""
    import shutil
    
    tsserver = shutil.which("typescript-language-server")
    if not tsserver:
        logger.info("typescript-language-server not found")
        return None
    
    import asyncio
    process = await asyncio.create_subprocess_exec(
        tsserver,
        "--stdio",
        cwd=root,
    )
    
    return Handle(process=process)


async def _spawn_pyright(root: str) -> Handle | None:
    """Spawn Pyright language server."""
    import shutil
    
    pyright = shutil.which("pyright-langserver")
    if not pyright:
        logger.info("pyright-langserver not found")
        return None
    
    import asyncio
    process = await asyncio.create_subprocess_exec(
        pyright,
        "--stdio",
        cwd=root,
    )
    
    return Handle(process=process)


async def _spawn_gopls(root: str) -> Handle | None:
    """Spawn Go language server."""
    import shutil
    
    gopls = shutil.which("gopls")
    if not gopls:
        logger.info("gopls not found")
        return None
    
    import asyncio
    process = await asyncio.create_subprocess_exec(
        gopls,
        cwd=root,
    )
    
    return Handle(process=process)


async def _spawn_rust_analyzer(root: str) -> Handle | None:
    """Spawn Rust analyzer."""
    import shutil
    
    rust_analyzer = shutil.which("rust-analyzer")
    if not rust_analyzer:
        logger.info("rust-analyzer not found")
        return None
    
    import asyncio
    process = await asyncio.create_subprocess_exec(
        rust_analyzer,
        cwd=root,
    )
    
    return Handle(process=process)
