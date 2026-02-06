"""Plugin module for opencode."""

from opencode.plugin.index import (
    PluginHandler,
    init,
    list_events,
    register,
    trigger,
    unregister,
)

__all__ = [
    "PluginHandler",
    "init",
    "list_events",
    "register",
    "trigger",
    "unregister",
]
