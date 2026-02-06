"""Configuration management for opencode."""

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PermissionAction(str):
    """Permission action type."""
    ASK = "ask"
    ALLOW = "allow"
    DENY = "deny"


class PermissionRule(BaseModel):
    """Permission rule configuration."""
    permission: str = Field(description="Permission name")
    pattern: str = Field(default="*", description="Pattern to match")
    action: str = Field(default="ask", description="Action to take")


class McpLocal(BaseModel):
    """Local MCP server configuration."""
    type: str = Field(default="local", description="Type of MCP server connection")
    command: list[str] = Field(description="Command and arguments to run the MCP server")
    environment: dict[str, str] | None = Field(default=None, description="Environment variables")
    enabled: bool | None = Field(default=None, description="Enable or disable the MCP server")
    timeout: int | None = Field(default=None, description="Timeout in ms for MCP server requests")


class McpOAuth(BaseModel):
    """OAuth configuration for MCP server."""
    client_id: str | None = Field(default=None, description="OAuth client ID")
    client_secret: str | None = Field(default=None, description="OAuth client secret")
    scope: str | None = Field(default=None, description="OAuth scopes to request")


class McpRemote(BaseModel):
    """Remote MCP server configuration."""
    type: str = Field(default="remote", description="Type of MCP server connection")
    url: str = Field(description="URL of the remote MCP server")
    enabled: bool | None = Field(default=None, description="Enable or disable the MCP server")
    headers: dict[str, str] | None = Field(default=None, description="Headers to send with the request")
    oauth: McpOAuth | bool | None = Field(default=None, description="OAuth authentication configuration")
    timeout: int | None = Field(default=None, description="Timeout in ms for MCP server requests")


class Agent(BaseModel):
    """Agent configuration."""
    model: str | None = Field(default=None, description="Model to use for this agent")
    variant: str | None = Field(default=None, description="Default model variant")
    temperature: float | None = Field(default=None, description="Temperature for model")
    top_p: float | None = Field(default=None, description="Top-p for model")
    prompt: str | None = Field(default=None, description="Agent prompt")
    disable: bool | None = Field(default=None, description="Disable this agent")
    description: str | None = Field(default=None, description="Description of when to use the agent")
    mode: str | None = Field(default=None, description="Agent mode: subagent, primary, or all")
    hidden: bool | None = Field(default=None, description="Hide from autocomplete")
    options: dict[str, Any] | None = Field(default=None, description="Additional options")
    color: str | None = Field(default=None, description="Hex color code or theme color")
    steps: int | None = Field(default=None, description="Maximum number of agentic iterations")
    permission: dict[str, Any] | None = Field(default=None, description="Permission configuration")


class Command(BaseModel):
    """Command configuration."""
    template: str = Field(description="Command template")
    description: str | None = Field(default=None, description="Command description")
    agent: str | None = Field(default=None, description="Agent to use")
    model: str | None = Field(default=None, description="Model to use")
    subtask: bool | None = Field(default=None, description="Run as subtask")


class Skills(BaseModel):
    """Skills configuration."""
    paths: list[str] | None = Field(default=None, description="Additional paths to skill folders")


class Keybinds(BaseModel):
    """Keybinds configuration."""
    leader: str = Field(default="ctrl+x", description="Leader key")
    app_exit: str = Field(default="ctrl+c,ctrl+d,<leader>q", description="Exit the application")
    editor_open: str = Field(default="<leader>e", description="Open external editor")
    theme_list: str = Field(default="<leader>t", description="List available themes")
    sidebar_toggle: str = Field(default="<leader>b", description="Toggle sidebar")
    session_new: str = Field(default="<leader>n", description="Create a new session")
    session_list: str = Field(default="<leader>l", description="List all sessions")
    model_list: str = Field(default="<leader>m", description="List available models")
    agent_list: str = Field(default="<leader>a", description="List agents")
    input_submit: str = Field(default="return", description="Submit input")
    input_newline: str = Field(default="shift+return,ctrl+return,alt+return,ctrl+j", description="Insert newline")


class Server(BaseModel):
    """Server configuration."""
    port: int | None = Field(default=None, description="Port to listen on")
    hostname: str | None = Field(default=None, description="Hostname to listen on")
    mdns: bool | None = Field(default=None, description="Enable mDNS service discovery")
    mdns_domain: str | None = Field(default=None, description="Custom domain name for mDNS")
    cors: list[str] | None = Field(default=None, description="Additional domains for CORS")


class Provider(BaseModel):
    """Provider configuration."""
    whitelist: list[str] | None = Field(default=None, description="Whitelist of models")
    blacklist: list[str] | None = Field(default=None, description="Blacklist of models")
    models: dict[str, Any] | None = Field(default=None, description="Model configurations")
    options: dict[str, Any] | None = Field(default=None, description="Provider options")


class Compaction(BaseModel):
    """Compaction configuration."""
    auto: bool | None = Field(default=None, description="Enable automatic compaction")
    prune: bool | None = Field(default=None, description="Enable pruning of old tool outputs")


class Experimental(BaseModel):
    """Experimental features configuration."""
    disable_paste_summary: bool | None = Field(default=None, description="Disable paste summary")
    batch_tool: bool | None = Field(default=None, description="Enable the batch tool")
    open_telemetry: bool | None = Field(default=None, description="Enable OpenTelemetry spans")
    primary_tools: list[str] | None = Field(default=None, description="Tools only available to primary agents")
    continue_loop_on_deny: bool | None = Field(default=None, description="Continue loop when tool call is denied")
    mcp_timeout: int | None = Field(default=None, description="Timeout for MCP requests")


