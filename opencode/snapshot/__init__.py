"""Snapshot module for opencode."""

from opencode.snapshot.index import (
    Patch,
    FileDiff,
    init,
    cleanup,
    track,
    patch,
    restore,
    revert,
    diff,
    diff_full,
)

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
