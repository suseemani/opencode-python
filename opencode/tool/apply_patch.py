"""Apply patch tool for unified diff patches."""

import re
from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "apply_patch"})


def normalize_unicode(text: str) -> str:
    """Normalize Unicode punctuation to ASCII equivalents."""
    return (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201A", "'")
        .replace("\u201B", "'")
        .replace("\u201C", '"')
        .replace("\u201D", '"')
        .replace("\u201E", '"')
        .replace("\u201F", '"')
        .replace("\u2010", "-")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2015", "-")
        .replace("\u2026", "...")
        .replace("\u00A0", " ")
    )


def seek_sequence(lines: list[str], pattern: list[str], start_idx: int, eof: bool = False) -> int:
    """Find pattern in lines starting from start_idx with fuzzy matching."""
    if not pattern:
        return -1

    def try_match(compare_fn) -> int:
        # Try EOF anchor first
        if eof:
            from_end = len(lines) - len(pattern)
            if from_end >= start_idx:
                matches = all(compare_fn(lines[from_end + j], pattern[j]) for j in range(len(pattern)))
                if matches:
                    return from_end

        # Forward search
        for i in range(start_idx, len(lines) - len(pattern) + 1):
            matches = all(compare_fn(lines[i + j], pattern[j]) for j in range(len(pattern)))
            if matches:
                return i
        return -1

    # Try exact match
    result = try_match(lambda a, b: a == b)
    if result != -1:
        return result

    # Try rstrip match
    result = try_match(lambda a, b: a.rstrip() == b.rstrip())
    if result != -1:
        return result

    # Try trim match
    result = try_match(lambda a, b: a.strip() == b.strip())
    if result != -1:
        return result

    # Try normalized match
    result = try_match(lambda a, b: normalize_unicode(a.strip()) == normalize_unicode(b.strip()))
    return result


def parse_patch_header(lines: list[str], idx: int) -> tuple[str, str | None, int] | None:
    """Parse a patch header line and return (file_path, move_path, next_idx)."""
    line = lines[idx]

    if line.startswith("*** Add File:"):
        file_path = line.split(":", 1)[1].strip()
        return (file_path, None, idx + 1) if file_path else None

    if line.startswith("*** Delete File:"):
        file_path = line.split(":", 1)[1].strip()
        return (file_path, None, idx + 1) if file_path else None

    if line.startswith("*** Update File:"):
        file_path = line.split(":", 1)[1].strip()
        move_path = None
        next_idx = idx + 1

        if next_idx < len(lines) and lines[next_idx].startswith("*** Move to:"):
            move_path = lines[next_idx].split(":", 1)[1].strip()
            next_idx += 1

        return (file_path, move_path, next_idx) if file_path else None

    return None


def parse_update_chunks(lines: list[str], idx: int) -> tuple[list[dict], int]:
    """Parse update file chunks from patch lines."""
    chunks = []
    i = idx

    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("@@"):
            context = lines[i][2:].strip()
            i += 1

            old_lines = []
            new_lines = []
            is_eof = False

            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("***"):
                change_line = lines[i]

                if change_line == "*** End of File":
                    is_eof = True
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

            chunks.append({
                "old_lines": old_lines,
                "new_lines": new_lines,
                "context": context or None,
                "is_eof": is_eof,
            })
        else:
            i += 1

    return chunks, i


def parse_add_file_content(lines: list[str], idx: int) -> tuple[str, int]:
    """Parse add file content from patch lines."""
    content_lines = []
    i = idx

    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("+"):
            content_lines.append(lines[i][1:])
        i += 1

    return "\n".join(content_lines), i


class Hunk:
    """Represents a patch hunk."""

    def __init__(self, hunk_type: str, path: str, **kwargs):
        self.type = hunk_type
        self.path = path
        self.move_path = kwargs.get("move_path")
        self.contents = kwargs.get("contents", "")
        self.chunks = kwargs.get("chunks", [])


