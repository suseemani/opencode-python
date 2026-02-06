"""Code formatting module."""

import asyncio
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "format"})


class FormatterConfig(BaseModel):
    """Formatter configuration."""
    
    name: str = Field(description="Formatter name")
    command: list[str] = Field(description="Formatter command and arguments")
    extensions: list[str] = Field(description="Supported file extensions")
    install_cmd: str | None = Field(default=None, description="Command to install formatter")


class FormatResult(BaseModel):
    """Result of formatting operation."""
    
    success: bool = Field(description="Whether formatting succeeded")
    formatted: bool = Field(description="Whether file was changed")
    output: str = Field(default="", description="Formatter output")
    error: str | None = Field(default=None, description="Error message if failed")


class FormatManager:
    """Manages code formatters."""
    
    def __init__(self) -> None:
        self._formatters: dict[str, FormatterConfig] = {}
        self._init_default_formatters()
    
    def _init_default_formatters(self) -> None:
        """Initialize default formatters."""
        self.register(FormatterConfig(
            name="black",
            command=["black", "-"],
            extensions=[".py"],
            install_cmd="pip install black",
        ))
        
        self.register(FormatterConfig(
            name="prettier",
            command=["prettier", "--stdin-filepath", "{file}"],
            extensions=[".js", ".ts", ".jsx", ".tsx", ".json", ".md", ".css", ".html"],
            install_cmd="npm install -g prettier",
        ))
        
        self.register(FormatterConfig(
            name="rustfmt",
            command=["rustfmt", "--emit", "stdout"],
            extensions=[".rs"],
        ))
        
        self.register(FormatterConfig(
            name="gofmt",
            command=["gofmt"],
            extensions=[".go"],
        ))
    
    def register(self, formatter: FormatterConfig) -> None:
        """Register a formatter."""
        self._formatters[formatter.name] = formatter
    
    def get(self, name: str) -> FormatterConfig | None:
        """Get a formatter by name."""
        return self._formatters.get(name)
    
    def get_for_file(self, file_path: str | Path) -> FormatterConfig | None:
        """Get appropriate formatter for a file."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        for formatter in self._formatters.values():
            if ext in formatter.extensions:
                return formatter
        return None
    
    def list_formatters(self) -> list[FormatterConfig]:
        """List all registered formatters."""
        return list(self._formatters.values())
    
    async def format_code(
        self,
        code: str,
        formatter_name: str | None = None,
        file_path: str | None = None,
    ) -> FormatResult:
        """Format code using specified or detected formatter."""
        # Get formatter
        if formatter_name:
            formatter = self.get(formatter_name)
        elif file_path:
            formatter = self.get_for_file(file_path)
        else:
            return FormatResult(
                success=False,
                formatted=False,
                error="No formatter specified and no file path provided",
            )
        
        if not formatter:
            return FormatResult(
                success=False,
                formatted=False,
                error="No suitable formatter found",
            )
        
        # Check if formatter is available
        cmd = formatter.command[0]
        if not shutil.which(cmd):
            return FormatResult(
                success=False,
                formatted=False,
                error=f"Formatter '{cmd}' not found. Install with: {formatter.install_cmd}",
            )
        
        try:
            # Prepare command
            command = formatter.command.copy()
            if file_path:
                command = [c.replace("{file}", file_path) for c in command]
            
            log.info("Formatting", {"formatter": formatter.name})
            
            # Run formatter
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await proc.communicate(code.encode())
            
            if proc.returncode != 0:
                return FormatResult(
                    success=False,
                    formatted=False,
                    error=stderr.decode(),
                )
            
            formatted_code = stdout.decode()
            
            return FormatResult(
                success=True,
                formatted=formatted_code != code,
                output=formatted_code,
            )
            
        except Exception as e:
            return FormatResult(
                success=False,
                formatted=False,
                error=str(e),
            )
    
    async def format_file(self, file_path: str | Path) -> FormatResult:
        """Format a file in place."""
        path = Path(file_path)
        
        if not path.exists():
            return FormatResult(
                success=False,
                formatted=False,
                error=f"File not found: {file_path}",
            )
        
        code = path.read_text()
        result = await self.format_code(code, file_path=str(path))
        
        if result.success and result.formatted:
            path.write_text(result.output)
        
        return result


# Global instance
_manager: FormatManager | None = None


def get_manager() -> FormatManager:
    """Get the global format manager."""
    global _manager
    if _manager is None:
        _manager = FormatManager()
    return _manager
