"""Server routes module for opencode."""

from opencode.server.routes.index import (
    Route,
    RouteGroup,
    RouteHandler,
    register,
    register_group,
    get_routes,
    clear_routes,
)

__all__ = [
    "Route",
    "RouteGroup",
    "RouteHandler",
    "register",
    "register_group",
    "get_routes",
    "clear_routes",
]
