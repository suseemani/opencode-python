"""WebFetch tool for fetching web content."""

from typing import Any

import httpx

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger
from opencode.util.http import create_http_client

log = create_logger({"service": "tool", "tool": "webfetch"})


class WebFetchTool(Tool):
    """Tool for fetching web page content."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="webfetch",
            description="Fetch and extract text content from a web page URL. Useful for reading documentation, articles, or any web content.",
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="The URL to fetch",
                    required=True,
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Request timeout in milliseconds",
                    required=False,
                    default=30000,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "status_code": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Fetch web page content."""
        url = params.get("url", "")
        timeout = params.get("timeout", 30000)

        if not url:
            return {"error": "No URL provided"}

        log.info("Fetching URL", {"url": url})

        try:
            async with create_http_client(timeout=timeout / 1000, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")

                if "text/html" in content_type:
                    # Parse HTML and extract text
                    try:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()

                        # Get text
                        text = soup.get_text(separator="\n", strip=True)

                        # Clean up whitespace
                        lines = [line.strip() for line in text.splitlines() if line.strip()]
                        text = "\n".join(lines)

                        title = soup.title.string if soup.title else url

                        return {
                            "url": url,
                            "title": title,
                            "content": text[:50000],  # Limit content
                            "status_code": response.status_code,
                        }
                    except ImportError:
                        # Fallback if BeautifulSoup not available
                        return {
                            "url": url,
                            "title": url,
                            "content": response.text[:50000],
                            "status_code": response.status_code,
                        }
                else:
                    # Return raw text for non-HTML
                    return {
                        "url": url,
                        "title": url,
                        "content": response.text[:50000],
                        "status_code": response.status_code,
                    }

        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error {e.response.status_code}",
                "status_code": e.response.status_code,
            }
        except Exception as e:
            log.error("Failed to fetch URL", {"error": str(e), "url": url})
            return {"error": f"Error fetching URL: {e}"}


# Singleton instance
_webfetch_tool = WebFetchTool()


def get_tool() -> WebFetchTool:
    """Get the webfetch tool instance."""
    return _webfetch_tool
