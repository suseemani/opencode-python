"""Patch module for opencode."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import log

logger = log.create(service="patch")


class UpdateFileChunk(BaseModel):
    """Chunk for updating a file."""
    old_lines: list[str] = Field(default_factory=list)
    new_lines: list[str] = Field(default_factory=list)
    change_context: str | None = Field(default=None)
    is_end_of_file: bool = Field(default=False)


class HunkAdd(BaseModel):
    """Add file hunk."""
    type: str = Field(default="add")
    path: str
    contents: str


class HunkDelete(BaseModel):
    """Delete file hunk."""
    type: str = Field(default="delete")
    path: str


class HunkUpdate(BaseModel):
    """Update file hunk."""
    type: str = Field(default="update")
    path: str
    move_path: str | None = Field(default=None)
    chunks: list[UpdateFileChunk] = Field(default_factory=list)


Hunk = HunkAdd | HunkDelete | HunkUpdate


class AffectedPaths(BaseModel):
    """Affected paths from patch application."""
    added: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)


class ApplyPatchError(Enum):
    """Apply patch errors."""
    PARSE_ERROR = "ParseError"
    IO_ERROR = "IoError"
    COMPUTE_REPLACEMENTS = "ComputeReplacements"
    IMPLICIT_INVOCATION = "ImplicitInvocation"


class MaybeApplyPatch(Enum):
    """Maybe apply patch result types."""
    BODY = "Body"
    SHELL_PARSE_ERROR = "ShellParseError"
    PATCH_PARSE_ERROR = "PatchParseError"
    NOT_APPLY_PATCH = "NotApplyPatch"


class MaybeApplyPatchVerified(Enum):
    """Verified maybe apply patch result types."""
    BODY = "Body"
    SHELL_PARSE_ERROR = "ShellParseError"
    CORRECTNESS_ERROR = "CorrectnessError"
    NOT_APPLY_PATCH = "NotApplyPatch"


def _strip_heredoc(input: str) -> str:
    """Strip heredoc syntax from patch text."""
    pattern = r"^(?:cat\s+)?<<['"]*(\w+)['"]*\s*\n([\s\S]*?)\n\1\s*$"
    match = re.match(pattern, input)
    if match:
        return match.group(2)
    return input


def _parse_patch_header(lines: list[str], start_idx: int) -> tuple[str, str | None, int] | None:
    """Parse patch header."""
    if start_idx >= len(lines):
        return None
    
    line = lines[start_idx]
    
    if line.startswith("*** Add File:"):
        parts = line.split(":", 1)
        if len(parts) > 1:
            return parts[1].strip(), None, start_idx + 1
        return None
    
    if line.startswith("*** Delete File:"):
        parts = line.split(":", 1)
        if len(parts) > 1:
            return parts[1].strip(), None, start_idx + 1
        return None
    
    if line.startswith("*** Update File:"):
        parts = line.split(":", 1)
        if len(parts) <= 1:
            return None
        file_path = parts[1].strip()
        move_path: str | None = None
        next_idx = start_idx + 1
        
        if next_idx < len(lines) and lines[next_idx].startswith("*** Move to:"):
            move_parts = lines[next_idx].split(":", 1)
            if len(move_parts) > 1:
                move_path = move_parts[1].strip()
            next_idx += 1
        
        return file_path, move_path, next_idx
    
    return None


def _parse_update_file_chunks(lines: list[str], start_idx: int) -> tuple[list[UpdateFileChunk], int]:
    """Parse update file chunks."""
    chunks: list[UpdateFileChunk] = []
    i = start_idx
    
    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("@@"):
            context_line = lines[i][2:].strip()
            i += 1
            
            old_lines: list[str] = []
            new_lines: list[str] = []
            is_end_of_file = False
            
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("***"):
                change_line = lines[i]
                
                if change_line == "*** End of File":
                    is_end_of_file = True
                    i += 1
                    break
                
                if change_line.startswith(" "):
                    content = change_line[1:]
                    old_lines.append(content)
                    new_lines.append(content)
                elif change_line.startswith("-"):
                    old_lines.append(change_line[1:])
                elif change_line.startswith("+"):
                    new_lines.append(change_line[1:])
                
                i += 1
            
            chunks.append(UpdateFileChunk(
                old_lines=old_lines,
                new_lines=new_lines,
                change_context=context_line or None,
                is_end_of_file=is_end_of_file,
            ))
        else:
            i += 1
    
    return chunks, i


def _parse_add_file_content(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Parse add file content."""
    content_lines: list[str] = []
    i = start_idx
    
    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("+"):
            content_lines.append(lines[i][1:])
        i += 1
    
    return "\n".join(content_lines), i


