"""OpenCode CLI main entry point."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import typer

from opencode.agent import get_manager as get_agent_manager
from opencode.provider import get_manager as get_provider_manager
from opencode.server import Server
from opencode.session import get_manager as get_session_manager
from opencode.tool import register_all_tools, get_registry
from opencode.tool import ToolContext
from opencode.util import Default as DefaultLogger
from opencode.util import LogLevel, LogOptions, init as init_log

app = typer.Typer(
    name="opencode",
    help="AI-powered development tool",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    print_logs: bool = typer.Option(False, "--print-logs", help="Print logs to stderr"),
    log_level: Optional[str] = typer.Option(None, "--log-level", help="Log level"),
) -> None:
    """OpenCode - AI-powered development tool."""
    async def _init() -> None:
        level = LogLevel.INFO
        if log_level:
            level = LogLevel(log_level.upper())
        await init_log(
            LogOptions(
                print_only=print_logs,
                dev=False,
                level=level,
            )
        )

    asyncio.run(_init())

    import os
    os.environ["AGENT"] = "1"
    os.environ["OPENCODE"] = "1"

    DefaultLogger.info(
        "opencode",
        {"version": "0.1.0", "args": sys.argv[1:]},
    )


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
) -> None:
    """Start the OpenCode server."""
    typer.echo(f"Starting OpenCode server on {host}:{port}")
    server = Server(host=host, port=port)
    server.run()


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't open browser automatically"),
) -> None:
    """Start OpenCode server and open web interface."""
    import os
    import socket
    import webbrowser
    from pathlib import Path
    
    # Check for password warning
    if not os.environ.get("OPENCODE_SERVER_PASSWORD"):
        typer.echo(typer.style("!  ", fg=typer.colors.YELLOW, bold=True) + 
                   "OPENCODE_SERVER_PASSWORD is not set; server is unsecured.")
    
    # Start server
    server = Server(host=host, port=port)
    
    # Display banner
    typer.echo("")
    typer.echo("   ____                      __         ")
    typer.echo("  / __ \\____ ___  ________  / /__  _____")
    typer.echo(" / / / / __ `/ / / / ___/ / / / _ \\/ ___/")
    typer.echo("/ /_/ / /_/ / /_/ (__  ) /_/ /  __/ /    ")
    typer.echo("\\____/\\__, /\\__, /____/\\____/\\___/_/     ")
    typer.echo("      /____//____/                       ")
    typer.echo("")
    
    if host == "0.0.0.0":
        # Show localhost for local access
        localhost_url = f"http://localhost:{port}"
        typer.echo(f"  Local access:       {localhost_url}")
        
        # Show network IPs for remote access
        try:
            # Get network interfaces
            import psutil
            network_ips = []
            for iface_name, iface_addrs in psutil.net_if_addrs().items():
                for addr in iface_addrs:
                    # Skip internal and non-IPv4 addresses
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        # Skip Docker bridge networks (typically 172.x.x.x)
                        if not addr.address.startswith("172."):
                            network_ips.append(addr.address)
            
            for ip in network_ips:
                typer.echo(f"  Network access:     http://{ip}:{port}")
        except ImportError:
            pass
        
        # Open localhost in browser
        if not no_open:
            try:
                webbrowser.open(localhost_url)
            except Exception:
                pass
    else:
        display_url = f"http://{host}:{port}"
        typer.echo(f"  Web interface:      {display_url}")
        if not no_open:
            try:
                webbrowser.open(display_url)
            except Exception:
                pass
    
    typer.echo("")
    typer.echo("Press Ctrl+C to stop the server")
    
    # Run server
    try:
        server.run()
    except KeyboardInterrupt:
        typer.echo("\nStopping server...")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("OpenCode v0.1.0 (Python)")
    typer.echo("AI-powered development tool")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to send to the AI"),
    agent: str = typer.Option("general", "--agent", "-a", help="Agent to use"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use (e.g., opencode/big-pickle)"),
    continue_last: bool = typer.Option(False, "--continue", "-c", help="Continue the last session"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID to continue"),
    files: Optional[List[str]] = typer.Option(None, "--file", "-f", help="File(s) to attach to the prompt"),
) -> None:
    """Run AI with a prompt using the big-pickle model (no API key required)."""
    
    async def run_session():
        from opencode.agent import get_manager as get_agent_manager
        from opencode.provider import get_manager as get_provider_manager, CompletionRequest, Message
        from opencode.session import get_manager as get_session_manager, MessageRole, MessagePart
        
        # Get agent
        agent_manager = get_agent_manager()
        agent_obj = agent_manager.get(agent)
        if not agent_obj:
            typer.echo(f"Error: Agent '{agent}' not found", err=True)
            sys.exit(1)
        
        # Get provider and model
        provider_manager = get_provider_manager()
        
        # Parse model if provided
        target_model = "big-pickle"
        provider_id = "opencode"
        if model:
            if "/" in model:
                provider_id, target_model = model.split("/", 1)
            else:
                target_model = model
        
        provider_obj = provider_manager.get(provider_id)
        if not provider_obj:
            typer.echo(f"Error: Provider '{provider_id}' not found", err=True)
            sys.exit(1)
        
        # Get session manager
        session_manager = get_session_manager()
        
        # Determine session to use
        session = None
        if continue_last:
            # Get the most recent session
            sessions = await session_manager.list_sessions("cli")
            if sessions:
                session = sessions[0]
                typer.echo(f"Continuing session: {session.id}")
            else:
                typer.echo("No previous session found, creating new session")
        elif session_id:
            # Try to get specific session
            try:
                sessions = await session_manager.list_sessions("cli")
                session = next((s for s in sessions if s.id == session_id), None)
                if session:
                    typer.echo(f"Continuing session: {session.id}")
                else:
                    typer.echo(f"Session '{session_id}' not found, creating new session")
            except Exception:
                typer.echo(f"Session '{session_id}' not found, creating new session")
        
        # Create new session if needed
        if not session:
            session = await session_manager.create(
                project_id="cli",
                title=f"CLI: {prompt[:50]}...",
            )
        
        # Read and attach files if provided
        attached_files = []
        if files:
            for file_path in files:
                path = Path(file_path)
                if path.exists():
                    try:
                        content = path.read_text(encoding="utf-8")
                        attached_files.append({"path": str(path), "content": content})
                    except Exception as e:
                        typer.echo(f"Warning: Could not read file '{file_path}': {e}", err=True)
                else:
                    typer.echo(f"Warning: File not found: '{file_path}'", err=True)
        
        # Build message content
        message_content = prompt
        if attached_files:
            message_content += "\n\nAttached files:\n"
            for file_info in attached_files:
                message_content += f"\n--- {file_info['path']} ---\n{file_info['content']}\n"
        
        # Add user message to session
        await session_manager.add_message(
            session.id,
            MessageRole.USER,
            [MessagePart(type="text", content=message_content)]
        )
        
        typer.echo(f"Session: {session.id}")
        typer.echo(f"Agent: {agent_obj.name}")
        typer.echo(f"Model: {target_model}")
        typer.echo(f"Provider: {provider_obj.type}")
        typer.echo("")
        typer.echo("User: " + prompt)
        if attached_files:
            typer.echo(f"Attached {len(attached_files)} file(s)")
        typer.echo("")
        typer.echo("Assistant: ", nl=False)
        
        # Prepare messages for the provider
        system_prompt = agent_obj.prompt or f"You are {agent_obj.name}. {agent_obj.description}"
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=message_content)
        ]
        
        # Create completion request
        request = CompletionRequest(
            model=target_model,
            messages=messages,
            temperature=agent_obj.temperature or 0.7,
            stream=True
        )
        
        # Stream the response
        full_response = ""
        chunk_count = 0
        try:
            async for chunk in provider_obj.complete(request):
                chunk_count += 1
                if chunk.content:
                    # Clean content for Windows console compatibility
                    import sys
                    content = chunk.content
                    if sys.platform == "win32":
                        # Remove emojis and problematic characters for Windows console
                        import re
                        # Remove emoji characters
                        content = re.sub(r'[^\x00-\x7F]+', '', content)
                    
                    typer.echo(content, nl=False)
                    full_response += content
                if chunk.finish_reason:
                    break
            
            if chunk_count == 0:
                typer.echo("(No response received from model)", err=True)
            elif not full_response.strip():
                typer.echo("(Empty response from model)", err=True)
            else:
                typer.echo("")  # New line at end
        except Exception as e:
            typer.echo(f"\nError calling model: {e}", err=True)
            sys.exit(1)
        
        # Add assistant message to session
        await session_manager.add_message(
            session.id,
            MessageRole.ASSISTANT,
            [MessagePart(type="text", content=full_response)]
        )
        
        typer.echo("")
        typer.echo(f"Session saved: {session.id}")
        
    asyncio.run(run_session())


# Session commands
session_app = typer.Typer(help="Manage sessions")

@session_app.command("list")
def session_list(
    max_count: int = typer.Option(10, "--max-count", "-n", help="Maximum number of sessions to show"),
) -> None:
    """List all sessions."""
    async def list_sessions():
        manager = get_session_manager()
        sessions = await manager.list_sessions("cli")
        
        if not sessions:
            typer.echo("No sessions found")
            return
            
        typer.echo(f"{'ID':<30} {'Status':<12} {'Title'}")
        typer.echo("-" * 80)
        for session in sessions[:max_count]:
            title = session.summary.title or "Untitled"
            if len(title) > 40:
                title = title[:37] + "..."
            typer.echo(f"{session.id:<30} {session.status.value:<12} {title}")
    
    asyncio.run(list_sessions())

@session_app.command("create")
def session_create(
    title: str = typer.Argument(..., help="Session title"),
) -> None:
    """Create a new session."""
    async def create():
        manager = get_session_manager()
        session = await manager.create(project_id="cli", title=title)
        typer.echo(f"Created session: {session.id}")
    
    asyncio.run(create())

@session_app.command("delete")
def session_delete(
    session_id: str = typer.Argument(..., help="Session ID to delete"),
) -> None:
    """Delete a session."""
    async def delete():
        manager = get_session_manager()
        success = await manager.delete(session_id, "cli")
        if success:
            typer.echo(f"Deleted session: {session_id}")
        else:
            typer.echo(f"Session not found: {session_id}", err=True)
            sys.exit(1)
    
    asyncio.run(delete())

app.add_typer(session_app, name="session")


@app.command()
def models(
    provider: Optional[str] = typer.Argument(None, help="Filter by provider ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
) -> None:
    """List available AI models."""
    from opencode.provider import get_manager
    
    manager = get_manager()
    all_models = manager.list_models()
    
    if provider:
        all_models = [m for m in all_models if m.provider.value == provider]
    
    if not all_models:
        typer.echo("No models found")
        return
    
    if verbose:
        typer.echo(f"{'Provider':<15} {'Model ID':<30} {'Name':<25} {'Context'}")
        typer.echo("-" * 100)
        for model in all_models:
            typer.echo(f"{model.provider:<15} {model.id:<30} {model.name:<25} {model.max_tokens}")
    else:
        typer.echo(f"{'Provider/Model':<50} {'Name'}")
        typer.echo("-" * 80)
        for model in all_models:
            typer.echo(f"{model.provider}/{model.id:<50} {model.name}")


# Agent commands
agent_app = typer.Typer(help="Manage agents")


@agent_app.command("list")
def agent_list() -> None:
    """List available agents."""
    from opencode.agent import get_manager
    
    manager = get_manager()
    agents = manager.list_agents()
    
    typer.echo(f"{'Name':<15} {'Mode':<12} {'Type':<20} {'Description'}")
    typer.echo("-" * 100)
    for agent in agents:
        desc = agent.description[:50] if len(agent.description) > 50 else agent.description
        typer.echo(f"{agent.name:<15} {agent.mode.value:<12} {agent.mode.value:<20} {desc}")


@agent_app.command("info")
def agent_info(
    agent_id: str = typer.Argument(..., help="Agent ID to show info for"),
) -> None:
    """Show detailed information about an agent."""
    from opencode.agent import get_manager
    
    manager = get_manager()
    agent = manager.get(agent_id)
    
    if not agent:
        typer.echo(f"Agent not found: {agent_id}", err=True)
        sys.exit(1)
    
    typer.echo(f"Agent: {agent.name}")
    typer.echo(f"Mode: {agent.mode.value}")
    typer.echo(f"Description: {agent.description}")
    model_str = f"{agent.model.get('modelID', 'default')}" if agent.model else "default"
    typer.echo(f"Model: {model_str}")
    typer.echo(f"Temperature: {agent.temperature or 0.7}")
    typer.echo(f"Native: {agent.native}")
    typer.echo(f"Hidden: {agent.hidden}")
    typer.echo(f"Permissions: {len(agent.permissions)} rules configured")


@agent_app.command("create")
def agent_create(
    name: str = typer.Argument(..., help="Agent name/identifier"),
    description: str = typer.Option(None, "--description", "-d", help="Agent description (required unless using --ai)"),
    mode: str = typer.Option("primary", "--mode", "-m", help="Agent mode: primary, subagent, or all"),
    tools: Optional[str] = typer.Option(None, "--tools", "-t", help="Comma-separated list of tools to enable (default: all)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model to use (provider/model format)"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="System prompt for the agent"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI to generate agent configuration"),
) -> None:
    """Create a new custom agent. With --ai, generates agent using AI based on description."""
    from opencode.agent import (
        get_manager, AgentInfo, AgentMode, PermissionAction, PermissionRule,
        generate_agent_sync, GeneratedAgent
    )
    
    manager = get_manager()
    
    # Use AI generation if requested
    if use_ai:
        if not description:
            typer.echo("Error: --description is required when using --ai", err=True)
            sys.exit(1)
        
        typer.echo("Generating agent configuration using AI...")
        try:
            # Parse model config for generation
            model_config = None
            if model:
                if "/" in model:
                    provider_id, model_id = model.split("/", 1)
                    model_config = {"providerID": provider_id, "modelID": model_id}
                else:
                    model_config = {"providerID": "opencode", "modelID": model}
            
            generated = generate_agent_sync(description, model_config)
            
            typer.echo(f"Generated agent: {generated.identifier}")
            typer.echo(f"When to use: {generated.whenToUse}")
            
            # Create agent from generated configuration
            agent = AgentInfo(
                name=name,
                description=generated.whenToUse,
                mode=AgentMode(mode.lower()) if mode else AgentMode.PRIMARY,
                native=False,
                permissions=[PermissionRule(permission="*", pattern="*", action=PermissionAction.ALLOW)],
                prompt=generated.systemPrompt,
                model=model_config,
            )
            
            manager.register(agent)
            typer.echo(f"\nCreated agent: {name}")
            typer.echo(f"Mode: {mode}")
            return
            
        except Exception as e:
            typer.echo(f"Error generating agent: {e}", err=True)
            sys.exit(1)
    
    # Manual agent creation (existing logic)
    if not description:
        typer.echo("Error: --description is required (or use --ai to generate)", err=True)
        sys.exit(1)
    
    # Validate mode
    try:
        agent_mode = AgentMode(mode.lower())
    except ValueError:
        typer.echo(f"Invalid mode: {mode}. Must be one of: primary, subagent, all", err=True)
        sys.exit(1)
    
    # Parse tools
    enabled_tools = None
    if tools:
        enabled_tools = [t.strip() for t in tools.split(",")]
    
    # Build permissions
    permissions = []
    if enabled_tools:
        # Deny all tools by default
        permissions.append(PermissionRule(permission="*", pattern="*", action=PermissionAction.DENY))
        # Allow specified tools
        for tool in enabled_tools:
            permissions.append(PermissionRule(permission=tool, pattern="*", action=PermissionAction.ALLOW))
    else:
        # Allow all tools
        permissions.append(PermissionRule(permission="*", pattern="*", action=PermissionAction.ALLOW))
    
    # Parse model if provided
    model_config = None
    if model:
        if "/" in model:
            provider_id, model_id = model.split("/", 1)
            model_config = {"providerID": provider_id, "modelID": model_id}
        else:
            model_config = {"providerID": "opencode", "modelID": model}
    
    # Create agent
    agent = AgentInfo(
        name=name,
        description=description,
        mode=agent_mode,
        native=False,
        permissions=permissions,
        model=model_config,
        prompt=prompt,
    )
    
    manager.register(agent)
    typer.echo(f"Created agent: {name}")
    typer.echo(f"Mode: {mode}")
    typer.echo(f"Description: {description}")
    if enabled_tools:
        typer.echo(f"Tools: {', '.join(enabled_tools)}")
    else:
        typer.echo("Tools: all enabled")


app.add_typer(agent_app, name="agent")


@app.command()
def shell(
    command: str = typer.Argument(..., help="Shell command to execute"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Execute a shell command using OpenCode tools."""
    async def run_shell():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=cwd or ".")
        registry = get_registry()
        result = await registry.execute("bash", {"command": command}, context)
        typer.echo(result.get("stdout", ""))
        if result.get("stderr"):
            typer.echo(result["stderr"], err=True)
        return result.get("exit_code", 0)
    
    exit_code = asyncio.run(run_shell())
    sys.exit(exit_code)


