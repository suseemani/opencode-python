"""Project module for opencode."""

from opencode.project.bootstrap import bootstrap
from opencode.project.instance import (
    contains_path,
    create_state,
    dispose,
    dispose_all,
    get_directory,
    get_project,
    get_worktree,
    provide,
)
from opencode.project.project import (
    Event,
    ProjectCommands,
    ProjectIcon,
    ProjectInfo,
    ProjectTime,
    add_sandbox,
    from_directory,
    get_sandboxes,
    list_projects,
    remove_sandbox,
    set_initialized,
    update,
)
from opencode.project.state import create as create_state_generic, dispose as dispose_state

__all__ = [
    "Event",
    "ProjectCommands",
    "ProjectIcon",
    "ProjectInfo",
    "ProjectTime",
    "add_sandbox",
    "bootstrap",
    "contains_path",
    "create_state",
    "create_state_generic",
    "dispose",
    "dispose_all",
    "dispose_state",
    "from_directory",
    "get_directory",
    "get_project",
    "get_sandboxes",
    "get_worktree",
    "list_projects",
    "provide",
    "remove_sandbox",
    "set_initialized",
    "update",
]
