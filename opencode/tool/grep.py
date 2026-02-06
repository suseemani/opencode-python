"""Grep tool for searching file contents."""

import re
import subprocess
from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "grep"})


class GrepTool(Tool):
    """Tool for searching file contents using patterns."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="grep",
            description="Search for patterns in file contents using regular expressions. Returns matching lines with file paths and line numbers.",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Regular expression pattern to search for",
                    required=True,
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directory or file to search in (relative to project directory)",
                    required=False,
                    default=".",
                ),
                ToolParameter(
                    name="file_pattern",
                    type="string",
                    description="Glob pattern to filter files (e.g., '*.py', '*.ts')",
                    required=False,
                ),
                ToolParameter(
                    name="case_sensitive",
                    type="boolean",
                    description="Whether the search is case sensitive",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of results to return",
                    required=False,
                    default=50,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "matches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "line": {"type": "integer"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "total": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Search for pattern in files."""
        pattern = params.get("pattern", "")
        search_path = params.get("path", ".")
        file_pattern = params.get("file_pattern")
        case_sensitive = params.get("case_sensitive", True)
        limit = params.get("limit", 50)

        if not pattern:
            return {"matches": [], "total": 0, "error": "No pattern provided"}

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / search_path

        log.info("Searching", {"pattern": pattern, "path": search_path})

        try:
            # Try to use ripgrep if available
            matches = await self._search_with_ripgrep(
                pattern, full_path, file_pattern, case_sensitive, limit
            )
        except Exception:
            # Fall back to Python implementation
            matches = await self._search_with_python(
                pattern, full_path, file_pattern, case_sensitive, limit
            )

        return {
            "matches": matches,
            "total": len(matches),
        }

    async def _search_with_ripgrep(
        self,
        pattern: str,
        path: Path,
        file_pattern: str | None,
        case_sensitive: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search using ripgrep."""
        cmd = ["rg", "--line-number", "--with-filename", "--no-heading"]

        if not case_sensitive:
            cmd.append("--ignore-case")

        if file_pattern:
            cmd.extend(["--glob", file_pattern])

        cmd.extend([pattern, str(path)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        matches = []
        for line in result.stdout.split("\n")[:limit]:
            if ":" not in line:
                continue

            parts = line.split(":", 2)
            if len(parts) >= 3:
                file_path, line_num, content = parts[0], parts[1], parts[2]
                try:
                    rel_path = str(Path(file_path).relative_to(Path(path)))
                except ValueError:
                    rel_path = file_path

                matches.append({
                    "path": rel_path,
                    "line": int(line_num),
                    "content": content.strip(),
                })

        return matches

    async def _search_with_python(
        self,
        pattern: str,
        path: Path,
        file_pattern: str | None,
        case_sensitive: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search using Python regex."""
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matches = []

        if path.is_file():
            files = [path]
        else:
            if file_pattern:
                files = list(path.rglob(file_pattern))
            else:
                files = [f for f in path.rglob("*") if f.is_file()]

        for file_path in files:
            if len(matches) >= limit:
                break

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        try:
                            rel_path = str(file_path.relative_to(path))
                        except ValueError:
                            rel_path = str(file_path)

                        matches.append({
                            "path": rel_path,
                            "line": i,
                            "content": line.strip(),
                        })

                        if len(matches) >= limit:
                            break
            except Exception:
                continue

        return matches


# Singleton instance
_grep_tool = GrepTool()


def get_tool() -> GrepTool:
    """Get the grep tool instance."""
    return _grep_tool
