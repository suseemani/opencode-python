"""Tool framework for AI tools."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""

    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")
    required: bool = Field(default=True, description="Whether the parameter is required")
    default: Any | None = Field(default=None, description="Default value")


class ToolDefinition(BaseModel):
    """Definition of a tool."""

    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters: list[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    returns: dict[str, Any] = Field(default_factory=dict, description="Return type schema")


class ToolContext(BaseModel):
    """Context for tool execution."""

    session_id: str | None = Field(default=None, description="Session ID")
    project_dir: str | None = Field(default=None, description="Project directory")

    class Config:
        arbitrary_types_allowed = True


class Tool(ABC):
    """Abstract base class for AI tools."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Get the tool definition."""
        pass

    @abstractmethod
    async def execute(self, params: dict[str, Any], context: ToolContext) -> Any:
        """Execute the tool with the given parameters."""
        pass


class ToolRegistry:
    """Registry for tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.definition.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tool definitions."""
        return [tool.definition for tool in self._tools.values()]

    async def execute(self, name: str, params: dict[str, Any], context: ToolContext) -> Any:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return await tool.execute(params, context)


# Global registry
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register(tool: Tool) -> None:
    """Register a tool in the global registry."""
    _global_registry.register(tool)


def define(
    name: str,
    description: str,
    parameters: list[ToolParameter],
) -> ToolDefinition:
    """Define a new tool."""
    return ToolDefinition(
        name=name,
        description=description,
        parameters=parameters,
    )
