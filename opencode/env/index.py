"""Environment variable management."""

import os
from typing import Any


class EnvManager:
    """Manages environment variables with instance isolation."""

    def __init__(self) -> None:
        # Create a shallow copy to isolate environment per instance
        # Prevents parallel tests from interfering with each other's env vars
        self._env = dict(os.environ)

    def get(self, key: str) -> str | None:
        """Get an environment variable."""
        return self._env.get(key)

    def all(self) -> dict[str, str]:
        """Get all environment variables."""
        return dict(self._env)

    def set(self, key: str, value: str) -> None:
        """Set an environment variable."""
        self._env[key] = value

    def remove(self, key: str) -> None:
        """Remove an environment variable."""
        self._env.pop(key, None)


# Global instance
_env_instance: EnvManager | None = None


def _get_instance() -> EnvManager:
    """Get or create the global EnvManager instance."""
    global _env_instance
    if _env_instance is None:
        _env_instance = EnvManager()
    return _env_instance


def get(key: str) -> str | None:
    """Get an environment variable."""
    return _get_instance().get(key)


def all() -> dict[str, str]:
    """Get all environment variables."""
    return _get_instance().all()


def set(key: str, value: str) -> None:
    """Set an environment variable."""
    _get_instance().set(key, value)


def remove(key: str) -> None:
    """Remove an environment variable."""
    _get_instance().remove(key)