def parse_patch(patch_text: str) -> list[Hunk]:
    """Parse a patch text and return list of hunks."""
    # Strip heredoc wrapper if present
    heredoc_match = re.match(r"^(?:cat\s+)?<<['\"]?(\w+)['\"]?\s*\n([\s\S]*?)\n\1\s*$", patch_text.strip())
    if heredoc_match:
        patch_text = heredoc_match.group(2)

    lines = patch_text.split("\n")
    hunks = []

    begin_marker = "*** Begin Patch"
    end_marker = "*** End Patch"

    begin_idx = next((i for i, line in enumerate(lines) if line.strip() == begin_marker), -1)
    end_idx = next((i for i, line in enumerate(lines) if line.strip() == end_marker), -1)

    if begin_idx == -1 or end_idx == -1 or begin_idx >= end_idx:
        raise ValueError("Invalid patch format: missing Begin/End markers")

    i = begin_idx + 1
    while i < end_idx:
        header = parse_patch_header(lines, i)
        if not header:
            i += 1
            continue

        file_path, move_path, next_idx = header

        if lines[i].startswith("*** Add File:"):
            content, next_idx = parse_add_file_content(lines, next_idx)
            hunks.append(Hunk("add", file_path, contents=content))
            i = next_idx
        elif lines[i].startswith("*** Delete File:"):
            hunks.append(Hunk("delete", file_path))
            i = next_idx
        elif lines[i].startswith("*** Update File:"):
            chunks, next_idx = parse_update_chunks(lines, next_idx)
            hunks.append(Hunk("update", file_path, move_path=move_path, chunks=chunks))
            i = next_idx
        else:
            i += 1

    return hunks


def apply_chunks_to_content(file_path: str, chunks: list[dict]) -> tuple[str, str]:
    """Apply update chunks to file content. Returns (new_content, unified_diff)."""
    try:
        original_content = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")

    original_lines = original_content.split("\n")
    if original_lines and original_lines[-1] == "":
        original_lines.pop()

    replacements = []
    line_idx = 0

    for chunk in chunks:
        if chunk.get("context"):
            context_idx = seek_sequence(original_lines, [chunk["context"]], line_idx)
            if context_idx == -1:
                raise ValueError(f"Failed to find context '{chunk['context']}' in {file_path}")
            line_idx = context_idx + 1

        if not chunk["old_lines"]:
            # Pure addition
            insertion_idx = len(original_lines) - 1 if original_lines and original_lines[-1] == "" else len(original_lines)
            replacements.append((insertion_idx, 0, chunk["new_lines"]))
            continue

        pattern = chunk["old_lines"]
        new_slice = chunk["new_lines"]
        found = seek_sequence(original_lines, pattern, line_idx, chunk.get("is_eof", False))

        # Retry without trailing empty line
        if found == -1 and pattern and pattern[-1] == "":
            pattern = pattern[:-1]
            if new_slice and new_slice[-1] == "":
                new_slice = new_slice[:-1]
            found = seek_sequence(original_lines, pattern, line_idx, chunk.get("is_eof", False))

        if found != -1:
            replacements.append((found, len(pattern), new_slice))
            line_idx = found + len(pattern)
        else:
            raise ValueError(f"Failed to find expected lines in {file_path}:\n" + "\n".join(chunk["old_lines"]))

    # Apply replacements in reverse order
    result = original_lines.copy()
    for start_idx, old_len, new_segment in sorted(replacements, key=lambda x: x[0], reverse=True):
        result[start_idx:start_idx + old_len] = new_segment

    # Ensure trailing newline
    if not result or result[-1] != "":
        result.append("")

    new_content = "\n".join(result)

    # Generate simple unified diff
    diff_lines = ["@@ -1 +1 @@"]
    old_lines = original_content.split("\n")
    new_lines_list = new_content.split("\n")
    max_len = max(len(old_lines), len(new_lines_list))

    for i in range(max_len):
        old_line = old_lines[i] if i < len(old_lines) else ""
        new_line = new_lines_list[i] if i < len(new_lines_list) else ""

        if old_line != new_line:
            if old_line:
                diff_lines.append(f"-{old_line}")
            if new_line:
                diff_lines.append(f"+{new_line}")
        elif old_line:
            diff_lines.append(f" {old_line}")

    unified_diff = "\n".join(diff_lines)

    return new_content, unified_diff


