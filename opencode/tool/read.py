"""Read tool for reading file contents."""

from pathlib import Path
from typing import Any

from opencode.file import FileManager
from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "read"})


class ReadTool(Tool):
    """Tool for reading file contents."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read",
            description="Read the contents of a file. Use this to view code, configuration files, or any text file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file to read (relative to project directory)",
                    required=True,
                ),
                ToolParameter(
                    name="offset",
                    type="integer",
                    description="Line offset to start reading from (0-indexed)",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of lines to read",
                    required=False,
                    default=200,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "type": {"type": "string", "enum": ["text", "binary"]},
                    "mime_type": {"type": "string"},
                    "encoding": {"type": "string"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Read a file."""
        file_path = params.get("path", "")
        offset = params.get("offset", 0)
        limit = params.get("limit", 200)

        if not file_path:
            return {
                "content": "",
                "type": "text",
                "error": "No file path provided",
            }

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / file_path

        log.info("Reading file", {"path": file_path, "offset": offset, "limit": limit})

        try:
            # Check if file exists
            if not full_path.exists():
                return {
                    "content": "",
                    "type": "text",
                    "error": f"File not found: {file_path}",
                }

            # Check if it's a directory
            if full_path.is_dir():
                return {
                    "content": "",
                    "type": "text",
                    "error": f"Path is a directory: {file_path}",
                }

            # Use FileManager for reading
            file_manager = FileManager(project_dir)
            result = await file_manager.read(file_path)

            # Apply offset and limit if text
            if result.type == "text" and result.content:
                lines = result.content.split("\n")
                if offset > 0:
                    lines = lines[offset:]
                if limit and len(lines) > limit:
                    lines = lines[:limit]
                    lines.append(f"\n... ({len(lines) - limit} more lines)")
                content = "\n".join(lines)
            else:
                content = result.content

            return {
                "content": content,
                "type": result.type,
                "mime_type": result.mime_type,
                "encoding": result.encoding,
            }

        except Exception as e:
            log.error("Failed to read file", {"error": str(e), "path": file_path})
            return {
                "content": "",
                "type": "text",
                "error": f"Error reading file: {e}",
            }


# Singleton instance
_read_tool = ReadTool()


def get_tool() -> ReadTool:
    """Get the read tool instance."""
    return _read_tool
