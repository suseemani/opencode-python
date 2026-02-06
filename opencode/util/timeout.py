"""Timeout utilities."""

import asyncio
from typing import TypeVar

T = TypeVar("T")


async def with_timeout(promise: asyncio.Future[T], ms: int) -> T:
    """
    Wrap a future with a timeout.

    Args:
        promise: The future to wrap
        ms: Timeout in milliseconds

    Returns:
        The result of the future

    Raises:
        TimeoutError: If the operation times out
    """

    async def timeout_task() -> None:
        await asyncio.sleep(ms / 1000)
        raise TimeoutError(f"Operation timed out after {ms}ms")

    done, pending = await asyncio.wait(
        [promise, asyncio.create_task(timeout_task())],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Cancel pending tasks
    for task in pending:
        task.cancel()

    # Get the result (or raise exception)
    result = await done.pop()
    return result
