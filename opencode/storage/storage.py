"""Storage layer for data persistence."""

import json
from pathlib import Path
from typing import Any, Callable, TypeVar

from opencode.global_path import get_paths

T = TypeVar("T")


class NotFoundError(Exception):
    """Error raised when a storage resource is not found."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class StorageManager:
    """Manages persistent storage with migrations."""

    def __init__(self) -> None:
        self._dir: Path | None = None
        self._initialized = False

    async def _init(self) -> Path:
        """Initialize storage directory and run migrations."""
        if self._initialized and self._dir:
            return self._dir

        paths = get_paths()
        self._dir = paths.data / "storage"
        self._dir.mkdir(parents=True, exist_ok=True)

        # Check and run migrations
        migration_file = self._dir / "migration"
        current_migration = 0

        if migration_file.exists():
            try:
                current_migration = int(migration_file.read_text().strip())
            except (ValueError, IOError):
                current_migration = 0

        # Run pending migrations
        for i in range(current_migration, len(self._migrations)):
            await self._run_migration(i)

        self._initialized = True
        return self._dir

    async def _run_migration(self, index: int) -> None:
        """Run a specific migration."""
        migration_file = self._dir / "migration"

        try:
            migration = self._migrations[index]
            await migration(self._dir)
        except Exception as e:
            # Log error but continue
            print(f"Migration {index} failed: {e}")

        # Update migration version
        migration_file.write_text(str(index + 1))

    @property
    def _migrations(self) -> list[Callable[[Path], Any]]:
        """List of migrations to run."""
        return [
            self._migration_0,
            self._migration_1,
        ]

    async def _migration_0(self, dir: Path) -> None:
        """Migration 0: Migrate old project structure."""
        # This is a placeholder - the actual migration logic would go here
        pass

    async def _migration_1(self, dir: Path) -> None:
        """Migration 1: Migrate session summaries."""
        # This is a placeholder - the actual migration logic would go here
        pass

    async def remove(self, key: list[str]) -> None:
        """Remove a storage entry."""
        dir = await self._init()
        target = dir / "/".join(key)
        target = target.with_suffix(".json")

        try:
            target.unlink(missing_ok=True)
        except OSError as e:
            raise NotFoundError(f"Resource not found: {target}") from e

    async def read(self, key: list[str]) -> Any:
        """Read a storage entry."""
        dir = await self._init()
        target = dir / "/".join(key)
        target = target.with_suffix(".json")

        try:
            content = target.read_text()
            return json.loads(content)
        except FileNotFoundError as e:
            raise NotFoundError(f"Resource not found: {target}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {target}") from e

    async def update(self, key: list[str], fn: Callable[[T], None]) -> T:
        """Update a storage entry."""
        dir = await self._init()
        target = dir / "/".join(key)
        target = target.with_suffix(".json")

        # Ensure directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Read existing or create new
        if target.exists():
            content = json.loads(target.read_text())
        else:
            content = {}

        # Apply update
        fn(content)

        # Write back
        target.write_text(json.dumps(content, indent=2))
        return content

    async def write(self, key: list[str], content: T) -> None:
        """Write a storage entry."""
        dir = await self._init()
        target = dir / "/".join(key)
        target = target.with_suffix(".json")

        # Ensure directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(json.dumps(content, indent=2, default=str))

    async def list_keys(self, prefix: list[str]) -> list[list[str]]:
        """List storage entries with the given prefix."""
        dir = await self._init()
        target_dir = dir / "/".join(prefix)

        if not target_dir.exists():
            return []

        results = []
        for file in target_dir.rglob("*.json"):
            # Convert path back to key list
            rel_path = file.relative_to(target_dir)
            key_parts = list(rel_path.parent.parts) + [rel_path.stem]
            results.append(prefix + key_parts)

        results.sort()
        return results


# Global instance
_manager: StorageManager | None = None


def get_manager() -> StorageManager:
    """Get the global storage manager."""
    global _manager
    if _manager is None:
        _manager = StorageManager()
    return _manager


# Convenience functions
async def remove(key: list[str]) -> None:
    """Remove a storage entry."""
    return await get_manager().remove(key)


async def read(key: list[str]) -> Any:
    """Read a storage entry."""
    return await get_manager().read(key)


async def update(key: list[str], fn: Callable[[Any], None]) -> Any:
    """Update a storage entry."""
    return await get_manager().update(key, fn)


async def write(key: list[str], content: Any) -> None:
    """Write a storage entry."""
    return await get_manager().write(key, content)


async def list_keys(prefix: list[str]) -> list[list[str]]:
    """List storage entries."""
    return await get_manager().list_keys(prefix)
