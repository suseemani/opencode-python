"""LSP tool for Language Server Protocol operations."""

from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "lsp"})

# Valid LSP operations
LSP_OPERATIONS = [
    "goToDefinition",
    "findReferences",
    "hover",
    "documentSymbol",
    "workspaceSymbol",
    "goToImplementation",
    "prepareCallHierarchy",
    "incomingCalls",
    "outgoingCalls",
]


class LspTool(Tool):
    """Tool for Language Server Protocol operations."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="lsp",
            description="Perform Language Server Protocol (LSP) operations like go-to-definition, find-references, hover, etc. Requires an LSP server to be running for the file type.",
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description=f"The LSP operation to perform. Valid operations: {', '.join(LSP_OPERATIONS)}",
                    required=True,
                ),
                ToolParameter(
                    name="filePath",
                    type="string",
                    description="The absolute or relative path to the file",
                    required=True,
                ),
                ToolParameter(
                    name="line",
                    type="integer",
                    description="The line number (1-based, as shown in editors)",
                    required=True,
                ),
                ToolParameter(
                    name="character",
                    type="integer",
                    description="The character offset (1-based, as shown in editors)",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                    "result": {"type": "array"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute an LSP operation."""
        operation = params.get("operation", "")
        file_path = params.get("filePath", "")
        line = params.get("line", 1)
        character = params.get("character", 1)

        if not operation:
            return {
                "output": "No operation specified",
                "title": "LSP error",
                "result": [],
            }

        if operation not in LSP_OPERATIONS:
            return {
                "output": f"Invalid operation: {operation}. Valid operations: {', '.join(LSP_OPERATIONS)}",
                "title": "LSP error",
                "result": [],
            }

        if not file_path:
            return {
                "output": "No file path specified",
                "title": "LSP error",
                "result": [],
            }

        # Resolve file path
        project_dir = context.project_dir or "."
        if not Path(file_path).is_absolute():
            file_path = str(Path(project_dir) / file_path)

        # Check if file exists
        if not Path(file_path).exists():
            return {
                "output": f"File not found: {file_path}",
                "title": "LSP error",
                "result": [],
            }

        log.info("LSP operation", {
            "operation": operation,
            "file": file_path,
            "line": line,
            "character": character,
        })

        # In a full implementation, this would:
        # 1. Connect to an LSP server for the file type
        # 2. Send the appropriate LSP request
        # 3. Return the results

        # For now, return a placeholder response
        return {
            "output": f"LSP operation '{operation}' at {file_path}:{line}:{character}\n\nNote: Full LSP integration requires an LSP server to be running for this file type.",
            "title": f"{operation} {Path(file_path).name}:{line}:{character}",
            "result": [],
        }


# Singleton instance
_lsp_tool = LspTool()


def get_tool() -> LspTool:
    """Get the lsp tool instance."""
    return _lsp_tool
