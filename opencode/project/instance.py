"""Instance management for opencode."""

from typing import Any, TypeVar

from opencode.project import project
from opencode.util import context
from opencode.util import log


class InstanceContext:
    """Context for instance management."""
    directory: str
    worktree: str
    project: project.ProjectInfo


_context = context.Context.create(InstanceContext)
_cache: dict[str, InstanceContext] = {}


def get_directory() -> str:
    """Get the current instance directory."""
    return _context.use().directory


def get_worktree() -> str:
    """Get the current instance worktree."""
    return _context.use().worktree


def get_project() -> project.ProjectInfo:
    """Get the current instance project."""
    return _context.use().project


def contains_path(filepath: str) -> bool:
    """Check if a path is within the instance boundary."""
    from opencode.util import filesystem
    
    if filesystem.contains(get_directory(), filepath):
        return True
    
    # Non-git projects set worktree to "/"
    if get_worktree() == "/":
        return False
    
    return filesystem.contains(get_worktree(), filepath)


T = TypeVar("T")


async def provide(directory: str, init: Any | None = None, fn: Any = None) -> Any:
    """Provide instance context for a function."""
    if directory not in _cache:
        log.Default.info("creating instance", {"directory": directory})
        
        proj, sandbox = await project.from_directory(directory)
        ctx = InstanceContext()
        ctx.directory = directory
        ctx.worktree = sandbox
        ctx.project = proj
        
        if init:
            await init()
        
        _cache[directory] = ctx
    
    ctx = _cache[directory]
    return _context.provide(ctx, fn)


def create_state(init: Any, dispose: Any | None = None) -> Any:
    """Create state for the current instance."""
    from opencode.project import state
    return state.create(get_directory, init, dispose)


async def dispose(directory: str | None = None) -> None:
    """Dispose an instance."""
    if directory is None:
        directory = get_directory()
    
    log.Default.info("disposing instance", {"directory": directory})
    
    from opencode.project import state
    await state.dispose(directory)
    
    if directory in _cache:
        del _cache[directory]


async def dispose_all() -> None:
    """Dispose all instances."""
    log.Default.info("disposing all instances")
    
    for directory in list(_cache.keys()):
        try:
            await dispose(directory)
        except Exception as e:
            log.Default.warn("instance dispose failed", {"directory": directory, "error": str(e)})
