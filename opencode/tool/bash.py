"""Bash tool for executing shell commands."""

import asyncio
import os
import shlex
from typing import Any

from pydantic import Field

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "bash"})


class BashTool(Tool):
    """Tool for executing bash/shell commands."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="bash",
            description="Execute a bash/shell command. Use this for running commands, installing packages, building projects, etc.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="The shell command to execute",
                    required=True,
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Timeout in milliseconds (default: 60000)",
                    required=False,
                    default=60000,
                ),
                ToolParameter(
                    name="cwd",
                    type="string",
                    description="Working directory for the command (defaults to project directory)",
                    required=False,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "stdout": {"type": "string"},
                    "stderr": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute a shell command."""
        command = params.get("command", "")
        timeout_ms = params.get("timeout", 60000)
        cwd = params.get("cwd") or context.project_dir or os.getcwd()

        if not command:
            return {
                "stdout": "",
                "stderr": "Error: No command provided",
                "exit_code": 1,
            }

        log.info("Executing command", {"command": command, "cwd": cwd})

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_ms / 1000,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout_ms}ms",
                    "exit_code": -1,
                }

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate output if too long
            max_output = 10000
            if len(stdout) > max_output:
                stdout = stdout[:max_output] + f"\n... ({len(stdout) - max_output} more characters)"
            if len(stderr) > max_output:
                stderr = stderr[:max_output] + f"\n... ({len(stderr) - max_output} more characters)"

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode or 0,
            }

        except Exception as e:
            log.error("Command execution failed", {"error": str(e)})
            return {
                "stdout": "",
                "stderr": f"Error executing command: {e}",
                "exit_code": 1,
            }


# Singleton instance
_bash_tool = BashTool()


def get_tool() -> BashTool:
    """Get the bash tool instance."""
    return _bash_tool
