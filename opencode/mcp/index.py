"""MCP (Model Context Protocol) client for opencode."""

from typing import Any

from pydantic import BaseModel, Field

from opencode.util import log


logger = log.create({"service": "mcp"})


class McpLocal(BaseModel):
    """Local MCP server configuration."""
    type: str = Field(default="local", description="Type of MCP server connection")
    command: list[str] = Field(description="Command and arguments to run the MCP server")
    environment: dict[str, str] | None = Field(default=None, description="Environment variables")
    enabled: bool | None = Field(default=None, description="Enable or disable the MCP server")
    timeout: int | None = Field(default=None, description="Timeout in ms")


class McpOAuth(BaseModel):
    """OAuth configuration for MCP server."""
    client_id: str | None = Field(default=None, description="OAuth client ID")
    client_secret: str | None = Field(default=None, description="OAuth client secret")
    scope: str | None = Field(default=None, description="OAuth scopes")


class McpRemote(BaseModel):
    """Remote MCP server configuration."""
    type: str = Field(default="remote", description="Type of MCP server connection")
    url: str = Field(description="URL of the remote MCP server")
    enabled: bool | None = Field(default=None, description="Enable or disable the MCP server")
    headers: dict[str, str] | None = Field(default=None, description="Headers to send")
    oauth: McpOAuth | bool | None = Field(default=None, description="OAuth configuration")
    timeout: int | None = Field(default=None, description="Timeout in ms")


class McpServer(BaseModel):
    """MCP server."""
    name: str = Field(description="Server name")
    config: McpLocal | McpRemote = Field(description="Server configuration")
    connected: bool = Field(default=False, description="Connection status")


_servers: dict[str, McpServer] = {}


async def init() -> None:
    """Initialize MCP subsystem."""
    logger.info("initializing MCP")
    
    # Load MCP servers from config
    from opencode.config import index as config
    cfg = await config.get()
    
    for name, server_config in (cfg.mcp or {}).items():
        if isinstance(server_config, dict):
            if server_config.get("enabled") is False:
                continue
            
            server_type = server_config.get("type", "local")
            if server_type == "local":
                config_obj = McpLocal(**server_config)
            else:
                config_obj = McpRemote(**server_config)
            
            _servers[name] = McpServer(name=name, config=config_obj)


async def connect(name: str) -> bool:
    """Connect to an MCP server."""
    server = _servers.get(name)
    if not server:
        return False
    
    logger.info("connecting to MCP server", {"name": name})
    
    # Implement connection logic here
    server.connected = True
    return True


async def disconnect(name: str) -> bool:
    """Disconnect from an MCP server."""
    server = _servers.get(name)
    if not server:
        return False
    
    logger.info("disconnecting from MCP server", {"name": name})
    
    server.connected = False
    return True


async def call(name: str, method: str, params: dict[str, Any] | None = None) -> Any:
    """Call an MCP method."""
    server = _servers.get(name)
    if not server:
        raise ValueError(f"MCP server not found: {name}")
    
    if not server.connected:
        await connect(name)
    
    logger.info("calling MCP method", {"name": name, "method": method})
    
    # Implement method call logic here
    return None


def list_servers() -> list[McpServer]:
    """List all MCP servers."""
    return list(_servers.values())


def get_server(name: str) -> McpServer | None:
    """Get an MCP server by name."""
    return _servers.get(name)
