"""State management for opencode."""

from typing import Any, Awaitable, Callable, TypeVar

from opencode.util import log


logger = log.create({"service": "state"})

T = TypeVar("T")

StateInit = Callable[[], T] | Callable[[], Awaitable[T]]
StateDispose = Callable[[T], Awaitable[None]] | None


class StateEntry:
    """State entry with optional disposal."""
    def __init__(self, state: Any, dispose: StateDispose = None):
        self.state = state
        self.dispose = dispose


_records: dict[str, dict[Any, StateEntry]] = {}


def create(
    root: Callable[[], str],
    init: StateInit[T],
    dispose: StateDispose = None,
) -> Callable[[], T]:
    """Create a state getter for a given root."""
    def getter() -> T:
        key = root()
        entries = _records.get(key)
        if entries is None:
            entries = {}
            _records[key] = entries
        
        existing = entries.get(init)
        if existing:
            return existing.state
        
        state = init()
        entries[init] = StateEntry(state, dispose)
        return state
    
    return getter


async def dispose(key: str) -> None:
    """Dispose all state for a key."""
    entries = _records.get(key)
    if not entries:
        return
    
    logger.info("waiting for state disposal to complete", {"key": key})
    
    disposal_finished = False
    
    def timeout_warning():
        if not disposal_finished:
            logger.warn(
                "state disposal is taking an unusually long time",
                {"key": key},
            )
    
    import asyncio
    asyncio.get_event_loop().call_later(10, timeout_warning)
    
    tasks = []
    for init_func, entry in entries.items():
        if not entry.dispose:
            continue
        
        label = init_func.__name__ if hasattr(init_func, "__name__") else str(init_func)
        
        async def dispose_entry(state=entry.state, label=label):
            try:
                await entry.dispose(state)
            except Exception as e:
                logger.error("Error while disposing state:", {"error": str(e), "key": key, "init": label})
        
        tasks.append(dispose_entry())
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    entries.clear()
    del _records[key]
    
    disposal_finished = True
    logger.info("state disposal completed", {"key": key})
