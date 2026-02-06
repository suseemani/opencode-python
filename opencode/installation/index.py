"""Installation management module for opencode."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import bus_event
from opencode.flag import index as flag
from opencode.util import log

logger = log.create(service="installation")

VERSION = "0.0.1"
CHANNEL = "local"
USER_AGENT = f"opencode/{CHANNEL}/{VERSION}/{flag.OPENCODE_CLIENT}"


class InstallationInfo(BaseModel):
    """Installation information."""
    version: str = Field(description="Current version")
    latest: str = Field(description="Latest available version")


class UpgradeFailedError(Exception):
    """Error raised when upgrade fails."""
    def __init__(self, stderr: str) -> None:
        self.stderr = stderr
        super().__init__(f"Upgrade failed: {stderr}")


UpdatedEvent = bus_event.BusEvent.define(
    "installation.updated",
    {"version": str},
)

UpdateAvailableEvent = bus_event.BusEvent.define(
    "installation.update-available",
    {"version": str},
)

Event = {
    "Updated": UpdatedEvent,
    "UpdateAvailable": UpdateAvailableEvent,
}


async def info() -> InstallationInfo:
    """Get installation information."""
    return InstallationInfo(
        version=VERSION,
        latest=await latest(),
    )


def is_preview() -> bool:
    """Check if running a preview version."""
    return CHANNEL != "latest"


def is_local() -> bool:
    """Check if running from local installation."""
    return CHANNEL == "local"


async def method() -> str:
    """Detect installation method."""
    exec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    # Check for curl installation
    if ".opencode" in exec_path or ".local" in exec_path:
        return "curl"
    
    exec_lower = exec_path.lower()
    
    # Define checks
    checks: list[tuple[str, list[str]]] = [
        ("npm", ["npm", "list", "-g", "--depth=0"]),
        ("yarn", ["yarn", "global", "list"]),
        ("pnpm", ["pnpm", "list", "-g", "--depth=0"]),
        ("pip", ["pip", "list"]),
        ("pipx", ["pipx", "list"]),
        ("brew", ["brew", "list", "--formula", "opencode"]),
        ("scoop", ["scoop", "list", "opencode"]),
        ("choco", ["choco", "list", "--limit-output", "opencode"]),
    ]
    
    # Sort by likelihood based on exec path
    checks.sort(key=lambda x: exec_lower.count(x[0]), reverse=True)
    
    for name, cmd in checks:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            installed_name = "opencode"
            if name in ("brew", "choco", "scoop"):
                installed_name = "opencode"
            else:
                installed_name = "opencode-ai"
            
            if installed_name in result.stdout.lower():
                return name
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            continue
    
    return "unknown"


async def _get_brew_formula() -> str:
    """Get the brew formula name."""
    try:
        result = subprocess.run(
            ["brew", "list", "--formula", "anomalyco/tap/opencode"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "opencode" in result.stdout:
            return "anomalyco/tap/opencode"
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["brew", "list", "--formula", "opencode"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "opencode" in result.stdout:
            return "opencode"
    except Exception:
        pass
    
    return "opencode"


async def upgrade(method_name: str, target: str) -> None:
    """Upgrade opencode installation."""
    cmd: list[str] = []
    env = {**os.environ}
    
    if method_name == "curl":
        cmd = ["bash", "-c", f"curl -fsSL https://opencode.ai/install | VERSION={target} bash"]
    elif method_name == "npm":
        cmd = ["npm", "install", "-g", f"opencode-ai@{target}"]
    elif method_name == "pnpm":
        cmd = ["pnpm", "install", "-g", f"opencode-ai@{target}"]
    elif method_name == "pip":
        cmd = ["pip", "install", "--upgrade", f"opencode-ai=={target}"]
    elif method_name == "pipx":
        cmd = ["pipx", "upgrade", "opencode-ai"]
    elif method_name == "brew":
        formula = await _get_brew_formula()
        cmd = ["brew", "upgrade", formula]
        env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    elif method_name == "choco":
        cmd = ["choco", "upgrade", "opencode", f"--version={target}", "-y"]
    elif method_name == "scoop":
        cmd = ["scoop", "update", "opencode"]
    else:
        raise ValueError(f"Unknown method: {method_name}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        env=env,
        timeout=300,
    )
    
    if result.returncode != 0:
        stderr = result.stderr.decode() if result.stderr else "Unknown error"
        if method_name == "choco":
            stderr = "not running from an elevated command shell"
        raise UpgradeFailedError(stderr)
    
    logger.info(
        "upgraded",
        {
            "method": method_name,
            "target": target,
            "stdout": result.stdout.decode() if result.stdout else "",
        },
    )


async def latest(install_method: str | None = None) -> str:
    """Get the latest version."""
    detected_method = install_method or await method()
    
    if detected_method == "brew":
        try:
            import urllib.request
            import json
            
            url = "https://formulae.brew.sh/api/formula/opencode.json"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                return data["versions"]["stable"]
        except Exception:
            pass
    
    if detected_method in ("npm", "pnpm", "pip"):
        try:
            import urllib.request
            import json
            
            registry = "https://pypi.org/pypi/opencode-ai/json"
            with urllib.request.urlopen(registry, timeout=10) as response:
                data = json.loads(response.read())
                return data["info"]["version"]
        except Exception:
            pass
    
    if detected_method == "choco":
        try:
            import urllib.request
            import json
            
            url = "https://community.chocolatey.org/api/v2/Packages?$filter=Id%20eq%20%27opencode%27%20and%20IsLatestVersion&$select=Version"
            headers = {"Accept": "application/json;odata=verbose"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                return data["d"]["results"][0]["Version"]
        except Exception:
            pass
    
    if detected_method == "scoop":
        try:
            import urllib.request
            import json
            
            url = "https://raw.githubusercontent.com/ScoopInstaller/Main/master/bucket/opencode.json"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                return data["version"]
        except Exception:
            pass
    
    # Default to GitHub releases
    try:
        import urllib.request
        import json
        
        url = "https://api.github.com/repos/anomalyco/opencode/releases/latest"
        headers = {"User-Agent": USER_AGENT}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data["tag_name"].replace("v", "")
    except Exception:
        return VERSION


__all__ = [
    "InstallationInfo",
    "UpgradeFailedError",
    "VERSION",
    "CHANNEL",
    "USER_AGENT",
    "info",
    "is_preview",
    "is_local",
    "method",
    "upgrade",
    "latest",
    "Event",
]
