"""Task tool for subtask/agent execution."""

import uuid
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "task"})


class TaskTool(Tool):
    """Tool for creating and executing subtasks with specialized agents."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="task",
            description="Launch a new subtask with a specialized agent. Available agents: general, build, plan, explore, docs. The subagent will execute independently and return results.",
            parameters=[
                ToolParameter(
                    name="description",
                    type="string",
                    description="A short (3-5 words) description of the task",
                    required=True,
                ),
                ToolParameter(
                    name="prompt",
                    type="string",
                    description="The task for the agent to perform",
                    required=True,
                ),
                ToolParameter(
                    name="subagent_type",
                    type="string",
                    description="The type of specialized agent to use for this task (general, build, plan, explore, docs)",
                    required=True,
                ),
                ToolParameter(
                    name="session_id",
                    type="string",
                    description="Existing Task session to continue (optional)",
                    required=False,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                    "session_id": {"type": "string"},
                    "success": {"type": "boolean"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute a subtask with a specialized agent."""
        description = params.get("description", "")
        prompt = params.get("prompt", "")
        subagent_type = params.get("subagent_type", "general")
        existing_session_id = params.get("session_id")

        if not description:
            return {
                "success": False,
                "output": "Task description is required",
                "title": "Task error",
            }

        if not prompt:
            return {
                "success": False,
                "output": "Task prompt is required",
                "title": "Task error",
            }

        # Validate subagent type
        valid_agents = ["general", "build", "plan", "explore", "docs"]
        if subagent_type not in valid_agents:
            return {
                "success": False,
                "output": f"Invalid subagent type: {subagent_type}. Valid types: {', '.join(valid_agents)}",
                "title": "Task error",
            }

        # Generate or use existing session ID
        session_id = existing_session_id or str(uuid.uuid4())

        log.info("Creating subtask", {
            "description": description,
            "agent": subagent_type,
            "session_id": session_id,
        })

        # In a full implementation, this would:
        # 1. Create a new child session linked to parent
        # 2. Assign the specified agent type
        # 3. Execute the prompt
        # 4. Return results

        # For now, return a mock response indicating the task structure
        output = f"""Task: {description}
Agent: {subagent_type}
Prompt: {prompt}

<task_metadata>
session_id: {session_id}
parent_session_id: {context.session_id or 'none'}
</task_metadata>"""

        return {
            "success": True,
            "output": output,
            "title": description,
            "session_id": session_id,
        }


# Singleton instance
_task_tool = TaskTool()


def get_tool() -> TaskTool:
    """Get the task tool instance."""
    return _task_tool
