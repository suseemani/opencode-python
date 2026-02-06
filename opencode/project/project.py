"""Project management for opencode."""

import asyncio
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import bus_event
from opencode.storage import storage
from opencode.util import log


logger = log.create({"service": "project"})


class ProjectIcon(BaseModel):
    """Project icon configuration."""
    url: str | None = Field(default=None, description="Icon URL")
    override: str | None = Field(default=None, description="Override icon")
    color: str | None = Field(default=None, description="Icon color")


class ProjectCommands(BaseModel):
    """Project commands configuration."""
    start: str | None = Field(default=None, description="Startup script")


class ProjectTime(BaseModel):
    """Project timestamps."""
    created: int = Field(description="Creation timestamp")
    updated: int = Field(description="Last update timestamp")
    initialized: int | None = Field(default=None, description="Initialization timestamp")


class ProjectInfo(BaseModel):
    """Project information."""
    id: str = Field(description="Project ID")
    worktree: str = Field(description="Worktree path")
    vcs: str | None = Field(default=None, description="Version control system")
    name: str | None = Field(default=None, description="Project name")
    icon: ProjectIcon | None = Field(default=None, description="Project icon")
    commands: ProjectCommands | None = Field(default=None, description="Project commands")
    time: ProjectTime = Field(description="Project timestamps")
    sandboxes: list[str] = Field(default_factory=list, description="Sandbox directories")


class ProjectUpdatedEvent(BaseModel):
    """Project updated event."""
    type: str = Field(default="project.updated")
    properties: ProjectInfo = Field(description="Updated project info")


Event = bus_event.BusEvent.define("project.updated", ProjectInfo)


async def from_directory(directory: str) -> tuple[ProjectInfo, str]:
    """Get or create project from directory."""
    logger.info("from_directory", {"directory": directory})
    
    # Find git repository
    git_dir = await _find_git_dir(directory)
    
    if git_dir:
        sandbox = str(Path(git_dir).parent)
        project_id = await _get_project_id(git_dir)
        vcs = "git"
        worktree = await _get_worktree(sandbox)
    else:
        project_id = "global"
        sandbox = "/"
        worktree = "/"
        vcs = None
    
    # Load existing project or create new
    existing = await storage.read(ProjectInfo, ["project", project_id]).catch(lambda: None)
    
    if not existing:
        existing = ProjectInfo(
            id=project_id,
            worktree=worktree,
            vcs=vcs,
            sandboxes=[],
            time=ProjectTime(
                created=int(asyncio.get_event_loop().time() * 1000),
                updated=int(asyncio.get_event_loop().time() * 1000),
            ),
        )
    
    # Update project
    result = existing.model_copy(update={
        "worktree": worktree,
        "vcs": vcs,
        "time": ProjectTime(
            created=existing.time.created,
            updated=int(asyncio.get_event_loop().time() * 1000),
            initialized=existing.time.initialized,
        ),
    })
    
    # Add sandbox if different from worktree
    if sandbox != result.worktree and sandbox not in result.sandboxes:
        result.sandboxes.append(sandbox)
    
    # Filter out non-existent sandboxes
    result.sandboxes = [s for s in result.sandboxes if Path(s).exists()]
    
    # Save project
    await storage.write(["project", project_id], result)
    
    # Emit event
    from opencode.bus import index as bus
    bus.publish(Event, result)
    
    return result, sandbox


async def _find_git_dir(directory: str) -> str | None:
    """Find .git directory starting from directory."""
    from opencode.util import filesystem
    
    current = Path(directory).resolve()
    
    while True:
        git_dir = current / ".git"
        if git_dir.exists():
            return str(git_dir)
        
        if current.parent == current:
            break
        current = current.parent
    
    return None


async def _get_project_id(git_dir: str) -> str:
    """Get project ID from git directory."""
    # Check for cached ID
    cache_file = Path(git_dir) / "opencode"
    if cache_file.exists():
        return cache_file.read_text().strip()
    
    # Get root commit
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "--all"],
            cwd=str(Path(git_dir).parent),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            commits = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
            if commits:
                commits.sort()
                project_id = commits[0]
                # Cache the ID
                try:
                    cache_file.write_text(project_id)
                except Exception:
                    pass
                return project_id
    except Exception:
        pass
    
    return "global"


async def _get_worktree(sandbox: str) -> str:
    """Get git worktree."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=sandbox,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            git_dir = result.stdout.strip()
            if git_dir == ".":
                return sandbox
            return str(Path(git_dir).resolve())
    except Exception:
        pass
    
    return sandbox


async def list_projects() -> list[ProjectInfo]:
    """List all projects."""
    keys = await storage.list_keys(["project"])
    projects = []
    for key in keys:
        try:
            project = await storage.read(ProjectInfo, key)
            # Filter out non-existent sandboxes
            project.sandboxes = [s for s in project.sandboxes if Path(s).exists()]
            projects.append(project)
        except Exception:
            pass
    return projects


async def update(
    project_id: str,
    name: str | None = None,
    icon: ProjectIcon | None = None,
    commands: ProjectCommands | None = None,
) -> ProjectInfo:
    """Update project information."""
    def updater(draft: ProjectInfo) -> None:
        if name is not None:
            draft.name = name
        if icon is not None:
            draft.icon = icon
        if commands is not None:
            draft.commands = commands
        draft.time.updated = int(asyncio.get_event_loop().time() * 1000)
    
    result = await storage.update(["project", project_id], updater)
    
    # Emit event
    from opencode.bus import index as bus
    bus.publish(Event, result)
    
    return result


async def set_initialized(project_id: str) -> None:
    """Mark project as initialized."""
    def updater(draft: ProjectInfo) -> None:
        draft.time.initialized = int(asyncio.get_event_loop().time() * 1000)
    
    await storage.update(["project", project_id], updater)


async def get_sandboxes(project_id: str) -> list[str]:
    """Get valid sandboxes for a project."""
    try:
        project = await storage.read(ProjectInfo, ["project", project_id])
        if not project.sandboxes:
            return []
        
        valid = []
        for sandbox in project.sandboxes:
            if Path(sandbox).is_dir():
                valid.append(sandbox)
        return valid
    except Exception:
        return []


async def add_sandbox(project_id: str, directory: str) -> ProjectInfo:
    """Add a sandbox to a project."""
    def updater(draft: ProjectInfo) -> None:
        if directory not in draft.sandboxes:
            draft.sandboxes.append(directory)
        draft.time.updated = int(asyncio.get_event_loop().time() * 1000)
    
    result = await storage.update(["project", project_id], updater)
    
    # Emit event
    from opencode.bus import index as bus
    bus.publish(Event, result)
    
    return result


async def remove_sandbox(project_id: str, directory: str) -> ProjectInfo:
    """Remove a sandbox from a project."""
    def updater(draft: ProjectInfo) -> None:
        draft.sandboxes = [s for s in draft.sandboxes if s != directory]
        draft.time.updated = int(asyncio.get_event_loop().time() * 1000)
    
    result = await storage.update(["project", project_id], updater)
    
    # Emit event
    from opencode.bus import index as bus
    bus.publish(Event, result)
    
    return result
