"""Patch module for opencode."""

from opencode.patch.index import (
    UpdateFileChunk,
    HunkAdd,
    HunkDelete,
    HunkUpdate,
    Hunk,
    AffectedPaths,
    ApplyPatchError,
    MaybeApplyPatch,
    MaybeApplyPatchVerified,
    parse_patch,
    derive_new_contents_from_chunks,
    apply_hunks_to_files,
    apply_patch,
)

__all__ = [
    "UpdateFileChunk",
    "HunkAdd",
    "HunkDelete",
    "HunkUpdate",
    "Hunk",
    "AffectedPaths",
    "ApplyPatchError",
    "MaybeApplyPatch",
    "MaybeApplyPatchVerified",
    "parse_patch",
    "derive_new_contents_from_chunks",
    "apply_hunks_to_files",
    "apply_patch",
]