def parse_patch(patch_text: str) -> dict[str, list[Hunk]]:
    """Parse patch text into hunks."""
    cleaned = _strip_heredoc(patch_text.strip())
    lines = cleaned.split("\n")
    hunks: list[Hunk] = []
    i = 0
    
    begin_marker = "*** Begin Patch"
    end_marker = "*** End Patch"
    
    begin_idx = next((idx for idx, line in enumerate(lines) if line.strip() == begin_marker), -1)
    end_idx = next((idx for idx, line in enumerate(lines) if line.strip() == end_marker), -1)
    
    if begin_idx == -1 or end_idx == -1 or begin_idx >= end_idx:
        raise ValueError("Invalid patch format: missing Begin/End markers")
    
    i = begin_idx + 1
    
    while i < end_idx:
        header = _parse_patch_header(lines, i)
        if not header:
            i += 1
            continue
        
        file_path, move_path, next_idx = header
        
        if lines[i].startswith("*** Add File:"):
            content, next_i = _parse_add_file_content(lines, next_idx)
            hunks.append(HunkAdd(path=file_path, contents=content))
            i = next_i
        elif lines[i].startswith("*** Delete File:"):
            hunks.append(HunkDelete(path=file_path))
            i = next_idx
        elif lines[i].startswith("*** Update File:"):
            chunks, next_i = _parse_update_file_chunks(lines, next_idx)
            hunks.append(HunkUpdate(path=file_path, move_path=move_path, chunks=chunks))
            i = next_i
        else:
            i += 1
    
    return {"hunks": hunks}


def _normalize_unicode(text: str) -> str:
    """Normalize Unicode punctuation to ASCII equivalents."""
    return (text
        .replace("\u2018", "'").replace("\u2019", "'").replace("\u201A", "'").replace("\u201B", "'")
        .replace("\u201C", '"').replace("\u201D", '"').replace("\u201E", '"').replace("\u201F", '"')
        .replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2015", "-")
        .replace("\u2026", "...")
        .replace("\u00A0", " ")
    )


def _seek_sequence(lines: list[str], pattern: list[str], start_index: int, eof: bool = False) -> int:
    """Find pattern in lines starting from start_index."""
    if not pattern:
        return -1
    
    def try_match(compare_func) -> int:
        if eof:
            from_end = len(lines) - len(pattern)
            if from_end >= start_index:
                matches = all(compare_func(lines[from_end + j], pattern[j]) for j in range(len(pattern)))
                if matches:
                    return from_end
        
        for i in range(start_index, len(lines) - len(pattern) + 1):
            matches = all(compare_func(lines[i + j], pattern[j]) for j in range(len(pattern)))
            if matches:
                return i
        return -1
    
    # Pass 1: exact match
    exact = try_match(lambda a, b: a == b)
    if exact != -1:
        return exact
    
    # Pass 2: rstrip match
    rstrip = try_match(lambda a, b: a.rstrip() == b.rstrip())
    if rstrip != -1:
        return rstrip
    
    # Pass 3: trim match
    trim = try_match(lambda a, b: a.strip() == b.strip())
    if trim != -1:
        return trim
    
    # Pass 4: normalized match
    normalized = try_match(lambda a, b: _normalize_unicode(a.strip()) == _normalize_unicode(b.strip()))
    return normalized


def _compute_replacements(original_lines: list[str], file_path: str, chunks: list[UpdateFileChunk]) -> list[tuple[int, int, list[str]]]:
    """Compute replacements for file update."""
    replacements: list[tuple[int, int, list[str]]] = []
    line_index = 0
    
    for chunk in chunks:
        if chunk.change_context:
            context_idx = _seek_sequence(original_lines, [chunk.change_context], line_index)
            if context_idx == -1:
                raise ValueError(f"Failed to find context '{chunk.change_context}' in {file_path}")
            line_index = context_idx + 1
        
        if not chunk.old_lines:
            insertion_idx = len(original_lines) - 1 if original_lines and original_lines[-1] == "" else len(original_lines)
            replacements.append((insertion_idx, 0, chunk.new_lines))
            continue
        
        pattern = chunk.old_lines[:]
        new_slice = chunk.new_lines[:]
        found = _seek_sequence(original_lines, pattern, line_index, chunk.is_end_of_file)
        
        if found == -1 and pattern and pattern[-1] == "":
            pattern = pattern[:-1]
            if new_slice and new_slice[-1] == "":
                new_slice = new_slice[:-1]
            found = _seek_sequence(original_lines, pattern, line_index, chunk.is_end_of_file)
        
        if found != -1:
            replacements.append((found, len(pattern), new_slice))
            line_index = found + len(pattern)
        else:
            raise ValueError(f"Failed to find expected lines in {file_path}:\n{chr(10).join(chunk.old_lines)}")
    
    replacements.sort(key=lambda x: x[0])
    return replacements


