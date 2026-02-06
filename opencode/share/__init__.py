"""Share module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class ShareInfo(BaseModel):
    """Share information."""
    id: str = Field(description="Share ID")
    url: str = Field(description="Share URL")
    content: str = Field(description="Shared content")


_shares: dict[str, ShareInfo] = {}


def init() -> None:
    """Initialize sharing."""
    pass


async def create(content: str) -> ShareInfo:
    """Create a new share."""
    import uuid
    
    share = ShareInfo(
        id=str(uuid.uuid4()),
        url=f"https://share.opencode.ai/{uuid.uuid4().hex[:8]}",
        content=content,
    )
    
    _shares[share.id] = share
    return share


async def get(share_id: str) -> ShareInfo | None:
    """Get a share by ID."""
    return _shares.get(share_id)


async def delete(share_id: str) -> bool:
    """Delete a share."""
    if share_id in _shares:
        del _shares[share_id]
        return True
    return False
