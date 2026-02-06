"""Write tool for writing file contents."""

from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "write"})


class WriteTool(Tool):
    """Tool for writing file contents."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write",
            description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Use this for creating new files or completely replacing file contents.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file to write (relative to project directory)",
                    required=True,
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write to the file",
                    required=True,
                ),
                ToolParameter(
                    name="create_dirs",
                    type="boolean",
                    description="Create parent directories if they don't exist",
                    required=False,
                    default=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "path": {"type": "string"},
                    "bytes_written": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Write a file."""
        file_path = params.get("path", "")
        content = params.get("content", "")
        create_dirs = params.get("create_dirs", True)

        if not file_path:
            return {
                "success": False,
                "error": "No file path provided",
            }

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / file_path

        log.info("Writing file", {"path": file_path, "content_length": len(content)})

        try:
            # Ensure the path is within project directory
            try:
                full_path.relative_to(Path(project_dir).resolve())
            except ValueError:
                return {
                    "success": False,
                    "error": "Path escapes project directory",
                }

            # Create parent directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            bytes_written = full_path.write_text(content, encoding="utf-8")

            return {
                "success": True,
                "path": file_path,
                "bytes_written": bytes_written,
            }

        except Exception as e:
            log.error("Failed to write file", {"error": str(e), "path": file_path})
            return {
                "success": False,
                "error": f"Error writing file: {e}",
            }


# Singleton instance
_write_tool = WriteTool()


def get_tool() -> WriteTool:
    """Get the write tool instance."""
    return _write_tool
