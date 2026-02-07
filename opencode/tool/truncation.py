"""Advanced output truncation for tools.

This module provides intelligent truncation for large tool outputs,
saving full content to files and returning truncated previews.
"""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from opencode.global_path import get_paths
from opencode.id import create as generate_id, timestamp as get_timestamp


# Constants
MAX_LINES = 2000
MAX_BYTES = 50 * 1024  # 50KB
RETENTION_MS = 7 * 24 * 60 * 60 * 1000  # 7 days
HOUR_MS = 60 * 60 * 1000  # 1 hour


@dataclass
class TruncationResult:
    """Result of truncation operation."""
    content: str
    truncated: bool
    output_path: str | None = None


class TruncationManager:
    """Manages output truncation and file cleanup."""
    
    def __init__(self) -> None:
        self._initialized = False
        self._cleanup_task: asyncio.Task | None = None
        self._dir: Path | None = None
    
    def _ensure_dir(self) -> Path:
        """Ensure truncation directory exists."""
        if self._dir is None:
            paths = get_paths()
            self._dir = Path(paths.data) / "tool-output"
            self._dir.mkdir(parents=True, exist_ok=True)
        return self._dir
    
    def init(self) -> None:
        """Initialize the truncation manager and start cleanup scheduler."""
        if self._initialized:
            return
        
        self._initialized = True
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()
    
    def _start_cleanup_scheduler(self) -> None:
        """Start the periodic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(HOUR_MS / 1000)  # Convert to seconds
                    await self.cleanup()
                except asyncio.CancelledError:
                    break
                except Exception:
                    # Silently ignore errors in cleanup
                    pass
        
        # Don't store reference to avoid keeping task alive
        asyncio.create_task(cleanup_loop())
    
    async def cleanup(self) -> None:
        """Clean up old truncated output files."""
        if self._dir is None:
            return
        
        cutoff_time = get_timestamp(generate_id("tool", descending=True)) - RETENTION_MS
        
        try:
            for filepath in self._dir.glob("tool_*"):
                if filepath.is_file():
                    # Extract timestamp from filename
                    try:
                        file_timestamp = get_timestamp(filepath.stem)
                        if file_timestamp < cutoff_time:
                            filepath.unlink(missing_ok=True)
                    except Exception:
                        # If we can't parse timestamp, delete old files by mtime
                        try:
                            mtime = filepath.stat().st_mtime * 1000  # Convert to ms
                            if mtime < cutoff_time:
                                filepath.unlink(missing_ok=True)
                        except Exception:
                            pass
        except Exception:
            # Silently ignore cleanup errors
            pass
    
    async def truncate(
        self,
        text: str,
        max_lines: int = MAX_LINES,
        max_bytes: int = MAX_BYTES,
        direction: Literal["head", "tail"] = "head",
    ) -> TruncationResult:
        """Truncate text if it exceeds limits.
        
        Args:
            text: Text to truncate
            max_lines: Maximum number of lines to keep
            max_bytes: Maximum bytes to keep
            direction: "head" to keep beginning, "tail" to keep end
            
        Returns:
            TruncationResult with truncated content and optional file path
        """
        lines = text.split("\n")
        total_bytes = len(text.encode("utf-8"))
        
        # Check if truncation is needed
        if len(lines) <= max_lines and total_bytes <= max_bytes:
            return TruncationResult(content=text, truncated=False)
        
        # Truncate
        out: list[str] = []
        i = 0
        bytes_count = 0
        hit_bytes = False
        
        if direction == "head":
            # Keep from the beginning
            for i in range(len(lines)):
                if len(out) >= max_lines:
                    break
                line = lines[i]
                line_bytes = len(line.encode("utf-8")) + (1 if i > 0 else 0)  # +1 for newline
                if bytes_count + line_bytes > max_bytes:
                    hit_bytes = True
                    break
                out.append(line)
                bytes_count += line_bytes
        else:
            # Keep from the end
            for i in range(len(lines) - 1, -1, -1):
                if len(out) >= max_lines:
                    break
                line = lines[i]
                line_bytes = len(line.encode("utf-8")) + (1 if len(out) > 0 else 0)
                if bytes_count + line_bytes > max_bytes:
                    hit_bytes = True
                    break
                out.insert(0, line)
                bytes_count += line_bytes
        
        # Calculate what was removed
        removed = total_bytes - bytes_count if hit_bytes else len(lines) - len(out)
        unit = "bytes" if hit_bytes else "lines"
        preview = "\n".join(out)
        
        # Save full content to file
        output_dir = self._ensure_dir()
        file_id = generate_id("tool", descending=False)
        output_path = output_dir / file_id
        
        try:
            output_path.write_text(text, encoding="utf-8")
        except Exception:
            # If we can't write file, return basic truncation
            truncated_content = preview + f"\n\n... ({removed} {unit} truncated)"
            return TruncationResult(
                content=truncated_content,
                truncated=True,
                output_path=None
            )
        
        # Create hint message
        hint = (
            f"The tool call succeeded but the output was truncated. "
            f"Full output saved to: {output_path}\n"
            f"Use the Task tool to have explore agent process this file with Grep and Read "
            f"(with offset/limit). Do NOT read the full file yourself - delegate to save context."
        )
        
        # Format final message
        if direction == "head":
            message = f"{preview}\n\n...{removed} {unit} truncated...\n\n{hint}"
        else:
            message = f"...{removed} {unit} truncated...\n\n{hint}\n\n{preview}"
        
        return TruncationResult(
            content=message,
            truncated=True,
            output_path=str(output_path)
        )


# Global instance
_manager: TruncationManager | None = None


def get_manager() -> TruncationManager:
    """Get the global truncation manager."""
    global _manager
    if _manager is None:
        _manager = TruncationManager()
        _manager.init()
    return _manager


async def truncate_output(
    text: str,
    max_lines: int = MAX_LINES,
    max_bytes: int = MAX_BYTES,
    direction: Literal["head", "tail"] = "head",
) -> TruncationResult:
    """Convenience function to truncate output.
    
    Args:
        text: Text to truncate
        max_lines: Maximum lines to keep
        max_bytes: Maximum bytes to keep
        direction: "head" or "tail"
        
    Returns:
        TruncationResult
    """
    manager = get_manager()
    return await manager.truncate(text, max_lines, max_bytes, direction)


# Export constants
__all__ = [
    "MAX_LINES",
    "MAX_BYTES",
    "RETENTION_MS",
    "HOUR_MS",
    "TruncationResult",
    "TruncationManager",
    "get_manager",
    "truncate_output",
]
