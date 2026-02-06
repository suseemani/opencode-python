"""Pseudo-terminal (PTY) implementation."""

import asyncio
import os
import platform
import signal
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "pty"})


class PTYSession(BaseModel):
    """PTY session information."""
    
    id: str = Field(description="Session ID")
    cwd: str = Field(description="Current working directory")
    shell: str = Field(description="Shell being used")
    pid: int | None = Field(default=None, description="Process ID")


class PTYProcess:
    """Manages a PTY process."""
    
    def __init__(
        self,
        session_id: str,
        shell: str,
        cwd: str,
        on_data: Callable[[str], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ) -> None:
        self.session_id = session_id
        self.shell = shell
        self.cwd = cwd
        self.on_data = on_data
        self.on_exit = on_exit
        self.process: asyncio.subprocess.Process | None = None
        self._running = False
    
    async def start(self) -> bool:
        """Start the PTY process."""
        try:
            # Create subprocess with PTY on Unix
            if platform.system() != "Windows":
                import pty
                import termios
                import tty
                
                # Fork with pseudo-terminal
                pid, fd = pty.fork()
                
                if pid == 0:
                    # Child process
                    os.chdir(self.cwd)
                    os.execv(self.shell, [self.shell])
                else:
                    # Parent process
                    self.process = await asyncio.create_subprocess_exec(
                        self.shell,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                        cwd=self.cwd,
                    )
            else:
                # Windows - use standard subprocess
                self.process = await asyncio.create_subprocess_shell(
                    self.shell,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=self.cwd,
                )
            
            self._running = True
            
            # Start reading output
            asyncio.create_task(self._read_output())
            
            return True
            
        except Exception as e:
            log.error("Failed to start PTY", {"error": str(e)})
            return False
    
    async def _read_output(self) -> None:
        """Read output from the PTY."""
        if not self.process or not self.process.stdout:
            return
        
        try:
            while self._running:
                data = await self.process.stdout.read(1024)
                if not data:
                    break
                
                text = data.decode("utf-8", errors="replace")
                if self.on_data:
                    self.on_data(text)
        
        except Exception as e:
            log.error("Error reading PTY output", {"error": str(e)})
        finally:
            self._running = False
            if self.on_exit and self.process:
                self.on_exit(self.process.returncode or 0)
    
    async def write(self, data: str) -> None:
        """Write data to the PTY."""
        if self.process and self.process.stdin:
            self.process.stdin.write(data.encode())
            await self.process.stdin.drain()
    
    async def resize(self, rows: int, cols: int) -> None:
        """Resize the PTY."""
        # Platform-specific resize
        if platform.system() != "Windows" and self.process:
            try:
                import fcntl
                import struct
                import termios
                
                # Get file descriptor
                fd = self.process.stdout._transport.get_extra_info("socket").fileno()
                
                # Set terminal size
                size = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
            except Exception as e:
                log.error("Failed to resize PTY", {"error": str(e)})
    
    async def kill(self) -> None:
        """Kill the PTY process."""
        self._running = False
        
        if self.process:
            try:
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                log.error("Error killing PTY", {"error": str(e)})
    
    @property
    def is_running(self) -> bool:
        """Check if PTY is running."""
        return self._running and self.process is not None


class PTYManager:
    """Manages PTY sessions."""
    
    def __init__(self) -> None:
        self._sessions: dict[str, PTYProcess] = {}
    
    async def create_session(
        self,
        session_id: str,
        cwd: str = ".",
        shell: str | None = None,
        on_data: Callable[[str], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ) -> PTYSession:
        """Create a new PTY session."""
        # Detect shell
        if not shell:
            shell = os.environ.get("SHELL", "/bin/bash")
            if platform.system() == "Windows":
                shell = os.environ.get("COMSPEC", "cmd.exe")
        
        # Create PTY process
        pty_process = PTYProcess(
            session_id=session_id,
            shell=shell,
            cwd=cwd,
            on_data=on_data,
            on_exit=on_exit,
        )
        
        if await pty_process.start():
            self._sessions[session_id] = pty_process
            
            return PTYSession(
                id=session_id,
                cwd=cwd,
                shell=shell,
                pid=pty_process.process.pid if pty_process.process else None,
            )
        else:
            raise RuntimeError("Failed to start PTY session")
    
    def get_session(self, session_id: str) -> PTYProcess | None:
        """Get a PTY session by ID."""
        return self._sessions.get(session_id)
    
    async def write_to_session(self, session_id: str, data: str) -> bool:
        """Write data to a session."""
        session = self.get_session(session_id)
        if session:
            await session.write(data)
            return True
        return False
    
    async def resize_session(self, session_id: str, rows: int, cols: int) -> bool:
        """Resize a session."""
        session = self.get_session(session_id)
        if session:
            await session.resize(rows, cols)
            return True
        return False
    
    async def close_session(self, session_id: str) -> bool:
        """Close a PTY session."""
        session = self._sessions.pop(session_id, None)
        if session:
            await session.kill()
            return True
        return False
    
    def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())


# Global instance
_manager: PTYManager | None = None


def get_manager() -> PTYManager:
    """Get the global PTY manager."""
    global _manager
    if _manager is None:
        _manager = PTYManager()
    return _manager
