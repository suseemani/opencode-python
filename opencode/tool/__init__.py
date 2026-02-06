"""Tool module with all available tools."""

from opencode.tool.tool import (
    Tool,
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    define,
    get_registry,
    register,
)

# Import all tools
from opencode.tool.bash import get_tool as get_bash_tool
from opencode.tool.read import get_tool as get_read_tool
from opencode.tool.write import get_tool as get_write_tool
from opencode.tool.edit import get_tool as get_edit_tool
from opencode.tool.grep import get_tool as get_grep_tool
from opencode.tool.ls import get_tool as get_ls_tool
from opencode.tool.glob import get_tool as get_glob_tool
from opencode.tool.webfetch import get_tool as get_webfetch_tool

# Import additional tools
from opencode.tool.websearch import get_tool as get_websearch_tool
from opencode.tool.todo import (
    get_read_tool as get_todo_read_tool,
    get_write_tool as get_todo_write_tool,
)
from opencode.tool.question import get_tool as get_question_tool
from opencode.tool.batch import get_tool as get_batch_tool
from opencode.tool.codesearch import get_tool as get_codesearch_tool
from opencode.tool.multiedit import get_tool as get_multiedit_tool
from opencode.tool.plan import get_exit_tool as get_plan_exit_tool, get_enter_tool as get_plan_enter_tool
from opencode.tool.task import get_tool as get_task_tool
from opencode.tool.lsp import get_tool as get_lsp_tool
from opencode.tool.skill import get_tool as get_skill_tool
from opencode.tool.apply_patch import get_tool as get_apply_patch_tool

__all__ = [
    "Tool",
    "ToolContext",
    "ToolDefinition",
    "ToolParameter",
    "ToolRegistry",
    "define",
    "get_registry",
    "register",
    "register_all_tools",
]


def register_all_tools() -> None:
    """Register all available tools in the global registry."""
    registry = get_registry()

    # Register core tools
    registry.register(get_bash_tool())
    registry.register(get_read_tool())
    registry.register(get_write_tool())
    registry.register(get_edit_tool())
    registry.register(get_grep_tool())
    registry.register(get_ls_tool())
    registry.register(get_glob_tool())
    registry.register(get_webfetch_tool())

    # Register additional tools
    registry.register(get_websearch_tool())
    registry.register(get_todo_read_tool())
    registry.register(get_todo_write_tool())
    registry.register(get_question_tool())
    registry.register(get_batch_tool())
    registry.register(get_codesearch_tool())
    registry.register(get_multiedit_tool())
    registry.register(get_plan_exit_tool())
    registry.register(get_plan_enter_tool())
    registry.register(get_task_tool())
    registry.register(get_lsp_tool())
    registry.register(get_skill_tool())
    registry.register(get_apply_patch_tool())
