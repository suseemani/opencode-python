"""Content sharing module."""

import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "share"})


class ShareItem(BaseModel):
    """A shared item."""
    
    id: str = Field(description="Share ID")
    content: str = Field(description="Content to share")
    content_type: str = Field(default="text", description="Content type")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = Field(default=None, description="Expiration time")
    access_count: int = Field(default=0, description="Number of accesses")
    max_access: int | None = Field(default=None, description="Maximum access count")


class ShareManager:
    """Manages shared content."""
    
    def __init__(self) -> None:
        self._shares: dict[str, ShareItem] = {}
    
    def _generate_id(self, content: str) -> str:
        """Generate a share ID from content."""
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]
    
    def create_share(
        self,
        content: str,
        content_type: str = "text",
        expires_in_hours: int | None = None,
        max_access: int | None = None,
    ) -> ShareItem:
        """Create a new share."""
        share_id = self._generate_id(content)
        
        expires_at = None
        if expires_in_hours:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        item = ShareItem(
            id=share_id,
            content=content,
            content_type=content_type,
            expires_at=expires_at,
            max_access=max_access,
        )
        
        self._shares[share_id] = item
        
        log.info("Created share", {"id": share_id, "type": content_type})
        
        return item
    
    def get_share(self, share_id: str) -> ShareItem | None:
        """Get a shared item by ID."""
        item = self._shares.get(share_id)
        
        if not item:
            return None
        
        # Check expiration
        if item.expires_at and datetime.now() > item.expires_at:
            del self._shares[share_id]
            return None
        
        # Check max access
        if item.max_access and item.access_count >= item.max_access:
            del self._shares[share_id]
            return None
        
        # Increment access count
        item.access_count += 1
        
        return item
    
    def delete_share(self, share_id: str) -> bool:
        """Delete a share."""
        if share_id in self._shares:
            del self._shares[share_id]
            return True
        return False
    
    def list_shares(self) -> list[ShareItem]:
        """List all active shares."""
        now = datetime.now()
        active = []
        
        for share_id, item in list(self._shares.items()):
            # Clean up expired
            if item.expires_at and now > item.expires_at:
                del self._shares[share_id]
                continue
            
            # Clean up max access reached
            if item.max_access and item.access_count >= item.max_access:
                del self._shares[share_id]
                continue
            
            active.append(item)
        
        return active
    
    def share_file(
        self,
        file_path: str | Path,
        expires_in_hours: int | None = None,
    ) -> ShareItem | None:
        """Share a file."""
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        try:
            # Read and encode file
            content_bytes = path.read_bytes()
            content = base64.b64encode(content_bytes).decode()
            
            return self.create_share(
                content=content,
                content_type=f"file:{path.suffix}",
                expires_in_hours=expires_in_hours,
            )
        except Exception as e:
            log.error("Failed to share file", {"error": str(e), "path": str(path)})
            return None
    
    def get_share_url(self, share_id: str, base_url: str = "https://share.opencode.ai") -> str:
        """Get shareable URL for an item."""
        return f"{base_url}/s/{share_id}"


# Global instance
_manager: ShareManager | None = None


def get_manager() -> ShareManager:
    """Get the global share manager."""
    global _manager
    if _manager is None:
        _manager = ShareManager()
    return _manager
