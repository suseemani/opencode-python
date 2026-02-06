"""Command system implementation."""

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "command"})


class CommandArgument(BaseModel):
    """Command argument definition."""
    
    name: str = Field(description="Argument name")
    description: str = Field(description="Argument description")
    required: bool = Field(default=True, description="Whether argument is required")
    default: Any | None = Field(default=None, description="Default value")
    type: str = Field(default="string", description="Argument type")


class CommandInfo(BaseModel):
    """Command information."""
    
    name: str = Field(description="Command name")
    description: str = Field(description="Command description")
    template: str = Field(description="Command template with placeholders")
    arguments: list[CommandArgument] = Field(default_factory=list, description="Command arguments")
    cwd: str | None = Field(default=None, description="Working directory")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class CommandRegistry:
    """Registry for commands."""
    
    def __init__(self) -> None:
        self._commands: dict[str, CommandInfo] = {}
    
    def register(self, command: CommandInfo) -> None:
        """Register a command."""
        self._commands[command.name] = command
        log.info("Registered command", {"name": command.name})
    
    def get(self, name: str) -> CommandInfo | None:
        """Get a command by name."""
        return self._commands.get(name)
    
    def list_commands(self) -> list[CommandInfo]:
        """List all registered commands."""
        return list(self._commands.values())
    
    def unregister(self, name: str) -> bool:
        """Unregister a command."""
        if name in self._commands:
            del self._commands[name]
            return True
        return False


class CommandExecutor:
    """Executes commands with template substitution."""
    
    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry
    
    def _substitute_template(self, template: str, args: dict[str, Any]) -> str:
        """Substitute arguments into template."""
        result = template
        for key, value in args.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    async def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a command with arguments."""
        command = self.registry.get(name)
        if not command:
            raise ValueError(f"Command not found: {name}")
        
        # Validate required arguments
        for arg in command.arguments:
            if arg.required and arg.name not in kwargs:
                raise ValueError(f"Missing required argument: {arg.name}")
        
        # Substitute template
        cmd_string = self._substitute_template(command.template, kwargs)
        
        log.info("Executing command", {"name": name, "command": cmd_string})
        
        import asyncio
        
        # Execute command
        proc = await asyncio.create_subprocess_shell(
            cmd_string,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=command.cwd,
            env={**dict(), **command.env},
        )
        
        stdout, stderr = await proc.communicate()
        
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "exit_code": proc.returncode,
        }
    
    async def execute_from_file(self, file_path: Path, **kwargs: Any) -> dict[str, Any]:
        """Execute a command defined in a file."""
        content = file_path.read_text()
        
        # Parse command from content
        # Format: # Command Name
        #         Description here
        #         ```
        #         command template
        #         ```
        
        lines = content.split("\n")
        name = lines[0].lstrip("# ").strip() if lines else "unnamed"
        
        # Find command block
        template = ""
        in_block = False
        for line in lines[1:]:
            if line.strip() == "```":
                in_block = not in_block
                continue
            if in_block:
                template += line + "\n"
        
        command = CommandInfo(
            name=name,
            description=content,
            template=template.strip(),
        )
        
        self.registry.register(command)
        return await self.execute(name, **kwargs)


# Global registry
_registry = CommandRegistry()
_executor = CommandExecutor(_registry)


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    return _registry


def get_executor() -> CommandExecutor:
    """Get the global command executor."""
    return _executor
