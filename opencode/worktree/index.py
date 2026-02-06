"""Git worktree management."""

import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "worktree"})


class WorktreeInfo(BaseModel):
    """Git worktree information."""
    
    path: str = Field(description="Worktree path")
    commit: str = Field(description="Current commit hash")
    branch: str | None = Field(default=None, description="Branch name")
    is_main: bool = Field(default=False, description="Whether this is the main worktree")
    is_detached: bool = Field(default=False, description="Whether HEAD is detached")


class WorktreeManager:
    """Manages git worktrees."""
    
    def __init__(self, repo_path: str = ".") -> None:
        self.repo_path = Path(repo_path)
    
    def _run_git(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(
            ["git", "-C", str(self.repo_path), *args],
            capture_output=True,
            text=True,
        )
    
    def is_git_repo(self) -> bool:
        """Check if path is a git repository."""
        result = self._run_git(["rev-parse", "--git-dir"])
        return result.returncode == 0
    
    def list_worktrees(self) -> list[WorktreeInfo]:
        """List all worktrees."""
        result = self._run_git(["worktree", "list", "--porcelain"])
        
        if result.returncode != 0:
            log.error("Failed to list worktrees", {"error": result.stderr})
            return []
        
        worktrees = []
        current = {}
        
        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(self._parse_worktree(current))
                current = {"path": line[9:]}
            elif line.startswith("HEAD "):
                current["commit"] = line[5:]
            elif line.startswith("branch "):
                current["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "detached":
                current["detached"] = True
        
        if current:
            worktrees.append(self._parse_worktree(current))
        
        # Mark main worktree
        if worktrees:
            worktrees[0].is_main = True
        
        return worktrees
    
    def _parse_worktree(self, data: dict[str, Any]) -> WorktreeInfo:
        """Parse worktree data."""
        return WorktreeInfo(
            path=data.get("path", ""),
            commit=data.get("commit", ""),
            branch=data.get("branch"),
            is_detached=data.get("detached", False),
        )
    
    def create_worktree(
        self,
        path: str,
        branch: str | None = None,
        commit: str | None = None,
    ) -> WorktreeInfo | None:
        """Create a new worktree."""
        args = ["worktree", "add", path]
        
        if branch:
            args.append(branch)
        elif commit:
            args.extend(["-d", commit])
        
        result = self._run_git(args)
        
        if result.returncode != 0:
            log.error("Failed to create worktree", {"error": result.stderr})
            return None
        
        # Get the newly created worktree info
        worktrees = self.list_worktrees()
        for wt in worktrees:
            if wt.path == path or wt.path == str(Path(self.repo_path) / path):
                return wt
        
        return None
    
    def remove_worktree(self, path: str, force: bool = False) -> bool:
        """Remove a worktree."""
        args = ["worktree", "remove"]
        
        if force:
            args.append("--force")
        
        args.append(path)
        
        result = self._run_git(args)
        
        if result.returncode != 0:
            log.error("Failed to remove worktree", {"error": result.stderr})
            return False
        
        return True
    
    def prune_worktrees(self) -> bool:
        """Prune stale worktrees."""
        result = self._run_git(["worktree", "prune"])
        return result.returncode == 0
    
    def move_worktree(self, old_path: str, new_path: str) -> bool:
        """Move a worktree."""
        result = self._run_git(["worktree", "move", old_path, new_path])
        
        if result.returncode != 0:
            log.error("Failed to move worktree", {"error": result.stderr})
            return False
        
        return True
    
    def lock_worktree(self, path: str, reason: str | None = None) -> bool:
        """Lock a worktree."""
        args = ["worktree", "lock"]
        
        if reason:
            args.extend(["--reason", reason])
        
        args.append(path)
        
        result = self._run_git(args)
        return result.returncode == 0
    
    def unlock_worktree(self, path: str) -> bool:
        """Unlock a worktree."""
        result = self._run_git(["worktree", "unlock", path])
        return result.returncode == 0


# Convenience function
def get_manager(repo_path: str = ".") -> WorktreeManager:
    """Get a worktree manager for a repository."""
    return WorktreeManager(repo_path)