class Tui(BaseModel):
    """TUI configuration."""
    scroll_speed: float | None = Field(default=None, description="TUI scroll speed")
    scroll_acceleration: dict[str, Any] | None = Field(default=None, description="Scroll acceleration settings")
    diff_style: str | None = Field(default=None, description="Diff rendering style: auto or stacked")


class LspServer(BaseModel):
    """LSP server configuration."""
    command: list[str] | None = Field(default=None, description="Command to start LSP server")
    extensions: list[str] | None = Field(default=None, description="File extensions")
    disabled: bool | None = Field(default=None, description="Disable this LSP server")
    env: dict[str, str] | None = Field(default=None, description="Environment variables")
    initialization: dict[str, Any] | None = Field(default=None, description="Initialization options")


class FormatterConfig(BaseModel):
    """Formatter configuration."""
    disabled: bool | None = Field(default=None, description="Disable this formatter")
    command: list[str] | None = Field(default=None, description="Formatter command")
    environment: dict[str, str] | None = Field(default=None, description="Environment variables")
    extensions: list[str] | None = Field(default=None, description="File extensions")


class ConfigInfo(BaseModel):
    """Main configuration model."""
    schema: str | None = Field(default=None, alias="$schema", description="JSON schema reference")
    theme: str | None = Field(default=None, description="Theme name")
    keybinds: Keybinds | None = Field(default=None, description="Custom keybind configurations")
    log_level: str | None = Field(default=None, description="Log level")
    tui: Tui | None = Field(default=None, description="TUI specific settings")
    server: Server | None = Field(default=None, description="Server configuration")
    command: dict[str, Command] | None = Field(default=None, description="Command configurations")
    skills: Skills | None = Field(default=None, description="Additional skill folder paths")
    watcher: dict[str, Any] | None = Field(default=None, description="Watcher configuration")
    plugin: list[str] | None = Field(default=None, description="Plugin list")
    snapshot: bool | None = Field(default=None, description="Enable snapshots")
    share: str | None = Field(default=None, description="Sharing behavior: manual, auto, or disabled")
    autoupdate: bool | str | None = Field(default=None, description="Auto-update setting")
    disabled_providers: list[str] | None = Field(default=None, description="Disabled providers")
    enabled_providers: list[str] | None = Field(default=None, description="Only these providers will be enabled")
    model: str | None = Field(default=None, description="Default model in format provider/model")
    small_model: str | None = Field(default=None, description="Small model for tasks like title generation")
    default_agent: str | None = Field(default=None, description="Default agent to use")
    username: str | None = Field(default=None, description="Custom username to display")
    mode: dict[str, Agent] | None = Field(default=None, description="Deprecated: use agent field")
    agent: dict[str, Agent] | None = Field(default=None, description="Agent configurations")
    provider: dict[str, Provider] | None = Field(default=None, description="Custom provider configurations")
    mcp: dict[str, McpLocal | McpRemote | dict[str, Any]] | None = Field(default=None, description="MCP server configurations")
    formatter: dict[str, FormatterConfig] | bool | None = Field(default=None, description="Formatter configurations")
    lsp: dict[str, LspServer] | bool | None = Field(default=None, description="LSP server configurations")
    instructions: list[str] | None = Field(default=None, description="Additional instruction files")
    layout: str | None = Field(default=None, description="Layout configuration")
    permission: dict[str, Any] | None = Field(default=None, description="Permission configuration")
    tools: dict[str, bool] | None = Field(default=None, description="Deprecated: use permission field")
    enterprise: dict[str, str] | None = Field(default=None, description="Enterprise configuration")
    compaction: Compaction | None = Field(default=None, description="Compaction settings")
    experimental: Experimental | None = Field(default=None, description="Experimental features")

    class Config:
        populate_by_name = True


_config: ConfigInfo | None = None


async def get() -> ConfigInfo:
    """Get the current configuration."""
    global _config
    if _config is None:
        _config = await load()
    return _config


async def load() -> ConfigInfo:
    """Load configuration from various sources."""
    from opencode.global_path import get_paths
    from opencode.util import filesystem
    import json
    
    paths = get_paths()
    result: dict[str, Any] = {}
    
    # Load global config
    for filename in ["config.json", "opencode.json", "opencode.jsonc"]:
        config_path = paths.config / filename
        if await filesystem.exists(config_path):
            try:
                content = await filesystem.read_file(config_path)
                # Remove comments for jsonc
                if filename.endswith(".jsonc"):
                    lines = content.split("\n")
                    content = "\n".join(line for line in lines if not line.strip().startswith("//"))
                data = json.loads(content)
                result.update(data)
            except Exception:
                pass
    
    # Load project config
    cwd = Path.cwd()
    for filename in ["opencode.jsonc", "opencode.json"]:
        config_path = cwd / filename
        if await filesystem.exists(config_path):
            try:
                content = await filesystem.read_file(config_path)
                if filename.endswith(".jsonc"):
                    lines = content.split("\n")
                    content = "\n".join(line for line in lines if not line.strip().startswith("//"))
                data = json.loads(content)
                result.update(data)
            except Exception:
                pass
            break
    
    # Set defaults
    if not result.get("username"):
        result["username"] = os.getlogin() if hasattr(os, "getlogin") else "user"
    
    return ConfigInfo(**result)


async def reload() -> ConfigInfo:
    """Reload configuration from disk."""
    global _config
    _config = None
    return await get()
