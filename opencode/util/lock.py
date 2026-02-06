"""Lock utilities for file locking."""

import fcntl
import os
from pathlib import Path
from typing import Any


class FileLock:
    """File-based lock for process synchronization."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._fd: int | None = None

    def acquire(self, blocking: bool = True) -> bool:
        """Acquire the lock."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR)

        try:
            if blocking:
                fcntl.flock(self._fd, fcntl.LOCK_EX)
            else:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            os.close(self._fd)
            self._fd = None
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()


class AsyncLock:
    """Async-aware lock using asyncio."""

    def __init__(self) -> None:
        self._lock = None

    async def __aenter__(self) -> "AsyncLock":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass
