"""Code search tool for OpenCode."""

import json
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger
from opencode.util.http import create_http_client

log = create_logger({"service": "tool", "tool": "codesearch"})


class CodeSearchTool(Tool):
    """Tool for searching code context via Exa MCP API."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="codesearch",
            description="Search and get relevant context for APIs, Libraries, and SDKs using Exa MCP",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query to find relevant context for APIs, Libraries, and SDKs. For example, 'React useState hook examples', 'Python pandas dataframe filtering', 'Express.js middleware'",
                    required=True,
                ),
                ToolParameter(
                    name="tokensNum",
                    type="integer",
                    description="Number of tokens to return (1000-50000). Default is 5000 tokens.",
                    required=False,
                    default=5000,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute code search."""
        query = params.get("query", "")
        tokens_num = params.get("tokensNum", 5000)

        if not query:
            return {
                "output": "No query provided",
                "title": "Code search error",
            }

        log.info("Code search", {"query": query, "tokens": tokens_num})

        try:
            # Use Exa MCP API for code context
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_code_context_exa",
                    "arguments": {
                        "query": query,
                        "tokensNum": tokens_num,
                    },
                },
            }

            async with create_http_client(timeout=30.0) as client:
                response = await client.post(
                    "https://mcp.exa.ai/mcp",
                    json=request_data,
                    headers={
                        "accept": "application/json, text/event-stream",
                        "content-type": "application/json",
                    },
                )

                response.raise_for_status()
                response_text = response.text

                # Parse SSE response
                for line in response_text.split("\n"):
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        result = data.get("result", {})
                        content = result.get("content", [])

                        if content:
                            return {
                                "output": content[0].get("text", ""),
                                "title": f"Code search: {query}",
                            }

                return {
                    "output": "No code snippets or documentation found. Please try a different query.",
                    "title": f"Code search: {query}",
                }

        except Exception as e:
            log.error("Code search failed", {"error": str(e)})
            return {
                "output": f"Code search failed: {e}",
                "title": "Code search error",
            }


# Singleton instance
_codesearch_tool = CodeSearchTool()


def get_tool() -> CodeSearchTool:
    """Get the codesearch tool instance."""
    return _codesearch_tool