@app.command()
def read(
    path: str = typer.Argument(..., help="File path to read"),
    offset: int = typer.Option(0, "--offset", "-o", help="Line offset"),
    limit: int = typer.Option(200, "--limit", "-l", help="Max lines to read"),
) -> None:
    """Read a file using OpenCode tools."""
    async def run_read():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("read", {"path": path, "offset": offset, "limit": limit}, context)
        if "error" in result:
            typer.echo(f"Error: {result['error']}", err=True)
            sys.exit(1)
        typer.echo(result.get("content", ""))
    
    asyncio.run(run_read())


@app.command()
def write(
    path: str = typer.Argument(..., help="File path to write"),
    content: str = typer.Argument(..., help="Content to write"),
) -> None:
    """Write content to a file using OpenCode tools."""
    async def run_write():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("write", {"path": path, "content": content}, context)
        if result.get("success"):
            typer.echo(f"Written: {path}")
        else:
            typer.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)
    
    asyncio.run(run_write())


@app.command()
def edit(
    path: str = typer.Argument(..., help="File path to edit"),
    old_string: str = typer.Option(..., "--old", help="Text to find"),
    new_string: str = typer.Option(..., "--new", help="Text to replace with"),
) -> None:
    """Edit a file by replacing text using OpenCode tools."""
    async def run_edit():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("edit", {"path": path, "old_string": old_string, "new_string": new_string}, context)
        if result.get("success"):
            typer.echo(f"Edited: {path} ({result.get('replacements', 0)} replacements)")
        else:
            typer.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)
    
    asyncio.run(run_edit())


