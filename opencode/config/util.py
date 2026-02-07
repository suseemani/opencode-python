"""Configuration utilities for deep merging and file discovery."""

import os
import re
from pathlib import Path
from typing import Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def find_up(filenames: list[str], start_dir: Path, stop_dir: Path | None = None) -> list[Path]:
    """Find files by searching up the directory tree.
    
    Args:
        filenames: List of filenames to search for
        start_dir: Directory to start searching from
        stop_dir: Directory to stop at (exclusive), typically git root
        
    Returns:
        List of found file paths, ordered from closest to start_dir to farthest
    """
    found = []
    current = start_dir.resolve()
    stop = stop_dir.resolve() if stop_dir else Path("/").resolve()
    
    while True:
        for filename in filenames:
            filepath = current / filename
            if filepath.exists():
                found.append(filepath)
        
        # Stop if we've reached the stop directory or root
        if current == stop or current.parent == current:
            break
            
        current = current.parent
    
    return found


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.
    
    - Nested dicts are recursively merged
    - Lists are concatenated (base + override)
    - Other values are overwritten
    
    Args:
        base: Base dictionary
        override: Dictionary to merge into base
        
    Returns:
        New merged dictionary
    """
    result = dict(base)
    
    for key, value in override.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # Concatenate lists
                result[key] = result[key] + value
            else:
                # Overwrite other values
                result[key] = value
        else:
            result[key] = value
    
    return result


def substitute_env_vars(text: str) -> str:
    """Substitute environment variables in text.
    
    Supports syntax: {env:VAR_NAME} or {env:VAR_NAME:default}
    
    Args:
        text: Text containing environment variable placeholders
        
    Returns:
        Text with environment variables substituted
    """
    def replace_env(match: re.Match) -> str:
        env_spec = match.group(1)
        if ":" in env_spec:
            var_name, default = env_spec.split(":", 1)
            value = os.environ.get(var_name)
            return value if value is not None else default
        else:
            value = os.environ.get(env_spec)
            return value if value is not None else ""
    
    # Pattern matches {env:VAR_NAME} or {env:VAR_NAME:default}
    pattern = r'\{env:([^}]+)\}'
    return re.sub(pattern, replace_env, text)


def substitute_env_vars_in_config(config: Any) -> Any:
    """Recursively substitute environment variables in config.
    
    Args:
        config: Config value (dict, list, or primitive)
        
    Returns:
        Config with environment variables substituted
    """
    if isinstance(config, dict):
        return {k: substitute_env_vars_in_config(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars_in_config(item) for item in config]
    elif isinstance(config, str):
        return substitute_env_vars(config)
    else:
        return config


def load_json_with_env_substitution(filepath: Path) -> dict[str, Any]:
    """Load JSON file with environment variable substitution.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed and substituted config dict
    """
    import json
    
    content = filepath.read_text(encoding="utf-8")
    
    # Handle JSONC (remove comments)
    if filepath.suffix == ".jsonc":
        lines = content.split("\n")
        content = "\n".join(
            line for line in lines 
            if not line.strip().startswith("//")
        )
    
    # Substitute environment variables before parsing
    content = substitute_env_vars(content)
    
    return json.loads(content)


async def load_remote_config(url: str) -> dict[str, Any]:
    """Load configuration from remote .well-known/opencode URL.
    
    Args:
        url: Base URL (e.g., "https://company.com")
        
    Returns:
        Config dict from remote, or empty dict if failed
    """
    import json
    
    if not HAS_HTTPX:
        return {}
    
    # Construct well-known URL
    well_known_url = f"{url.rstrip('/')}/.well-known/opencode"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(well_known_url)
            if response.status_code == 200:
                data = response.json()
                # Extract config from well-known response
                config = data.get("config", {})
                # Add $schema if missing to prevent rewrites
                if "$schema" not in config:
                    config["$schema"] = "https://opencode.ai/config.json"
                return config
    except Exception:
        # Silently fail on any error (network, parse, etc.)
        pass
    
    return {}


async def load_remote_configs_from_env() -> dict[str, Any]:
    """Load remote configs from OPENCODE_REMOTE_CONFIG env var.
    
    Supports multiple URLs separated by commas.
    Format: "https://company1.com,https://company2.com"
    
    Returns:
        Merged config from all remote sources
    """
    import os
    
    remote_urls = os.environ.get("OPENCODE_REMOTE_CONFIG", "")
    if not remote_urls:
        return {}
    
    result: dict[str, Any] = {}
    
    for url in remote_urls.split(","):
        url = url.strip()
        if url:
            remote_config = await load_remote_config(url)
            if remote_config:
                result = deep_merge(result, remote_config)
    
    return result
