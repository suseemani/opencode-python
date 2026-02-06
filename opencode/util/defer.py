"""Deferred execution utilities."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any


class Deferred(AbstractContextManager[Any]):
    """Context manager that defers execution of a function until exit."""

    def __init__(self, fn: Callable[[], None]) -> None:
        self.fn = fn

    def __exit__(self, *args: Any) -> None:
        self.fn()


class AsyncDeferred:
    """Async context manager that defers execution of a function until exit."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        self.fn = fn

    async def __aenter__(self) -> "AsyncDeferred":
        return self

    async def __aexit__(self, *args: Any) -> None:
        result = self.fn()
        if hasattr(result, "__await__"):
            await result


def defer(fn: Callable[[], None]) -> Deferred:
    """Create a deferred context manager."""
    return Deferred(fn)


def async_defer(fn: Callable[[], Any]) -> AsyncDeferred:
    """Create an async deferred context manager."""
    return AsyncDeferred(fn)
