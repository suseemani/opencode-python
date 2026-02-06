"""Todo tool for OpenCode."""

from typing import Any

from pydantic import BaseModel, Field

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "todo"})


class TodoItem(BaseModel):
    """A todo item."""

    id: str = Field(description="Todo ID")
    content: str = Field(description="Todo content")
    status: str = Field(default="pending", description="Todo status: pending, in_progress, completed")
    priority: str = Field(default="medium", description="Priority: low, medium, high")


class TodoManager:
    """Manages todos for a session."""

    def __init__(self) -> None:
        self._todos: dict[str, list[TodoItem]] = {}

    def get_todos(self, session_id: str) -> list[TodoItem]:
        """Get todos for a session."""
        return self._todos.get(session_id, [])

    def update_todos(self, session_id: str, todos: list[TodoItem]) -> None:
        """Update todos for a session."""
        self._todos[session_id] = todos

    def add_todo(self, session_id: str, content: str, priority: str = "medium") -> TodoItem:
        """Add a new todo."""
        import uuid

        todo = TodoItem(
            id=str(uuid.uuid4())[:8],
            content=content,
            priority=priority,
        )

        todos = self.get_todos(session_id)
        todos.append(todo)
        self.update_todos(session_id, todos)

        return todo


# Global todo manager
_todo_manager = TodoManager()


class TodoReadTool(Tool):
    """Tool for reading todos."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="todoread",
            description="Read the current todo list",
            parameters=[],
            returns={
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "content": {"type": "string"},
                                "status": {"type": "string"},
                                "priority": {"type": "string"},
                            },
                        },
                    },
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Read todos."""
        todos = _todo_manager.get_todos(context.session_id or "default")

        return {
            "todos": [todo.model_dump() for todo in todos],
            "count": len(todos),
            "pending": len([t for t in todos if t.status == "pending"]),
        }


class TodoWriteTool(Tool):
    """Tool for writing/updating todos."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="todowrite",
            description="Update the todo list - add, modify, or remove todos",
            parameters=[
                ToolParameter(
                    name="todos",
                    type="array",
                    description="The updated todo list",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "count": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Write todos."""
        todos_data = params.get("todos", [])

        todos = [TodoItem(**todo) for todo in todos_data]
        _todo_manager.update_todos(context.session_id or "default", todos)

        return {
            "success": True,
            "count": len(todos),
        }


# Singleton instances
_todo_read_tool = TodoReadTool()
_todo_write_tool = TodoWriteTool()


def get_read_tool() -> TodoReadTool:
    """Get the todo read tool instance."""
    return _todo_read_tool


def get_write_tool() -> TodoWriteTool:
    """Get the todo write tool instance."""
    return _todo_write_tool
