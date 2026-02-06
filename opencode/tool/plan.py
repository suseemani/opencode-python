"""Plan tools for switching between plan and build agents."""

from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "plan"})


class PlanExitTool(Tool):
    """Tool for exiting plan mode and switching to build agent."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="plan_exit",
            description="Exit plan mode and switch to the build agent to start implementing. Call this when the plan is complete and ready for implementation.",
            parameters=[],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Exit plan mode and prompt to switch to build agent."""
        log.info("Exiting plan mode")

        # This tool signals the system to switch agents
        # The actual switch happens at the session level
        return {
            "output": "Plan is complete. The build agent can now start implementing.",
            "title": "Switching to build agent",
            "switch_agent": "build",
        }


class PlanEnterTool(Tool):
    """Tool for entering plan mode from build agent."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="plan_enter",
            description="Enter plan mode to create a detailed plan before implementation. Use this when you need to research and plan before making code changes.",
            parameters=[],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Enter plan mode."""
        log.info("Entering plan mode")

        # This tool signals the system to switch to plan agent
        return {
            "output": "Entering plan mode. A plan file will be created for detailed planning.",
            "title": "Switching to plan agent",
            "switch_agent": "plan",
        }


# Singleton instances
_plan_exit_tool = PlanExitTool()
_plan_enter_tool = PlanEnterTool()


def get_exit_tool() -> PlanExitTool:
    """Get the plan_exit tool instance."""
    return _plan_exit_tool


def get_enter_tool() -> PlanEnterTool:
    """Get the plan_enter tool instance."""
    return _plan_enter_tool
