"""MCP module for opencode."""

from opencode.mcp.index import (
    McpLocal,
    McpOAuth,
    McpRemote,
    McpServer,
    call,
    connect,
    disconnect,
    get_server,
    init,
    list_servers,
)

__all__ = [
    "McpLocal",
    "McpOAuth",
    "McpRemote",
    "McpServer",
    "call",
    "connect",
    "disconnect",
    "get_server",
    "init",
    "list_servers",
]