class ApplyPatchTool(Tool):
    """Tool for applying unified diff patches to files."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="apply_patch",
            description="Apply a unified diff patch to files. Supports adding, deleting, updating, and moving files using a custom patch format with *** markers.",
            parameters=[
                ToolParameter(
                    name="patchText",
                    type="string",
                    description="The full patch text that describes all changes to be made",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "output": {"type": "string"},
                    "files_added": {"type": "array"},
                    "files_modified": {"type": "array"},
                    "files_deleted": {"type": "array"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Apply a patch to files."""
        patch_text = params.get("patchText", "")

        if not patch_text:
            return {
                "success": False,
                "output": "No patch text provided",
                "files_added": [],
                "files_modified": [],
                "files_deleted": [],
            }

        log.info("Applying patch")

        try:
            # Parse the patch
            hunks = parse_patch(patch_text)

            if not hunks:
                normalized = patch_text.replace("\r\n", "\n").replace("\r", "\n").strip()
                if normalized == "*** Begin Patch\n*** End Patch":
                    raise ValueError("patch rejected: empty patch")
                raise ValueError("apply_patch verification failed: no hunks found")

            project_dir = Path(context.project_dir or ".")
            files_added = []
            files_modified = []
            files_deleted = []

            # Apply each hunk
            for hunk in hunks:
                file_path = project_dir / hunk.path

                if hunk.type == "add":
                    # Create parent directories
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(hunk.contents, encoding="utf-8")
                    files_added.append(str(file_path.relative_to(project_dir)))
                    log.info(f"Added file: {file_path}")

                elif hunk.type == "delete":
                    if file_path.exists():
                        file_path.unlink()
                        files_deleted.append(str(file_path.relative_to(project_dir)))
                        log.info(f"Deleted file: {file_path}")

                elif hunk.type == "update":
                    if not file_path.exists():
                        raise ValueError(f"Failed to read file to update: {file_path}")

                    new_content, _ = apply_chunks_to_content(str(file_path), hunk.chunks)

                    if hunk.move_path:
                        # Move file
                        move_path = project_dir / hunk.move_path
                        move_path.parent.mkdir(parents=True, exist_ok=True)
                        move_path.write_text(new_content, encoding="utf-8")
                        file_path.unlink()
                        files_modified.append(str(move_path.relative_to(project_dir)))
                        log.info(f"Moved file: {file_path} -> {move_path}")
                    else:
                        # Regular update
                        file_path.write_text(new_content, encoding="utf-8")
                        files_modified.append(str(file_path.relative_to(project_dir)))
                        log.info(f"Updated file: {file_path}")

            # Build summary
            summary_lines = []
            for hunk in hunks:
                if hunk.type == "add":
                    summary_lines.append(f"A {hunk.path}")
                elif hunk.type == "delete":
                    summary_lines.append(f"D {hunk.path}")
                else:
                    target = hunk.move_path or hunk.path
                    summary_lines.append(f"M {target}")

            output = f"Success. Updated the following files:\n" + "\n".join(summary_lines)

            return {
                "success": True,
                "output": output,
                "files_added": files_added,
                "files_modified": files_modified,
                "files_deleted": files_deleted,
            }

        except Exception as e:
            log.error("Failed to apply patch", {"error": str(e)})
            return {
                "success": False,
                "output": f"Failed to apply patch: {e}",
                "files_added": [],
                "files_modified": [],
                "files_deleted": [],
            }


# Singleton instance
_apply_patch_tool = ApplyPatchTool()


def get_tool() -> ApplyPatchTool:
    """Get the apply_patch tool instance."""
    return _apply_patch_tool
