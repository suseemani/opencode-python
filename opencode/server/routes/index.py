"""Server routes for opencode."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from pydantic import BaseModel, Field

RouteHandler = Callable[..., Coroutine[Any, Any, Any]]


class Route(BaseModel):
    """Server route."""
    path: str = Field(description="Route path")
    method: str = Field(description="HTTP method")
    handler: RouteHandler = Field(description="Route handler")
    operation_id: str = Field(description="OpenAPI operation ID")
    summary: str = Field(default="", description="Route summary")
    description: str = Field(default="", description="Route description")
    tags: list[str] = Field(default_factory=list, description="Route tags")
    request_model: type[BaseModel] | None = Field(default=None, description="Request model")
    response_model: type[BaseModel] | None = Field(default=None, description="Response model")


class RouteGroup:
    """Group of routes."""
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix
        self.routes: list[Route] = []
    
    def get(
        self,
        path: str,
        operation_id: str,
        summary: str = "",
        description: str = "",
        tags: list[str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register a GET route."""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.routes.append(Route(
                path=self.prefix + path,
                method="GET",
                handler=handler,
                operation_id=operation_id,
                summary=summary,
                description=description,
                tags=tags or [],
                response_model=response_model,
            ))
            return handler
        return decorator
    
    def post(
        self,
        path: str,
        operation_id: str,
        summary: str = "",
        description: str = "",
        tags: list[str] | None = None,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register a POST route."""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.routes.append(Route(
                path=self.prefix + path,
                method="POST",
                handler=handler,
                operation_id=operation_id,
                summary=summary,
                description=description,
                tags=tags or [],
                request_model=request_model,
                response_model=response_model,
            ))
            return handler
        return decorator
    
    def patch(
        self,
        path: str,
        operation_id: str,
        summary: str = "",
        description: str = "",
        tags: list[str] | None = None,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register a PATCH route."""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.routes.append(Route(
                path=self.prefix + path,
                method="PATCH",
                handler=handler,
                operation_id=operation_id,
                summary=summary,
                description=description,
                tags=tags or [],
                request_model=request_model,
                response_model=response_model,
            ))
            return handler
        return decorator
    
    def delete(
        self,
        path: str,
        operation_id: str,
        summary: str = "",
        description: str = "",
        tags: list[str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register a DELETE route."""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.routes.append(Route(
                path=self.prefix + path,
                method="DELETE",
                handler=handler,
                operation_id=operation_id,
                summary=summary,
                description=description,
                tags=tags or [],
                response_model=response_model,
            ))
            return handler
        return decorator


_routes: list[Route] = []


def register(route: Route) -> None:
    """Register a route."""
    _routes.append(route)


def register_group(group: RouteGroup) -> None:
    """Register a route group."""
    _routes.extend(group.routes)


def get_routes() -> list[Route]:
    """Get all registered routes."""
    return _routes.copy()


def clear_routes() -> None:
    """Clear all routes."""
    _routes.clear()


__all__ = [
    "Route",
    "RouteGroup",
    "RouteHandler",
    "register",
    "register_group",
    "get_routes",
    "clear_routes",
]
