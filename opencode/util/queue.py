"""Async queue and concurrency utilities."""

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import TypeVar

T = TypeVar("T")


class AsyncQueue:
    """Async queue that can be used as an async iterator."""

    def __init__(self) -> None:
        self._queue: list[T] = []
        self._resolvers: list[asyncio.Future[T]] = []

    def push(self, item: T) -> None:
        """Push an item to the queue."""
        if self._resolvers:
            resolver = self._resolvers.pop(0)
            resolver.set_result(item)
        else:
            self._queue.append(item)

    async def next(self) -> T:
        """Get the next item from the queue."""
        if self._queue:
            return self._queue.pop(0)

        future: asyncio.Future[T] = asyncio.get_event_loop().create_future()
        self._resolvers.append(future)
        return await future

    def __aiter__(self) -> AsyncIterator[T]:
        """Return async iterator."""
        return self

    async def __anext__(self) -> T:
        """Get next item for async iteration."""
        return await self.next()


async def work(
    concurrency: int, items: list[T], fn: Callable[[T], asyncio.Future[None] | None]
) -> None:
    """
    Process items with limited concurrency.

    Args:
        concurrency: Maximum number of concurrent operations
        items: List of items to process
        fn: Function to apply to each item
    """
    pending = items.copy()

    async def worker() -> None:
        while True:
            if not pending:
                return
            item = pending.pop()
            result = fn(item)
            if result is not None:
                await result

    await asyncio.gather(*[worker() for _ in range(concurrency)])
