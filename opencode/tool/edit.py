"""Edit tool for modifying file contents."""

import re
from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "edit"})


class EditTool(Tool):
    """Tool for editing file contents using various strategies."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="edit",
            description="Edit a file by replacing content. Supports multiple edit modes: replace (exact string replacement), regex (pattern replacement), or line-based edits.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file to edit (relative to project directory)",
                    required=True,
                ),
                ToolParameter(
                    name="old_string",
                    type="string",
                    description="The text/pattern to find and replace",
                    required=True,
                ),
                ToolParameter(
                    name="new_string",
                    type="string",
                    description="The replacement text",
                    required=True,
                ),
                ToolParameter(
                    name="mode",
                    type="string",
                    description="Edit mode: 'replace' for exact match, 'regex' for pattern match",
                    required=False,
                    default="replace",
                ),
                ToolParameter(
                    name="occurrences",
                    type="integer",
                    description="Number of occurrences to replace (0 = all, default: 1)",
                    required=False,
                    default=1,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "replacements": {"type": "integer"},
                    "path": {"type": "string"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Edit a file."""
        file_path = params.get("path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        mode = params.get("mode", "replace")
        occurrences = params.get("occurrences", 1)

        if not file_path:
            return {"success": False, "error": "No file path provided"}

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / file_path

        log.info("Editing file", {"path": file_path, "mode": mode})

        try:
            # Ensure path is within project directory
            try:
                full_path.relative_to(Path(project_dir).resolve())
            except ValueError:
                return {"success": False, "error": "Path escapes project directory"}

            if not full_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read current content
            content = full_path.read_text(encoding="utf-8")
            original_content = content

            if mode == "regex":
                # Regex replacement
                flags = re.MULTILINE
                if occurrences == 0:
                    new_content, count = re.subn(old_string, new_string, content, flags=flags)
                else:
                    new_content = re.sub(old_string, new_string, content, count=occurrences, flags=flags)
                    count = occurrences if old_string in content else 0
            else:
                # Exact string replacement
                if occurrences == 0:
                    new_content = content.replace(old_string, new_string)
                    count = original_content.count(old_string)
                else:
                    count = 0
                    new_content = content
                    for _ in range(occurrences):
                        if old_string in new_content:
                            new_content = new_content.replace(old_string, new_string, 1)
                            count += 1
                        else:
                            break

            if count == 0:
                return {
                    "success": False,
                    "error": "Pattern not found in file",
                    "replacements": 0,
                }

            # Write the modified content
            full_path.write_text(new_content, encoding="utf-8")

            return {
                "success": True,
                "replacements": count,
                "path": file_path,
            }

        except Exception as e:
            log.error("Failed to edit file", {"error": str(e), "path": file_path})
            return {
                "success": False,
                "error": f"Error editing file: {e}",
                "replacements": 0,
            }


# Singleton instance
_edit_tool = EditTool()


def get_tool() -> EditTool:
    """Get the edit tool instance."""
    return _edit_tool
