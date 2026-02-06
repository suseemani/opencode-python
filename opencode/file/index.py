"""File operations module."""

import base64
import fnmatch
import mimetypes
import os
import subprocess
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field

from opencode.bus import get_bus
from opencode.util import create as create_logger

log = create_logger({"service": "file"})


class FileInfo(BaseModel):
    """Information about a changed file."""

    path: str = Field(description="File path")
    added: int = Field(description="Number of lines added")
    removed: int = Field(description="Number of lines removed")
    status: Literal["added", "deleted", "modified"] = Field(description="Change status")


class FileNode(BaseModel):
    """A file system node (file or directory)."""

    name: str = Field(description="Node name")
    path: str = Field(description="Relative path")
    absolute: str = Field(description="Absolute path")
    type: Literal["file", "directory"] = Field(description="Node type")
    ignored: bool = Field(description="Whether the node is ignored")


class PatchHunk(BaseModel):
    """A hunk in a diff patch."""

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]


class FilePatch(BaseModel):
    """A diff patch."""

    old_file_name: str
    new_file_name: str
    old_header: str | None = None
    new_header: str | None = None
    hunks: List[PatchHunk]
    index: str | None = None


class FileContent(BaseModel):
    """Content of a file."""

    type: Literal["text", "binary"] = Field(description="Content type")
    content: str = Field(description="File content")
    diff: str | None = Field(None, description="Diff if file has changes")
    patch: FilePatch | None = Field(None, description="Patch information")
    encoding: Literal["base64"] | None = Field(None, description="Content encoding")
    mime_type: str | None = Field(None, description="MIME type")


# Binary file extensions
binary_extensions = {
    "exe", "dll", "pdb", "bin", "so", "dylib", "o", "a", "lib",
    "wav", "mp3", "ogg", "oga", "ogv", "ogx", "flac", "aac",
    "wma", "m4a", "weba", "mp4", "avi", "mov", "wmv", "flv",
    "webm", "mkv", "zip", "tar", "gz", "gzip", "bz", "bz2",
    "bzip", "bzip2", "7z", "rar", "xz", "lz", "z", "pdf",
    "doc", "docx", "ppt", "pptx", "xls", "xlsx", "dmg", "iso",
    "img", "vmdk", "ttf", "otf", "woff", "woff2", "eot",
    "sqlite", "db", "mdb", "apk", "ipa", "aab", "xapk", "app",
    "pkg", "deb", "rpm", "snap", "flatpak", "appimage", "msi",
    "msp", "jar", "war", "ear", "class", "kotlin_module", "dex",
    "vdex", "odex", "oat", "art", "wasm", "wat", "bc", "ll",
    "s", "ko", "sys", "drv", "efi", "rom", "com", "bat", "cmd",
    "ps1", "sh", "bash", "zsh", "fish",
}

# Image file extensions
image_extensions = {
    "png", "jpg", "jpeg", "gif", "bmp", "webp", "ico", "tif",
    "tiff", "svg", "svgz", "avif", "apng", "jxl", "heic", "heif",
    "raw", "cr2", "nef", "arw", "dng", "orf", "raf", "pef", "x3f",
}

# MIME types for images
image_mime_types = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "webp": "image/webp",
    "ico": "image/x-icon",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "svg": "image/svg+xml",
    "svgz": "image/svg+xml",
    "avif": "image/avif",
    "apng": "image/apng",
    "jxl": "image/jxl",
    "heic": "image/heic",
    "heif": "image/heif",
}


def is_image_by_extension(filepath: str) -> bool:
    """Check if a file is an image by its extension."""
    ext = Path(filepath).suffix.lower().lstrip(".")
    return ext in image_extensions


def get_image_mime_type(filepath: str) -> str:
    """Get the MIME type for an image file."""
    ext = Path(filepath).suffix.lower().lstrip(".")
    return image_mime_types.get(ext, f"image/{ext}")


