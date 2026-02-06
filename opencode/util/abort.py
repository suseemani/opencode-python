"""Abort/timeout utilities."""

import asyncio
from collections.abc import Callable


class AbortHandle:
    """Handle for an abortable operation."""

    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._cancelled = False

    @property
    def signal(self) -> asyncio.Event:
        """Get the abort signal event."""
        return self._event

    def abort(self) -> None:
        """Trigger the abort signal."""
        self._cancelled = True
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self._cancelled


def abort_after(ms: int) -> tuple[AbortHandle, Callable[[], None]]:
    """
    Create an AbortHandle that automatically aborts after a timeout.

    Args:
        ms: Timeout in milliseconds

    Returns:
        Tuple of (abort_handle, clear_timeout_function)
    """
    handle = AbortHandle()

    async def _timeout() -> None:
        await asyncio.sleep(ms / 1000)
        handle.abort()

    task = asyncio.create_task(_timeout())

    def clear_timeout() -> None:
        task.cancel()

    return handle, clear_timeout


async def abort_after_any(
    ms: int, *signals: asyncio.Event
) -> tuple[asyncio.Event, Callable[[], None]]:
    """
    Combine multiple abort signals with a timeout.

    Args:
        ms: Timeout in milliseconds
        signals: Additional events to combine

    Returns:
        Tuple of (combined_event, clear_timeout_function)
    """
    combined = asyncio.Event()
    handle, clear_timeout = abort_after(ms)

    async def _wait_for_any() -> None:
        tasks = [
            asyncio.create_task(handle.signal.wait()),
            *[asyncio.create_task(s.wait()) for s in signals],
        ]
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        combined.set()

    asyncio.create_task(_wait_for_any())
    return combined, clear_timeout