def _apply_replacements(lines: list[str], replacements: list[tuple[int, int, list[str]]]) -> list[str]:
    """Apply replacements to lines."""
    result = lines[:]
    
    for i in range(len(replacements) - 1, -1, -1):
        start_idx, old_len, new_segment = replacements[i]
        result[start_idx:start_idx + old_len] = new_segment
    
    return result


def _generate_unified_diff(old_content: str, new_content: str) -> str:
    """Generate unified diff between old and new content."""
    old_lines = old_content.split("\n")
    new_lines = new_content.split("\n")
    
    diff_lines = ["@@ -1 +1 @@"]
    has_changes = False
    
    max_len = max(len(old_lines), len(new_lines))
    for i in range(max_len):
        old_line = old_lines[i] if i < len(old_lines) else ""
        new_line = new_lines[i] if i < len(new_lines) else ""
        
        if old_line != new_line:
            if old_line:
                diff_lines.append(f"-{old_line}")
            if new_line:
                diff_lines.append(f"+{new_line}")
            has_changes = True
        elif old_line:
            diff_lines.append(f" {old_line}")
    
    return "\n".join(diff_lines) if has_changes else ""


def derive_new_contents_from_chunks(file_path: str, chunks: list[UpdateFileChunk]) -> dict[str, str]:
    """Derive new file contents from update chunks."""
    try:
        original_content = Path(file_path).read_text(encoding="utf-8")
    except Exception as error:
        raise ValueError(f"Failed to read file {file_path}: {error}")
    
    original_lines = original_content.split("\n")
    
    if original_lines and original_lines[-1] == "":
        original_lines.pop()
    
    replacements = _compute_replacements(original_lines, file_path, chunks)
    new_lines = _apply_replacements(original_lines, replacements)
    
    if not new_lines or new_lines[-1] != "":
        new_lines.append("")
    
    new_content = "\n".join(new_lines)
    unified_diff = _generate_unified_diff(original_content, new_content)
    
    return {"unified_diff": unified_diff, "content": new_content}


async def apply_hunks_to_files(hunks: list[Hunk]) -> AffectedPaths:
    """Apply hunks to the filesystem."""
    if not hunks:
        raise ValueError("No files were modified.")
    
    added: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    
    for hunk in hunks:
        if isinstance(hunk, HunkAdd):
            path_obj = Path(hunk.path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(hunk.contents, encoding="utf-8")
            added.append(hunk.path)
            logger.info(f"Added file: {hunk.path}")
        
        elif isinstance(hunk, HunkDelete):
            Path(hunk.path).unlink(missing_ok=True)
            deleted.append(hunk.path)
            logger.info(f"Deleted file: {hunk.path}")
        
        elif isinstance(hunk, HunkUpdate):
            file_update = derive_new_contents_from_chunks(hunk.path, hunk.chunks)
            
            if hunk.move_path:
                move_path = Path(hunk.move_path)
                move_path.parent.mkdir(parents=True, exist_ok=True)
                move_path.write_text(file_update["content"], encoding="utf-8")
                Path(hunk.path).unlink(missing_ok=True)
                modified.append(hunk.move_path)
                logger.info(f"Moved file: {hunk.path} -> {hunk.move_path}")
            else:
                Path(hunk.path).write_text(file_update["content"], encoding="utf-8")
                modified.append(hunk.path)
                logger.info(f"Updated file: {hunk.path}")
    
    return AffectedPaths(added=added, modified=modified, deleted=deleted)


async def apply_patch(patch_text: str) -> AffectedPaths:
    """Apply a patch to the filesystem."""
    parsed = parse_patch(patch_text)
    return await apply_hunks_to_files(parsed["hunks"])


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
