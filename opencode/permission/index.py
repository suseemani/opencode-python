"""Permission management for opencode."""

from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import bus_event
from opencode.id import id
from opencode.project import instance
from opencode.util import log


logger = log.create({"service": "permission"})


class PermissionInfo(BaseModel):
    """Permission request information."""
    id: str = Field(description="Permission ID")
    type: str = Field(description="Permission type")
    pattern: str | list[str] | None = Field(default=None, description="Permission pattern")
    session_id: str = Field(description="Session ID")
    message_id: str = Field(description="Message ID")
    call_id: str | None = Field(default=None, description="Tool call ID")
    message: str = Field(description="Permission message")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Permission metadata")
    time: dict[str, int] = Field(description="Permission timestamps")


class PermissionReplied(BaseModel):
    """Permission replied event."""
    session_id: str = Field(description="Session ID")
    permission_id: str = Field(description="Permission ID")
    response: str = Field(description="Permission response")


Event = {
    "Updated": bus_event.BusEvent.define("permission.updated", PermissionInfo),
    "Replied": bus_event.BusEvent.define("permission.replied", PermissionReplied),
}


class RejectedError(Exception):
    """Error raised when permission is rejected."""
    def __init__(
        self,
        session_id: str,
        permission_id: str,
        call_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        reason: str | None = None,
    ):
        self.session_id = session_id
        self.permission_id = permission_id
        self.call_id = call_id
        self.metadata = metadata or {}
        self.reason = reason
        
        if reason:
            super().__init__(reason)
        else:
            super().__init__("The user rejected permission to use this specific tool call. You may try again with different parameters.")


def _to_keys(pattern: str | list[str] | None, type: str) -> list[str]:
    """Convert pattern to keys."""
    if pattern is None:
        return [type]
    if isinstance(pattern, list):
        return pattern
    return [pattern]


def _covered(keys: list[str], approved: dict[str, bool]) -> bool:
    """Check if all keys are covered by approved patterns."""
    from opencode.util import wildcard
    
    patterns = list(approved.keys())
    return all(
        any(wildcard.match(k, p) for p in patterns)
        for k in keys
    )


_pending: dict[str, dict[str, dict[str, Any]]] = {}
_approved: dict[str, dict[str, bool]] = {}


def pending() -> dict[str, dict[str, dict[str, Any]]]:
    """Get pending permissions."""
    return _pending


def list_permissions() -> list[PermissionInfo]:
    """List all pending permissions."""
    result = []
    for items in _pending.values():
        for item in items.values():
            result.append(item["info"])
    return sorted(result, key=lambda x: x.id)


async def ask(
    type: str,
    message: str,
    session_id: str,
    message_id: str,
    pattern: str | list[str] | None = None,
    call_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Ask for permission."""
    logger.info("asking", {
        "session_id": session_id,
        "message_id": message_id,
        "tool_call_id": call_id,
        "pattern": pattern,
    })
    
    approved_for_session = _approved.get(session_id, {})
    keys = _to_keys(pattern, type)
    
    if _covered(keys, approved_for_session):
        return
    
    info = PermissionInfo(
        id=id.ascending("permission"),
        type=type,
        pattern=pattern,
        session_id=session_id,
        message_id=message_id,
        call_id=call_id,
        message=message,
        metadata=metadata or {},
        time={"created": int(__import__("asyncio").get_event_loop().time() * 1000)},
    )
    
    # Create future for async handling
    import asyncio
    future: asyncio.Future[None] = asyncio.get_event_loop().create_future()
    
    if session_id not in _pending:
        _pending[session_id] = {}
    
    _pending[session_id][info.id] = {
        "info": info,
        "resolve": lambda: future.set_result(None),
        "reject": lambda e: future.set_exception(e),
    }
    
    # Publish event
    from opencode.bus import index as bus
    bus.publish(Event["Updated"], info)
    
    # Wait for response
    await future


Response = str  # "once", "always", "reject"


def respond(session_id: str, permission_id: str, response: str) -> None:
    """Respond to a permission request."""
    logger.info("response", {"session_id": session_id, "permission_id": permission_id, "response": response})
    
    match = _pending.get(session_id, {}).get(permission_id)
    if not match:
        return
    
    del _pending[session_id][permission_id]
    
    # Publish event
    from opencode.bus import index as bus
    bus.publish(Event["Replied"], PermissionReplied(
        session_id=session_id,
        permission_id=permission_id,
        response=response,
    ))
    
    if response == "reject":
        match["reject"](RejectedError(
            session_id,
            permission_id,
            match["info"].call_id,
            match["info"].metadata,
        ))
        return
    
    match["resolve"]()
    
    if response == "always":
        if session_id not in _approved:
            _approved[session_id] = {}
        
        approve_keys = _to_keys(match["info"].pattern, match["info"].type)
        for k in approve_keys:
            _approved[session_id][k] = True
        
        # Auto-approve matching pending permissions
        items = _pending.get(session_id, {})
        for item in list(items.values()):
            item_keys = _to_keys(item["info"].pattern, item["info"].type)
            if _covered(item_keys, _approved[session_id]):
                respond(
                    session_id=item["info"].session_id,
                    permission_id=item["info"].id,
                    response=response,
                )
