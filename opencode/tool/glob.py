"""Glob tool for finding files by pattern."""

from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "glob"})


class GlobTool(Tool):
    """Tool for finding files using glob patterns."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="glob",
            description="Find files matching a glob pattern. Supports wildcards like *.py, **/*.ts, src/**/*.js, etc.",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Glob pattern to match files (e.g., '*.py', 'src/**/*.ts')",
                    required=True,
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directory to search in (relative to project directory)",
                    required=False,
                    default=".",
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of results to return",
                    required=False,
                    default=100,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "files": {"type": "array", "items": {"type": "string"}},
                    "total": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Find files matching glob pattern."""
        pattern = params.get("pattern", "")
        search_path = params.get("path", ".")
        limit = params.get("limit", 100)

        if not pattern:
            return {"files": [], "total": 0, "error": "No pattern provided"}

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / search_path

        log.info("Globbing", {"pattern": pattern, "path": search_path})

        try:
            # Use pathlib's glob
            if pattern.startswith("**") or "/" in pattern:
                # Recursive glob
                matches = list(full_path.rglob(pattern.replace("**/*", "*").lstrip("/")))
            else:
                # Simple glob
                matches = list(full_path.glob(pattern))

            # Filter to files only and get relative paths
            files = []
            for match in matches:
                if match.is_file():
                    try:
                        rel_path = str(match.relative_to(Path(project_dir).resolve()))
                        files.append(rel_path)
                    except ValueError:
                        files.append(str(match))

                if len(files) >= limit:
                    break

            return {
                "files": files,
                "total": len(files),
            }

        except Exception as e:
            log.error("Failed to glob", {"error": str(e), "pattern": pattern})
            return {
                "files": [],
                "total": 0,
                "error": f"Error globbing: {e}",
            }


# Singleton instance
_glob_tool = GlobTool()


def get_tool() -> GlobTool:
    """Get the glob tool instance."""
    return _glob_tool
