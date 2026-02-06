"""Scheduler module for opencode."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

from opencode.project import instance
from opencode.util import log

logger = log.create(service="scheduler")

Task = Callable[[], Coroutine[Any, Any, None]]


class _TaskEntry:
    """Task entry."""
    def __init__(
        self,
        id: str,
        interval: float,
        run: Task,
        scope: str,
    ):
        self.id = id
        self.interval = interval
        self.run = run
        self.scope = scope
        self.timer: asyncio.Task | None = None


class _Entry:
    """Scheduler entry."""
    def __init__(self) -> None:
        self.tasks: dict[str, _TaskEntry] = {}
        self.timers: dict[str, asyncio.Task] = {}


_shared = _Entry()


class _InstanceState:
    """Instance state manager."""
    def __init__(self) -> None:
        self._entry: _Entry | None = None
    
    async def get(self) -> _Entry:
        if self._entry is None:
            self._entry = _Entry()
        return self._entry
    
    async def cleanup(self) -> None:
        if self._entry:
            for timer in self._entry.timers.values():
                timer.cancel()
            self._entry.tasks.clear()
            self._entry.timers.clear()
            self._entry = None


_instance_state = _InstanceState()


async def _run_task(entry: _TaskEntry) -> None:
    """Run a scheduled task."""
    logger.info("run", {"id": entry.id})
    try:
        await entry.run()
    except Exception as error:
        logger.error("run failed", {"id": entry.id, "error": error})


async def _schedule_task(entry: _TaskEntry) -> None:
    """Schedule a task to run at intervals."""
    await _run_task(entry)
    
    while True:
        await asyncio.sleep(entry.interval / 1000)  # Convert ms to seconds
        await _run_task(entry)


def register(
    id: str,
    interval: float,
    run: Task,
    scope: str = "instance",
) -> None:
    """Register a scheduled task.
    
    Args:
        id: Task identifier
        interval: Interval in milliseconds
        run: Task function to run
        scope: "instance" or "global" (default: "instance")
    """
    entry_container = _shared if scope == "global" else _instance_state._entry or _Entry()
    
    if scope == "instance" and _instance_state._entry is None:
        _instance_state._entry = entry_container
    
    # Cancel existing timer if any
    existing_timer = entry_container.timers.get(id)
    if existing_timer:
        if scope == "global":
            return  # Don't re-register global tasks
        existing_timer.cancel()
    
    task_entry = _TaskEntry(id, interval, run, scope)
    entry_container.tasks[id] = task_entry
    
    # Run immediately and schedule
    timer_task = asyncio.create_task(_schedule_task(task_entry))
    entry_container.timers[id] = timer_task


async def unregister(id: str, scope: str = "instance") -> None:
    """Unregister a scheduled task."""
    entry_container = _shared if scope == "global" else await _instance_state.get()
    
    if id in entry_container.timers:
        entry_container.timers[id].cancel()
        del entry_container.timers[id]
    
    if id in entry_container.tasks:
        del entry_container.tasks[id]


async def list_tasks(scope: str | None = None) -> list[dict[str, Any]]:
    """List all scheduled tasks."""
    result: list[dict[str, Any]] = []
    
    if scope is None or scope == "global":
        for task in _shared.tasks.values():
            result.append({
                "id": task.id,
                "interval": task.interval,
                "scope": "global",
            })
    
    if scope is None or scope == "instance":
        entry = await _instance_state.get()
        for task in entry.tasks.values():
            result.append({
                "id": task.id,
                "interval": task.interval,
                "scope": "instance",
            })
    
    return result


async def cleanup() -> None:
    """Cleanup all instance-scoped tasks."""
    await _instance_state.cleanup()


__all__ = [
    "Task",
    "register",
    "unregister",
    "list_tasks",
    "cleanup",
]
