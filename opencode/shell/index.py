"""Shell module for opencode."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from opencode.flag import index as flag

SIGKILL_TIMEOUT_MS = 0.2  # 200ms

_BLACKLIST = {"fish", "nu"}


class ShellResult(BaseModel):
    """Shell command result."""
    stdout: str = Field(description="Standard output")
    stderr: str = Field(description="Standard error")
    exit_code: int = Field(description="Exit code")


async def kill_tree(proc: subprocess.Popen, exited: Callable[[], bool] | None = None) -> None:
    """Kill a process tree."""
    pid = proc.pid
    if pid is None or (exited and exited()):
        return
    
    if os.name == "nt":  # Windows
        try:
            killer = subprocess.Popen(
                ["taskkill", "/pid", str(pid), "/f", "/t"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.get_event_loop().run_in_executor(None, killer.wait)
        except Exception:
            pass
        return
    
    # Unix-like systems
    try:
        os.kill(-pid, signal.SIGTERM)
        await asyncio.sleep(SIGKILL_TIMEOUT_MS)
        if not (exited and exited()):
            os.kill(-pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        try:
            proc.terminate()
            await asyncio.sleep(SIGKILL_TIMEOUT_MS)
            if not (exited and exited()):
                proc.kill()
        except Exception:
            pass


def _fallback() -> str:
    """Get fallback shell."""
    if os.name == "nt":  # Windows
        git_bash = flag.OPENCODE_GIT_BASH_PATH
        if git_bash:
            return git_bash
        
        # Try to find git bash
        git_path = shutil.which("git")
        if git_path:
            bash = Path(git_path).parent.parent / "bin" / "bash.exe"
            if bash.exists():
                return str(bash)
        
        return os.environ.get("COMSPEC", "cmd.exe")
    
    if os.uname().sysname == "Darwin":  # macOS
        return "/bin/zsh"
    
    bash = shutil.which("bash")
    if bash:
        return bash
    
    return "/bin/sh"


_preferred: str | None = None


def preferred() -> str:
    """Get preferred shell."""
    global _preferred
    if _preferred is None:
        shell = os.environ.get("SHELL")
        _preferred = shell if shell else _fallback()
    return _preferred


_acceptable: str | None = None


def acceptable() -> str:
    """Get acceptable shell (not blacklisted)."""
    global _acceptable
    if _acceptable is None:
        shell = os.environ.get("SHELL")
        if shell:
            basename = Path(shell).name
            if basename not in _BLACKLIST:
                _acceptable = shell
            else:
                _acceptable = _fallback()
        else:
            _acceptable = _fallback()
    return _acceptable


async def run(
    command: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    shell: str | None = None,
) -> ShellResult:
    """Run a shell command."""
    use_shell = shell or acceptable()
    
    full_env = {**os.environ, **(env or {})}
    
    if os.name == "nt":
        # On Windows, use shell=True for better compatibility
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=full_env,
        )
    else:
        # On Unix, use explicit shell
        proc = await asyncio.create_subprocess_exec(
            use_shell,
            "-c",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=full_env,
        )
    
    stdout, stderr = await proc.communicate()
    
    return ShellResult(
        stdout=stdout.decode(),
        stderr=stderr.decode(),
        exit_code=proc.returncode or 0,
    )


__all__ = [
    "ShellResult",
    "kill_tree",
    "preferred",
    "acceptable",
    "run",
]

import shutil  # noqa: E402