def is_binary_by_extension(filepath: str) -> bool:
    """Check if a file is binary by its extension."""
    ext = Path(filepath).suffix.lower().lstrip(".")
    return ext in binary_extensions


def is_image(mime_type: str) -> bool:
    """Check if a MIME type is an image."""
    return mime_type.startswith("image/")


def should_encode(file_path: Path) -> bool:
    """Determine if a file should be base64 encoded."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        return False

    if mime_type.startswith("text/"):
        return False
    if "charset=" in mime_type:
        return False

    top = mime_type.split("/")[0]
    return top in ("image", "audio", "video", "font", "model", "multipart")


class FileManager:
    """Manages file operations within a project."""

    def __init__(self, project_dir: str, vcs: str = "git") -> None:
        self.project_dir = Path(project_dir)
        self.vcs = vcs
        self._cache: dict[str, List[str]] | None = None
        self._cache_fetching = False

    def _get_ignore_patterns(self) -> List[str]:
        """Get ignore patterns from .gitignore and .ignore files."""
        patterns = []

        gitignore = self.project_dir / ".gitignore"
        if gitignore.exists():
            patterns.extend(gitignore.read_text().splitlines())

        ignore_file = self.project_dir / ".ignore"
        if ignore_file.exists():
            patterns.extend(ignore_file.read_text().splitlines())

        return patterns

    def _is_ignored(self, path: str, patterns: List[str]) -> bool:
        """Check if a path matches ignore patterns."""
        for pattern in patterns:
            pattern = pattern.strip()
            if not pattern or pattern.startswith("#"):
                continue
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(
                Path(path).name, pattern
            ):
                return True
        return False

    async def status(self) -> List[FileInfo]:
        """Get the status of changed files in the project."""
        if self.vcs != "git":
            return []

        changed_files: List[FileInfo] = []

        # Get diff stats
        try:
            result = subprocess.run(
                ["git", "-c", "core.quotepath=false", "diff", "--numstat", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("\t")
                    if len(parts) == 3:
                        added, removed, filepath = parts
                        changed_files.append(
                            FileInfo(
                                path=filepath,
                                added=0 if added == "-" else int(added),
                                removed=0 if removed == "-" else int(removed),
                                status="modified",
                            )
                        )
        except Exception:
            pass

        # Get untracked files
        try:
            result = subprocess.run(
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout.strip():
                for filepath in result.stdout.strip().split("\n"):
                    try:
                        content = (self.project_dir / filepath).read_text()
                        lines = len(content.split("\n"))
                        changed_files.append(
                            FileInfo(
                                path=filepath,
                                added=lines,
                                removed=0,
                                status="added",
                            )
                        )
                    except Exception:
                        continue
        except Exception:
            pass

        # Get deleted files
        try:
            result = subprocess.run(
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "diff",
                    "--name-only",
                    "--diff-filter=D",
                    "HEAD",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout.strip():
                for filepath in result.stdout.strip().split("\n"):
                    changed_files.append(
                        FileInfo(
                            path=filepath,
                            added=0,
                            removed=0,
                            status="deleted",
                        )
                    )
        except Exception:
            pass

        return changed_files

    async def read(self, file_path: str) -> FileContent:
        """Read a file and return its content."""
        with log.time("read", {"file": file_path}):
            full_path = self.project_dir / file_path

            # Check if path is within project directory
            try:
                full_path.relative_to(self.project_dir)
            except ValueError:
                raise ValueError("Access denied: path escapes project directory")

            # Handle images
            if is_image_by_extension(file_path):
                if full_path.exists():
                    content = base64.b64encode(full_path.read_bytes()).decode()
                    mime_type = get_image_mime_type(file_path)
                    return FileContent(
                        type="text",
                        content=content,
                        mime_type=mime_type,
                        encoding="base64",
                    )
                return FileContent(type="text", content="")

            # Handle binary files
            if is_binary_by_extension(file_path):
                return FileContent(type="binary", content="")

            if not full_path.exists():
                return FileContent(type="text", content="")

            mime_type, _ = mimetypes.guess_type(str(full_path))
            mime_type = mime_type or "application/octet-stream"

            # Check if we should encode
            encode = should_encode(full_path)

            if encode and not is_image(mime_type):
                return FileContent(type="binary", content="", mime_type=mime_type)

            if encode:
                content = base64.b64encode(full_path.read_bytes()).decode()
                return FileContent(
                    type="text",
                    content=content,
                    mime_type=mime_type,
                    encoding="base64",
                )

            content = full_path.read_text().strip()

            # Get diff if in git
            if self.vcs == "git":
                try:
                    diff_result = subprocess.run(
                        ["git", "diff", file_path],
                        cwd=self.project_dir,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    diff = diff_result.stdout

                    if not diff.strip():
                        diff_result = subprocess.run(
                            ["git", "diff", "--staged", file_path],
                            cwd=self.project_dir,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        diff = diff_result.stdout

                    if diff.strip():
                        return FileContent(type="text", content=content, diff=diff)
                except Exception:
                    pass

            return FileContent(type="text", content=content)

    async def list(self, dir_path: str | None = None) -> List[FileNode]:
        """List files and directories in the given path."""
        exclude = {".git", ".DS_Store"}
        patterns = self._get_ignore_patterns()

        resolved = self.project_dir / (dir_path or "")

        # Check if path is within project directory
        try:
            resolved.relative_to(self.project_dir)
        except ValueError:
            raise ValueError("Access denied: path escapes project directory")

        nodes: List[FileNode] = []

        try:
            for entry in os.scandir(resolved):
                if entry.name in exclude:
                    continue

                full_path = Path(entry.path)
                relative_path = str(full_path.relative_to(self.project_dir))
                node_type = "directory" if entry.is_dir() else "file"
                ignored = self._is_ignored(
                    relative_path + "/" if node_type == "directory" else relative_path,
                    patterns,
                )

                nodes.append(
                    FileNode(
                        name=entry.name,
                        path=relative_path,
                        absolute=str(full_path),
                        type=node_type,
                        ignored=ignored,
                    )
                )
        except (OSError, IOError):
            pass

        # Sort directories first, then by name
        nodes.sort(key=lambda n: (n.type != "directory", n.name.lower()))
        return nodes

    async def search(
        self,
        query: str,
        limit: int = 100,
        dirs: bool | None = None,
        file_type: Literal["file", "directory"] | None = None,
    ) -> List[str]:
        """Search for files and directories matching the query."""
        query = query.strip()
        kind = file_type or ("all" if dirs is None or dirs else "file")

        log.info("search", {"query": query, "kind": kind})

        # Get cached file list
        files: List[str] = []
        directories: List[str] = []

        if self._cache is not None:
            files = self._cache.get("files", [])
            directories = self._cache.get("dirs", [])

        # Scan if no cache
        if not files and not directories:
            for root, dirs_list, files_list in os.walk(self.project_dir):
                # Skip ignored directories
                dirs_list[:] = [
                    d for d in dirs_list if not d.startswith(".") and d not in exclude
                ]

                rel_root = str(Path(root).relative_to(self.project_dir))
                if rel_root != ".":
                    directories.append(rel_root + "/")

                for file in files_list:
                    if not file.startswith("."):
                        if rel_root == ".":
                            files.append(file)
                        else:
                            files.append(f"{rel_root}/{file}")

        if not query:
            if kind == "file":
                return files[:limit]
            return directories[:limit]

        # Fuzzy search
        from fuzzywuzzy import fuzz

        items = files if kind == "file" else directories if kind == "directory" else files + directories
        scored = [(item, fuzz.partial_ratio(query, item)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [item for item, _ in scored[:limit]]


# Exclude patterns for scanning
exclude = {".git", "node_modules", "dist", "build", "target", "vendor"}
