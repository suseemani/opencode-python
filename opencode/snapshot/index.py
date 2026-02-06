"""Snapshot module for opencode."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode import config
from opencode.global_path import index as global_path
from opencode.project import instance
from opencode.scheduler import index as scheduler
from opencode.shell import index as shell
from opencode.util import log

logger = log.create(service="snapshot")

HOUR_MS = 60 * 60 * 1000
PRUNE = "7.days"


class Patch(BaseModel):
    """Snapshot patch."""
    hash: str
    files: list[str]


class FileDiff(BaseModel):
    """File diff information."""
    file: str
    before: str
    after: str
    additions: int
    deletions: int
    status: str | None = Field(default=None, description="added, deleted, or modified")


async def _git_dir() -> Path:
    """Get the git directory for snapshots."""
    project = await instance.project()
    return Path(global_path.data) / "snapshot" / project["id"]


def init() -> None:
    """Initialize snapshot module with scheduled cleanup."""
    scheduler.register(
        id="snapshot.cleanup",
        interval=HOUR_MS,
        run=cleanup,
        scope="instance",
    )


async def cleanup() -> None:
    """Clean up old snapshots."""
    project = await instance.project()
    if project.get("vcs") != "git":
        return
    
    cfg = await config.get()
    if cfg.get("snapshot") is False:
        return
    
    git = await _git_dir()
    if not git.exists():
        return
    
    worktree = await instance.worktree()
    directory = await instance.directory()
    
    result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} gc --prune={PRUNE}",
        cwd=directory,
    )
    
    if result.exit_code != 0:
        logger.warn("cleanup failed", {
            "exit_code": result.exit_code,
            "stderr": result.stderr,
        })
        return
    
    logger.info("cleanup", {"prune": PRUNE})


async def track() -> str | None:
    """Track current state in snapshot."""
    project = await instance.project()
    if project.get("vcs") != "git":
        return None
    
    cfg = await config.get()
    if cfg.get("snapshot") is False:
        return None
    
    git = await _git_dir()
    worktree = await instance.worktree()
    directory = await instance.directory()
    
    # Initialize git repo if needed
    git.mkdir(parents=True, exist_ok=True)
    if not (git / "HEAD").exists():
        env = {**asyncio.get_event_loop().get_debug() if False else {}}
        init_result = await shell.run(
            "git init",
            cwd=str(git),
            env={"GIT_DIR": str(git), "GIT_WORK_TREE": worktree},
        )
        await shell.run(
            f"git --git-dir {git} config core.autocrlf false",
            cwd=str(git),
        )
        logger.info("initialized snapshot git repo")
    
    # Add all files
    await shell.run(
        f"git --git-dir {git} --work-tree {worktree} add .",
        cwd=directory,
    )
    
    # Write tree
    result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} write-tree",
        cwd=directory,
    )
    
    hash_val = result.stdout.strip()
    logger.info("tracking", {"hash": hash_val, "cwd": directory, "git": str(git)})
    return hash_val


async def patch(hash_val: str) -> Patch:
    """Get patch for a snapshot hash."""
    git = await _git_dir()
    worktree = await instance.worktree()
    directory = await instance.directory()
    
    # Add all current files
    await shell.run(
        f"git --git-dir {git} --work-tree {worktree} add .",
        cwd=directory,
    )
    
    # Get diff
    result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} diff --no-ext-diff --name-only {hash_val} -- .",
        cwd=directory,
    )
    
    if result.exit_code != 0:
        logger.warn("failed to get diff", {"hash": hash_val, "exit_code": result.exit_code})
        return Patch(hash=hash_val, files=[])
    
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    return Patch(
        hash=hash_val,
        files=[str(Path(worktree) / f) for f in files],
    )


async def restore(snapshot: str) -> None:
    """Restore a snapshot."""
    logger.info("restore", {"commit": snapshot})
    git = await _git_dir()
    worktree = await instance.worktree()
    
    result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} read-tree {snapshot} && "
        f"git --git-dir {git} --work-tree {worktree} checkout-index -a -f",
        cwd=worktree,
    )
    
    if result.exit_code != 0:
        logger.error("failed to restore snapshot", {
            "snapshot": snapshot,
            "exit_code": result.exit_code,
            "stderr": result.stderr,
        })


async def revert(patches: list[Patch]) -> None:
    """Revert files from patches."""
    files: set[str] = set()
    git = await _git_dir()
    worktree = await instance.worktree()
    
    for item in patches:
        for file in item.files:
            if file in files:
                continue
            
            logger.info("reverting", {"file": file, "hash": item.hash})
            relative_path = str(Path(file).relative_to(worktree))
            
            result = await shell.run(
                f"git --git-dir {git} --work-tree {worktree} checkout {item.hash} -- {relative_path}",
                cwd=worktree,
            )
            
            if result.exit_code != 0:
                # Check if file existed in tree
                check_result = await shell.run(
                    f"git --git-dir {git} --work-tree {worktree} ls-tree {item.hash} -- {relative_path}",
                    cwd=worktree,
                )
                if check_result.exit_code == 0 and check_result.stdout.strip():
                    logger.info("file existed in snapshot but checkout failed, keeping", {"file": file})
                else:
                    logger.info("file did not exist in snapshot, deleting", {"file": file})
                    Path(file).unlink(missing_ok=True)
            
            files.add(file)


async def diff(hash_val: str) -> str:
    """Get diff for a snapshot."""
    git = await _git_dir()
    worktree = await instance.worktree()
    directory = await instance.directory()
    
    # Add all current files
    await shell.run(
        f"git --git-dir {git} --work-tree {worktree} add .",
        cwd=directory,
    )
    
    result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} diff --no-ext-diff {hash_val} -- .",
        cwd=worktree,
    )
    
    if result.exit_code != 0:
        logger.warn("failed to get diff", {
            "hash": hash_val,
            "exit_code": result.exit_code,
            "stderr": result.stderr,
        })
        return ""
    
    return result.stdout.strip()


async def diff_full(from_hash: str, to_hash: str) -> list[FileDiff]:
    """Get full diff between two snapshots."""
    git = await _git_dir()
    worktree = await instance.worktree()
    directory = await instance.directory()
    
    result: list[FileDiff] = []
    status_map: dict[str, str] = {}
    
    # Get status
    status_result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} diff --no-ext-diff --name-status --no-renames {from_hash} {to_hash} -- .",
        cwd=directory,
    )
    
    for line in status_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            code, file = parts[0], parts[1]
            kind = "added" if code.startswith("A") else "deleted" if code.startswith("D") else "modified"
            status_map[file] = kind
    
    # Get numstat
    numstat_result = await shell.run(
        f"git --git-dir {git} --work-tree {worktree} diff --no-ext-diff --no-renames --numstat {from_hash} {to_hash} -- .",
        cwd=directory,
    )
    
    for line in numstat_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            additions, deletions, file = parts[0], parts[1], parts[2]
            is_binary = additions == "-" and deletions == "-"
            
            if is_binary:
                before = ""
                after = ""
                added = 0
                deleted = 0
            else:
                before_result = await shell.run(
                    f"git --git-dir {git} --work-tree {worktree} show {from_hash}:{file}",
                    cwd=worktree,
                )
                after_result = await shell.run(
                    f"git --git-dir {git} --work-tree {worktree} show {to_hash}:{file}",
                    cwd=worktree,
                )
                before = before_result.stdout
                after = after_result.stdout
                added = int(additions) if additions.isdigit() else 0
                deleted = int(deletions) if deletions.isdigit() else 0
            
            result.append(FileDiff(
                file=file,
                before=before,
                after=after,
                additions=added,
                deletions=deleted,
                status=status_map.get(file, "modified"),
            ))
    
    return result


__all__ = [
    "Patch",
    "FileDiff",
    "init",
    "cleanup",
    "track",
    "patch",
    "restore",
    "revert",
    "diff",
    "diff_full",
]
