"""File operations module."""

from .index import (
    FileContent,
    FileInfo,
    FileManager,
    FileNode,
    FilePatch,
    PatchHunk,
    is_binary_by_extension,
    is_image,
    is_image_by_extension,
)

__all__ = [
    "FileContent",
    "FileInfo",
    "FileManager",
    "FileNode",
    "FilePatch",
    "PatchHunk",
    "is_binary_by_extension",
    "is_image",
    "is_image_by_extension",
]
