"""Worktree module for opencode."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorktreeInfo(BaseModel):
    """Worktree information."""
    path: str = Field(description="Worktree path")
    branch: str = Field(description="Git branch")
    is_main: bool = Field(description="Is main worktree")


async def list_worktrees(git_dir: str) -> list[WorktreeInfo]:
    """List all git worktrees."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=git_dir,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            return []
        
        worktrees = []
        lines = result.stdout.strip().split("\n")
        current = {}
        
        for line in lines:
            if line.startswith("worktree "):
                if current:
                    worktrees.append(WorktreeInfo(
                        path=current.get("path", ""),
                        branch=current.get("branch", ""),
                        is_main=current.get("bare", False),
                    ))
                current = {"path": line[9:]}
            elif line.startswith("branch "):
                current["branch"] = line[7:]
            elif line == "bare":
                current["bare"] = True
        
        if current:
            worktrees.append(WorktreeInfo(
                path=current.get("path", ""),
                branch=current.get("branch", ""),
                is_main=current.get("bare", False),
            ))
        
        return worktrees
    except Exception:
        return []


async def create(git_dir: str, path: str, branch: str) -> bool:
    """Create a new worktree."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "worktree", "add", path, branch],
            cwd=git_dir,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


async def remove(git_dir: str, path: str) -> bool:
    """Remove a worktree."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "worktree", "remove", path],
            cwd=git_dir,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False
