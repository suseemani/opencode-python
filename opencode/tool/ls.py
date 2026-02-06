"""Ls tool for listing directory contents."""

from pathlib import Path
from typing import Any

from opencode.file import FileManager, FileNode
from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "ls"})


class LsTool(Tool):
    """Tool for listing directory contents."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="ls",
            description="List the contents of a directory. Shows files and directories with their types and ignore status.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directory path to list (relative to project directory, defaults to current directory)",
                    required=False,
                    default=".",
                ),
                ToolParameter(
                    name="show_hidden",
                    type="boolean",
                    description="Whether to show hidden files (starting with .)",
                    required=False,
                    default=False,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "entries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "path": {"type": "string"},
                                "type": {"type": "string", "enum": ["file", "directory"]},
                                "ignored": {"type": "boolean"},
                            },
                        },
                    },
                    "total": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """List directory contents."""
        dir_path = params.get("path", ".")
        show_hidden = params.get("show_hidden", False)

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / dir_path

        log.info("Listing directory", {"path": dir_path})

        try:
            # Check if path exists and is a directory
            if not full_path.exists():
                return {
                    "entries": [],
                    "total": 0,
                    "error": f"Path not found: {dir_path}",
                }

            if not full_path.is_dir():
                return {
                    "entries": [],
                    "total": 0,
                    "error": f"Path is not a directory: {dir_path}",
                }

            # Use FileManager to list
            file_manager = FileManager(project_dir)
            nodes = await file_manager.list(dir_path if dir_path != "." else None)

            # Filter hidden files if needed
            if not show_hidden:
                nodes = [n for n in nodes if not n.name.startswith(".")]

            # Convert to dict format
            entries = [
                {
                    "name": node.name,
                    "path": node.path,
                    "type": node.type,
                    "ignored": node.ignored,
                }
                for node in nodes
            ]

            return {
                "entries": entries,
                "total": len(entries),
            }

        except Exception as e:
            log.error("Failed to list directory", {"error": str(e), "path": dir_path})
            return {
                "entries": [],
                "total": 0,
                "error": f"Error listing directory: {e}",
            }


# Singleton instance
_ls_tool = LsTool()


def get_tool() -> LsTool:
    """Get the ls tool instance."""
    return _ls_tool
