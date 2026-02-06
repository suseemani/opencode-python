"""Plugin system for opencode."""

from typing import Any, Callable

from opencode.util import log


logger = log.create({"service": "plugin"})


PluginHandler = Callable[..., Any]

_plugins: dict[str, list[PluginHandler]] = {}


def register(event: str, handler: PluginHandler) -> None:
    """Register a plugin handler for an event."""
    if event not in _plugins:
        _plugins[event] = []
    
    _plugins[event].append(handler)
    logger.info("registered plugin handler", {"event": event})


def unregister(event: str, handler: PluginHandler) -> None:
    """Unregister a plugin handler."""
    if event in _plugins and handler in _plugins[event]:
        _plugins[event].remove(handler)
        logger.info("unregistered plugin handler", {"event": event})


async def trigger(event: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Trigger plugin handlers for an event."""
    handlers = _plugins.get(event, [])
    
    result = {"status": "continue"}
    
    for handler in handlers:
        try:
            if asyncio.iscoroutinefunction(handler):
                handler_result = await handler(*args, **kwargs)
            else:
                handler_result = handler(*args, **kwargs)
            
            if isinstance(handler_result, dict):
                result.update(handler_result)
        except Exception as e:
            logger.error("plugin handler failed", {"event": event, "error": str(e)})
    
    return result


def list_events() -> list[str]:
    """List all registered plugin events."""
    return list(_plugins.keys())


async def init() -> None:
    """Initialize plugin system."""
    logger.info("initializing plugin system")
    
    # Load plugins from config
    from opencode.config import index as config
    cfg = await config.get()
    
    for plugin in cfg.plugin or []:
        logger.info("loading plugin", {"plugin": plugin})
        # Implement plugin loading logic here


import asyncio
