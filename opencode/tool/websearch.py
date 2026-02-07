"""Web search tool for OpenCode."""

import json
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger
from opencode.util.http import create_http_client

log = create_logger({"service": "tool", "tool": "websearch"})


class WebSearchTool(Tool):
    """Tool for searching the web."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="websearch",
            description="Search the web for information using Exa MCP API",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Web search query",
                    required=True,
                ),
                ToolParameter(
                    name="num_results",
                    type="integer",
                    description="Number of search results to return (default: 8)",
                    required=False,
                    default=8,
                ),
                ToolParameter(
                    name="type",
                    type="string",
                    description="Search type: 'auto', 'fast', or 'deep' (default: 'auto')",
                    required=False,
                    default="auto",
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute web search."""
        query = params.get("query", "")
        num_results = params.get("num_results", 8)
        search_type = params.get("type", "auto")

        if not query:
            return {"error": "No query provided"}

        log.info("Web search", {"query": query})

        try:
            # Use Exa MCP API (similar to TypeScript implementation)
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "web_search_exa",
                    "arguments": {
                        "query": query,
                        "type": search_type,
                        "numResults": num_results,
                        "livecrawl": "fallback",
                    },
                },
            }

            async with create_http_client(timeout=30.0) as client:
                response = await client.post(
                    "https://mcp.exa.ai/mcp",
                    json=request_data,
                    headers={
                        "accept": "application/json",
                        "content-type": "application/json",
                    },
                )

                response.raise_for_status()
                data = response.json()

                # Parse results
                content = data.get("result", {}).get("content", [])
                results = []

                for item in content:
                    if item.get("type") == "text":
                        try:
                            search_results = json.loads(item.get("text", "[]"))
                            results.extend(search_results)
                        except json.JSONDecodeError:
                            pass

                return {
                    "results": results,
                    "total": len(results),
                }

        except Exception as e:
            log.error("Web search failed", {"error": str(e)})
            return {
                "error": f"Search failed: {e}",
                "results": [],
            }


# Singleton instance
_websearch_tool = WebSearchTool()


def get_tool() -> WebSearchTool:
    """Get the websearch tool instance."""
    return _websearch_tool