@app.command()
def grep(
    pattern: str = typer.Argument(..., help="Search pattern"),
    path: str = typer.Option(".", "--path", "-p", help="Path to search in"),
    file_pattern: Optional[str] = typer.Option(None, "--files", "-f", help="File pattern (e.g., '*.py')"),
) -> None:
    """Search for patterns in files using OpenCode tools."""
    async def run_grep():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("grep", {"pattern": pattern, "path": path, "file_pattern": file_pattern}, context)
        matches = result.get("matches", [])
        if not matches:
            typer.echo("No matches found")
            return
        for match in matches:
            typer.echo(f"{match['path']}:{match['line']}: {match['content']}")
    
    asyncio.run(run_grep())


@app.command()
def glob(
    pattern: str = typer.Argument(..., help="Glob pattern (e.g., '*.py')"),
    path: str = typer.Option(".", "--path", "-p", help="Path to search in"),
) -> None:
    """Find files matching a glob pattern using OpenCode tools."""
    async def run_glob():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("glob", {"pattern": pattern, "path": path}, context)
        files = result.get("files", [])
        if not files:
            typer.echo("No files found")
            return
        for file in files:
            typer.echo(file)
    
    asyncio.run(run_glob())


@app.command(name="list")
def list_dir(
    path: str = typer.Argument(".", help="Directory path"),
) -> None:
    """List directory contents."""
    async def run_ls():
        register_all_tools()
        context = ToolContext(session_id="cli", project_dir=".")
        registry = get_registry()
        result = await registry.execute("ls", {"path": path}, context)
        if result.get("error"):
            typer.echo(f"Error: {result['error']}", err=True)
            sys.exit(1)
        for entry in result.get("entries", []):
            icon = "📁" if entry["type"] == "directory" else "📄"
            typer.echo(f"{icon} {entry['name']}")
    
    asyncio.run(run_ls())


