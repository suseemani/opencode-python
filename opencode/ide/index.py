"""IDE integration module."""

import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "ide"})


class IDEType(str, Enum):
    """Supported IDE types."""
    
    VSCODE = "vscode"
    VSCODIUM = "vscodium"
    CURSOR = "cursor"
    ZED = "zed"
    JETBRAINS = "jetbrains"
    SUBLIME = "sublime"
    NEOVIM = "neovim"
    VIM = "vim"


class IDEConfig(BaseModel):
    """IDE configuration."""
    
    name: str = Field(description="IDE name")
    type: IDEType = Field(description="IDE type")
    command: str = Field(description="Command to launch IDE")
    supports_diff: bool = Field(default=True, description="Whether IDE supports showing diffs")
    supports_protocol: bool = Field(default=False, description="Whether IDE supports custom protocol")


class IDEManager:
    """Manages IDE integrations."""
    
    def __init__(self) -> None:
        self._ides: dict[IDEType, IDEConfig] = {}
        self._init_default_ides()
    
    def _init_default_ides(self) -> None:
        """Initialize default IDE configurations."""
        self.register(IDEConfig(
            name="VS Code",
            type=IDEType.VSCODE,
            command="code",
            supports_diff=True,
            supports_protocol=True,
        ))
        
        self.register(IDEConfig(
            name="Cursor",
            type=IDEType.CURSOR,
            command="cursor",
            supports_diff=True,
            supports_protocol=True,
        ))
        
        self.register(IDEConfig(
            name="Zed",
            type=IDEType.ZED,
            command="zed",
            supports_diff=True,
        ))
        
        self.register(IDEConfig(
            name="Neovim",
            type=IDEType.NEOVIM,
            command="nvim",
            supports_diff=False,
        ))
    
    def register(self, config: IDEConfig) -> None:
        """Register an IDE."""
        self._ides[config.type] = config
    
    def get(self, ide_type: IDEType) -> IDEConfig | None:
        """Get IDE configuration."""
        return self._ides.get(ide_type)
    
    def detect_installed_ides(self) -> list[IDEType]:
        """Detect which IDEs are installed."""
        import shutil
        
        installed = []
        for ide_type, config in self._ides.items():
            if shutil.which(config.command):
                installed.append(ide_type)
        
        return installed
    
    def open_file(
        self,
        file_path: str | Path,
        ide_type: IDEType | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> bool:
        """Open a file in an IDE."""
        path = Path(file_path)
        
        if not path.exists():
            log.error("File not found", {"path": str(path)})
            return False
        
        # Detect IDE if not specified
        if not ide_type:
            installed = self.detect_installed_ides()
            if not installed:
                log.error("No IDE detected")
                return False
            ide_type = installed[0]
        
        config = self.get(ide_type)
        if not config:
            log.error("IDE not found", {"type": ide_type})
            return False
        
        # Build command
        cmd = [config.command]
        
        # Add line/column if supported
        if line is not None:
            if ide_type in (IDEType.VSCODE, IDEType.CURSOR):
                if column:
                    cmd.extend(["--goto", f"{path}:{line}:{column}"])
                else:
                    cmd.extend(["--goto", f"{path}:{line}"])
            else:
                cmd.append(str(path))
        else:
            cmd.append(str(path))
        
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info("Opened file in IDE", {"path": str(path), "ide": config.name})
            return True
        except Exception as e:
            log.error("Failed to open IDE", {"error": str(e)})
            return False
    
    def open_diff(
        self,
        file_path: str | Path,
        original_content: str,
        modified_content: str,
        ide_type: IDEType | None = None,
    ) -> bool:
        """Open a diff view in IDE."""
        path = Path(file_path)
        
        # Detect IDE if not specified
        if not ide_type:
            installed = self.detect_installed_ides()
            if not installed:
                return False
            ide_type = installed[0]
        
        config = self.get(ide_type)
        if not config or not config.supports_diff:
            log.error("IDE does not support diff view")
            return False
        
        # Create temp files for diff
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=path.suffix, delete=False) as f:
            f.write(original_content)
            original_file = f.name
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=path.suffix, delete=False) as f:
            f.write(modified_content)
            modified_file = f.name
        
        try:
            # Open diff in IDE
            if ide_type in (IDEType.VSCODE, IDEType.CURSOR):
                cmd = [config.command, "--diff", original_file, modified_file]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            else:
                # Fallback: just open the modified file
                return self.open_file(modified_file, ide_type)
        except Exception as e:
            log.error("Failed to open diff", {"error": str(e)})
            return False
        finally:
            # Clean up temp files
            import os
            try:
                os.unlink(original_file)
                os.unlink(modified_file)
            except:
                pass
    
    def open_workspace(self, path: str | Path, ide_type: IDEType | None = None) -> bool:
        """Open a workspace/directory in IDE."""
        path = Path(path)
        
        if not path.exists():
            return False
        
        # Detect IDE if not specified
        if not ide_type:
            installed = self.detect_installed_ides()
            if not installed:
                return False
            ide_type = installed[0]
        
        config = self.get(ide_type)
        if not config:
            return False
        
        try:
            subprocess.Popen(
                [config.command, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            log.error("Failed to open workspace", {"error": str(e)})
            return False


# Global instance
_manager: IDEManager | None = None


def get_manager() -> IDEManager:
    """Get the global IDE manager."""
    global _manager
    if _manager is None:
        _manager = IDEManager()
    return _manager
