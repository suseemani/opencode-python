"""Signal handling utilities."""

import asyncio
import signal
from collections.abc import Callable
from typing import Any

_signal_handlers: dict[int, list[Callable[[], Any]]] = {}


def on_exit(handler: Callable[[], Any]) -> None:
    """Register a handler to be called on exit signals (SIGINT, SIGTERM)."""
    _signal_handlers.setdefault(signal.SIGINT, []).append(handler)
    _signal_handlers.setdefault(signal.SIGTERM, []).append(handler)

    # Set up signal handler if not already set
    def _handler(signum: int, frame: Any) -> None:
        for h in _signal_handlers.get(signum, []):
            try:
                h()
            except Exception:
                pass

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def on_signal(sig: int, handler: Callable[[], Any]) -> None:
    """Register a handler for a specific signal."""
    _signal_handlers.setdefault(sig, []).append(handler)

    def _handler(signum: int, frame: Any) -> None:
        for h in _signal_handlers.get(signum, []):
            try:
                h()
            except Exception:
                pass

    signal.signal(sig, _handler)


class SignalHandler:
    """Context manager for temporary signal handling."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    async def wait(self) -> None:
        """Wait for a signal."""
        await self._event.wait()

    def __enter__(self) -> "SignalHandler":
        on_exit(self._event.set)
        return self

    def __exit__(self, *args: Any) -> None:
        pass
