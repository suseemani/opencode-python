"""Batch tool for OpenCode - execute multiple tools in parallel."""

import asyncio
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.tool.tool import get_registry
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "batch"})


class BatchTool(Tool):
    """Tool for executing multiple tools in parallel."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="batch",
            description="Execute multiple tool calls in parallel. Use this when you need to perform several independent operations at once.",
            parameters=[
                ToolParameter(
                    name="operations",
                    type="array",
                    description="List of tool operations to execute in parallel",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "description": "Results from each operation in order",
                    },
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute batch of tools."""
        operations = params.get("operations", [])

        if not operations:
            return {"results": []}

        log.info("Batch execution", {"count": len(operations)})

        registry = get_registry()
        results = []

        # Execute all operations in parallel
        async def execute_op(index: int, op: dict) -> dict:
            tool_name = op.get("tool", "")
            tool_params = op.get("params", {})

            try:
                tool = registry.get(tool_name)
                if not tool:
                    return {
                        "index": index,
                        "tool": tool_name,
                        "error": f"Tool not found: {tool_name}",
                    }

                result = await tool.execute(tool_params, context)
                return {
                    "index": index,
                    "tool": tool_name,
                    "result": result,
                }
            except Exception as e:
                return {
                    "index": index,
                    "tool": tool_name,
                    "error": str(e),
                }

        # Run all operations concurrently
        tasks = [execute_op(i, op) for i, op in enumerate(operations)]
        results = await asyncio.gather(*tasks)

        # Sort by index
        results.sort(key=lambda x: x["index"])

        return {
            "results": results,
            "count": len(results),
            "successful": len([r for r in results if "error" not in r]),
        }


# Singleton instance
_batch_tool = BatchTool()


def get_tool() -> BatchTool:
    """Get the batch tool instance."""
    return _batch_tool
