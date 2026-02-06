"""Multi-edit tool for batch file modifications."""

from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.tool.edit import get_tool as get_edit_tool
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "multiedit"})


class MultiEditTool(Tool):
    """Tool for performing multiple edit operations on a single file."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="multiedit",
            description="Edit a file by applying multiple edit operations sequentially. Each edit is applied in order, with the output of each edit becoming the input for the next.",
            parameters=[
                ToolParameter(
                    name="filePath",
                    type="string",
                    description="The absolute or relative path to the file to modify",
                    required=True,
                ),
                ToolParameter(
                    name="edits",
                    type="array",
                    description="Array of edit operations to perform sequentially on the file",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "replacements": {"type": "integer"},
                    "path": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute multiple edits on a file."""
        file_path = params.get("filePath", "")
        edits = params.get("edits", [])

        if not file_path:
            return {"success": False, "error": "No file path provided"}

        if not edits:
            return {"success": False, "error": "No edits provided"}

        project_dir = context.project_dir or "."
        full_path = Path(project_dir) / file_path

        # Resolve to absolute path if relative
        if not Path(file_path).is_absolute():
            file_path = str(full_path.resolve())

        log.info("Multi-edit file", {"path": file_path, "edit_count": len(edits)})

        edit_tool = get_edit_tool()
        results = []
        total_replacements = 0

        try:
            for i, edit in enumerate(edits):
                if not isinstance(edit, dict):
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "Invalid edit format",
                    })
                    continue

                old_string = edit.get("oldString", "")
                new_string = edit.get("newString", "")
                replace_all = edit.get("replaceAll", False)

                # Use the edit tool for each operation
                edit_params = {
                    "path": file_path,
                    "old_string": old_string,
                    "new_string": new_string,
                    "mode": "replace",
                    "occurrences": 0 if replace_all else 1,
                }

                result = await edit_tool.execute(edit_params, context)
                results.append({
                    "index": i,
                    "success": result.get("success", False),
                    "replacements": result.get("replacements", 0),
                })

                if result.get("success"):
                    total_replacements += result.get("replacements", 0)

            # Check if all edits succeeded
            all_success = all(r.get("success", False) for r in results)

            return {
                "success": all_success,
                "replacements": total_replacements,
                "path": file_path,
                "results": results,
            }

        except Exception as e:
            log.error("Multi-edit failed", {"error": str(e), "path": file_path})
            return {
                "success": False,
                "error": f"Multi-edit failed: {e}",
                "replacements": total_replacements,
                "results": results,
            }


# Singleton instance
_multiedit_tool = MultiEditTool()


def get_tool() -> MultiEditTool:
    """Get the multiedit tool instance."""
    return _multiedit_tool
