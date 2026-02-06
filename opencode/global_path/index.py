"""Global paths and configuration."""

import os
from pathlib import Path

APP_NAME = "opencode"
CACHE_VERSION = "21"


def get_home() -> str:
    """Get the home directory, allowing override for test isolation."""
    return os.environ.get("OPENCODE_TEST_HOME") or os.path.expanduser("~")


class GlobalPaths:
    """Global path configuration following XDG Base Directory Specification."""

    def __init__(self) -> None:
        self._init_xdg_paths()
        self._ensure_directories()
        self._check_cache_version()

    def _init_xdg_paths(self) -> None:
        """Initialize XDG paths."""
        # XDG Data
        xdg_data = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
        self.data = Path(xdg_data) / APP_NAME

        # XDG Cache
        xdg_cache = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
        self.cache = Path(xdg_cache) / APP_NAME

        # XDG Config
        xdg_config = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
        self.config = Path(xdg_config) / APP_NAME

        # XDG State
        xdg_state = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
        self.state = Path(xdg_state) / APP_NAME

        # Derived paths
        self.bin = self.data / "bin"
        self.log = self.data / "log"

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.data.mkdir(parents=True, exist_ok=True)
        self.config.mkdir(parents=True, exist_ok=True)
        self.state.mkdir(parents=True, exist_ok=True)
        self.log.mkdir(parents=True, exist_ok=True)
        self.bin.mkdir(parents=True, exist_ok=True)
        self.cache.mkdir(parents=True, exist_ok=True)

    def _check_cache_version(self) -> None:
        """Check and clear cache if version mismatch."""
        version_file = self.cache / "version"
        current_version = "0"

        if version_file.exists():
            try:
                current_version = version_file.read_text().strip()
            except Exception:
                pass

        if current_version != CACHE_VERSION:
            # Clear cache
            if self.cache.exists():
                for item in self.cache.iterdir():
                    try:
                        if item.is_dir():
                            import shutil

                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except Exception:
                        pass

            # Write new version
            version_file.write_text(CACHE_VERSION)


# Global instance
_paths: GlobalPaths | None = None


def get_paths() -> GlobalPaths:
    """Get the global paths instance."""
    global _paths
    if _paths is None:
        _paths = GlobalPaths()
    return _paths


# Convenience exports
data = property(lambda self: get_paths().data)
cache = property(lambda self: get_paths().cache)
config = property(lambda self: get_paths().config)
state = property(lambda self: get_paths().state)
bin_dir = property(lambda self: get_paths().bin)
log = property(lambda self: get_paths().log)
