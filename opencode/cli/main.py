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
def version() -> None:
    """Show version information."""
    typer.echo("OpenCode v0.1.0 (Python)")
    typer.echo("AI-powered development tool")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to send to the AI"),
    agent: str = typer.Option("general", "--agent", "-a", help="Agent to use"),
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
        
        # Get provider
        provider_manager = get_provider_manager()
        provider_obj = provider_manager.get("opencode")
        target_model = "big-pickle"
        
        # Create session
        session_manager = get_session_manager()
        session = await session_manager.create(
            project_id="cli",
            title=f"CLI: {prompt[:50]}...",
        )
        
        # Add user message to session
        await session_manager.add_message(
            session.id,
            MessageRole.USER,
            [MessagePart(type="text", content=prompt)]
        )
        
        typer.echo(f"Session: {session.id}")
        typer.echo(f"Agent: {agent_obj.name}")
        typer.echo(f"Model: {target_model}")
        typer.echo(f"Provider: {provider_obj.type}")
        typer.echo("")
        typer.echo("User: " + prompt)
        typer.echo("")
        typer.echo("Assistant: ", nl=False)
        
        # Prepare messages for the provider
        messages = [
            Message(role="system", content=agent_obj.system_prompt),
            Message(role="user", content=prompt)
        ]
        
        # Create completion request
        request = CompletionRequest(
            model=target_model,
            messages=messages,
            temperature=agent_obj.temperature,
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


@app.command()
def agents() -> None:
    """List available agents."""
    from opencode.agent import get_manager
    
    manager = get_manager()
    agents = manager.list_agents()
    
    typer.echo(f"{'ID':<15} {'Type':<12} {'Name':<20} {'Description'}")
    typer.echo("-" * 100)
    for agent in agents:
        desc = agent.description[:50] if len(agent.description) > 50 else agent.description
        typer.echo(f"{agent.id:<15} {agent.type.value:<12} {agent.name:<20} {desc}")


@app.command()
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
    typer.echo(f"ID: {agent.id}")
    typer.echo(f"Type: {agent.type.value}")
    typer.echo(f"Description: {agent.description}")
    typer.echo(f"Model: {agent.model or 'default'}")
    typer.echo(f"Temperature: {agent.temperature}")
    typer.echo(f"Permissions: {', '.join(p.value for p in agent.permissions)}")


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
