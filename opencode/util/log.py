"""Structured logging utilities."""

import asyncio
import sys
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from opencode.global_path import get_paths


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


_level_priority: dict[LogLevel, int] = {
    LogLevel.DEBUG: 0,
    LogLevel.INFO: 1,
    LogLevel.WARN: 2,
    LogLevel.ERROR: 3,
}

_current_level: LogLevel = LogLevel.INFO
_loggers: dict[str, "Logger"] = {}
_log_path: str = ""
_write_func: Callable[[str], Any] = lambda msg: sys.stderr.write(msg)
_last_time = datetime.now().timestamp() * 1000


def _should_log(level: LogLevel) -> bool:
    """Check if a log level should be logged."""
    return _level_priority[level] >= _level_priority[_current_level]


def _format_error(error: Exception, depth: int = 0) -> str:
    """Format an error message with cause chain."""
    result = str(error)
    if depth < 10 and error.__cause__ is not None:
        result += " Caused by: " + _format_error(error.__cause__, depth + 1)
    return result


class Logger:
    """Structured logger with tagging and timing support."""

    def __init__(self, tags: dict[str, Any] | None = None) -> None:
        self.tags = tags or {}
        self._last_time = datetime.now().timestamp() * 1000

    def _build(self, message: Any, extra: dict[str, Any] | None = None) -> str:
        """Build a log message with tags and metadata."""
        extra = extra or {}
        prefix_parts = []

        for key, value in {**self.tags, **extra}.items():
            if value is None:
                continue
            prefix = f"{key}="
            if isinstance(value, Exception):
                prefix_parts.append(prefix + _format_error(value))
            elif isinstance(value, dict | list):
                import json

                prefix_parts.append(prefix + json.dumps(value))
            else:
                prefix_parts.append(prefix + str(value))

        prefix = " ".join(prefix_parts)
        now = datetime.now()
        now_ms = now.timestamp() * 1000
        diff = int(now_ms - self._last_time)
        self._last_time = now_ms

        parts = [
            now.isoformat().split(".")[0],
            f"+{diff}ms",
            prefix,
            str(message) if message is not None else "",
        ]
        return " ".join(filter(None, parts)) + "\n"

    def debug(self, message: Any = None, extra: dict[str, Any] | None = None) -> None:
        """Log a debug message."""
        if _should_log(LogLevel.DEBUG):
            _write_func("DEBUG " + self._build(message, extra))

    def info(self, message: Any = None, extra: dict[str, Any] | None = None) -> None:
        """Log an info message."""
        if _should_log(LogLevel.INFO):
            _write_func("INFO  " + self._build(message, extra))

    def error(self, message: Any = None, extra: dict[str, Any] | None = None) -> None:
        """Log an error message."""
        if _should_log(LogLevel.ERROR):
            _write_func("ERROR " + self._build(message, extra))

    def warn(self, message: Any = None, extra: dict[str, Any] | None = None) -> None:
        """Log a warning message."""
        if _should_log(LogLevel.WARN):
            _write_func("WARN  " + self._build(message, extra))

    def tag(self, key: str, value: str) -> "Logger":
        """Add a tag to the logger."""
        self.tags[key] = value
        return self

    def clone(self) -> "Logger":
        """Create a cloned logger with the same tags."""
        return Logger(dict(self.tags))

    def time(self, message: str, extra: dict[str, Any] | None = None) -> "Timer":
        """Create a timer for the given message."""
        return Timer(self, message, extra)


class Timer:
    """Context manager for timing operations."""

    def __init__(
        self, logger: Logger, message: str, extra: dict[str, Any] | None = None
    ) -> None:
        self.logger = logger
        self.message = message
        self.extra = extra or {}
        self.start_time: float = 0

    def __enter__(self) -> "Timer":
        self.start_time = datetime.now().timestamp() * 1000
        self.logger.info(self.message, {"status": "started", **self.extra})
        return self

    def __exit__(self, *args: Any) -> None:
        duration = int(datetime.now().timestamp() * 1000 - self.start_time)
        self.logger.info(
            self.message, {"status": "completed", "duration": duration, **self.extra}
        )

    def stop(self) -> None:
        """Stop the timer and log completion."""
        self.__exit__()


def create(tags: dict[str, Any] | None = None) -> Logger:
    """Create a new logger with the given tags."""
    tags = tags or {}
    service = tags.get("service")

    if service and isinstance(service, str) and service in _loggers:
        return _loggers[service]

    logger = Logger(tags)

    if service and isinstance(service, str):
        _loggers[service] = logger

    return logger


class LogOptions:
    """Options for log initialization."""

    def __init__(
        self,
        print_only: bool = False,
        dev: bool = False,
        level: LogLevel | None = None,
    ) -> None:
        self.print_only = print_only
        self.dev = dev
        self.level = level


async def init(options: LogOptions) -> None:
    """Initialize logging with the given options."""
    global _current_level, _log_path, _write_func

    if options.level:
        _current_level = options.level

    paths = get_paths()
    await _cleanup(paths.log)

    if options.print_only:
        return

    # Generate log filename
    if options.dev:
        _log_path = str(paths.log / "dev.log")
    else:
        timestamp = datetime.now().isoformat().split(".")[0].replace(":", "")
        _log_path = str(paths.log / f"{timestamp}.log")

    # Truncate or create log file
    Path(_log_path).touch()
    Path(_log_path).write_text("")

    # Set up file writer
    def file_writer(msg: str) -> None:
        with open(_log_path, "a") as f:
            f.write(msg)

    _write_func = file_writer


async def _cleanup(log_dir: Path) -> None:
    """Clean up old log files, keeping the most recent 10."""
    import fnmatch

    files = sorted(log_dir.glob("????-??-??T??????.log"))
    if len(files) <= 5:
        return

    files_to_delete = files[:-10]
    for file in files_to_delete:
        try:
            file.unlink()
        except Exception:
            pass


def file() -> str:
    """Get the current log file path."""
    return _log_path


# Default logger instance
Default = create({"service": "default"})