@app.command()
def upgrade() -> None:
    """Upgrade OpenCode to the latest version."""
    typer.echo("Checking for updates...")
    typer.echo("OpenCode Python is at version 0.1.0")
    typer.echo("To upgrade, run: pip install -e . --upgrade")


@app.command()
def config() -> None:
    """Show configuration information."""
    from opencode.global_path import get_paths
    
    paths = get_paths()
    typer.echo("OpenCode Configuration")
    typer.echo("=" * 50)
    typer.echo(f"Data directory:    {paths.data}")
    typer.echo(f"Config directory:  {paths.config}")
    typer.echo(f"Cache directory:   {paths.cache}")
    typer.echo(f"State directory:   {paths.state}")
    typer.echo(f"Log directory:     {paths.log}")


# Auth commands
auth_app = typer.Typer(help="Manage authentication credentials")


@auth_app.command("set")
def auth_set(
    provider: str = typer.Argument(..., help="Provider ID (e.g., openai, anthropic)"),
    api_key: str = typer.Argument(..., help="API key"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Custom base URL (optional)"),
    organization: Optional[str] = typer.Option(None, "--org", help="Organization ID (optional)"),
) -> None:
    """Set API credentials for a provider."""
    from opencode.cli.auth import get_manager, SUPPORTED_PROVIDERS
    
    manager = get_manager()
    
    # Validate provider
    provider_names = {p[0]: p[1] for p in SUPPORTED_PROVIDERS}
    if provider not in provider_names:
        typer.echo(f"Warning: '{provider}' is not a standard provider", err=True)
        typer.echo("Supported providers:", err=True)
        for pid, pname, url in SUPPORTED_PROVIDERS:
            typer.echo(f"  - {pid}: {pname}", err=True)
    
    manager.set_credentials(provider, api_key, base_url, organization)
    typer.echo(f"Credentials set for provider: {provider}")


@auth_app.command("get")
def auth_get(
    provider: str = typer.Argument(..., help="Provider ID"),
) -> None:
    """Show credentials for a provider (API key masked)."""
    from opencode.cli.auth import get_manager
    
    manager = get_manager()
    creds = manager.get_credentials(provider)
    
    if not creds:
        typer.echo(f"No credentials found for provider: {provider}")
        return
    
    typer.echo(f"Provider: {creds.provider}")
    typer.echo(f"API Key: {creds.api_key[:8]}...{creds.api_key[-4:]}")
    if creds.base_url:
        typer.echo(f"Base URL: {creds.base_url}")
    if creds.organization:
        typer.echo(f"Organization: {creds.organization}")


@auth_app.command("list")
def auth_list() -> None:
    """List all providers with stored credentials."""
    from opencode.cli.auth import get_manager
    
    manager = get_manager()
    providers = manager.list_providers()
    
    if not providers:
        typer.echo("No credentials stored")
        return
    
    typer.echo("Configured providers:")
    for provider in providers:
        creds = manager.get_credentials(provider)
        masked_key = f"{creds.api_key[:8]}...{creds.api_key[-4:]}" if len(creds.api_key) > 12 else "***"
        typer.echo(f"  - {provider}: {masked_key}")


@auth_app.command("remove")
def auth_remove(
    provider: str = typer.Argument(..., help="Provider ID"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """Remove credentials for a provider."""
    from opencode.cli.auth import get_manager
    
    manager = get_manager()
    
    if not force:
        confirm = typer.confirm(f"Remove credentials for '{provider}'?")
        if not confirm:
            typer.echo("Cancelled")
            return
    
    if manager.remove_credentials(provider):
        typer.echo(f"Credentials removed for provider: {provider}")
    else:
        typer.echo(f"No credentials found for provider: {provider}")


app.add_typer(auth_app, name="auth")


def cli_run() -> None:
    """Run the CLI application."""
    try:
        app()
    except Exception as e:
        DefaultLogger.error("fatal", {"error": str(e), "type": type(e).__name__})
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli_run()
