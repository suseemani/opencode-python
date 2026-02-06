"""Authentication module for opencode."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from opencode.global_path import index as global_path

OAUTH_DUMMY_KEY = "opencode-oauth-dummy-key"


class OAuthAuth(BaseModel):
    """OAuth authentication info."""
    type: Literal["oauth"] = Field(default="oauth")
    refresh: str = Field(description="Refresh token")
    access: str = Field(description="Access token")
    expires: int = Field(description="Expiration timestamp")
    account_id: str | None = Field(default=None, description="Account ID")
    enterprise_url: str | None = Field(default=None, description="Enterprise URL")


class ApiAuth(BaseModel):
    """API key authentication info."""
    type: Literal["api"] = Field(default="api")
    key: str = Field(description="API key")


class WellKnownAuth(BaseModel):
    """Well-known authentication info."""
    type: Literal["wellknown"] = Field(default="wellknown")
    key: str = Field(description="Key")
    token: str = Field(description="Token")


AuthInfo = OAuthAuth | ApiAuth | WellKnownAuth


_auth_file_path: Path | None = None


def _get_auth_file_path() -> Path:
    """Get the path to the auth file."""
    global _auth_file_path
    if _auth_file_path is None:
        _auth_file_path = Path(global_path.data) / "auth.json"
    return _auth_file_path


async def all() -> dict[str, AuthInfo]:
    """Get all authentication info."""
    filepath = _get_auth_file_path()
    
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
    
    result: dict[str, AuthInfo] = {}
    for key, value in data.items():
        try:
            auth_type = value.get("type")
            if auth_type == "oauth":
                result[key] = OAuthAuth.model_validate(value)
            elif auth_type == "api":
                result[key] = ApiAuth.model_validate(value)
            elif auth_type == "wellknown":
                result[key] = WellKnownAuth.model_validate(value)
        except Exception:
            continue
    
    return result


async def get(provider_id: str) -> AuthInfo | None:
    """Get authentication info for a provider."""
    auth = await all()
    return auth.get(provider_id)


async def set(key: str, info: AuthInfo) -> None:
    """Set authentication info for a key."""
    filepath = _get_auth_file_path()
    data = await all()
    data[key] = info
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(
            {k: v.model_dump() for k, v in data.items()},
            f,
            indent=2,
        )
    
    os.chmod(filepath, 0o600)


async def remove(key: str) -> None:
    """Remove authentication info for a key."""
    filepath = _get_auth_file_path()
    data = await all()
    
    if key in data:
        del data[key]
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(
                {k: v.model_dump() for k, v in data.items()},
                f,
                indent=2,
            )
        
        os.chmod(filepath, 0o600)


__all__ = [
    "OAuthAuth",
    "ApiAuth", 
    "WellKnownAuth",
    "AuthInfo",
    "OAUTH_DUMMY_KEY",
    "get",
    "set",
    "all",
    "remove",
]
