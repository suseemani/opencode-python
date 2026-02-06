"""Session management for OpenCode."""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from opencode.id import create as create_id
from opencode.storage import read, write
from opencode.util import create as create_logger

log = create_logger({"service": "session"})


class MessageRole(str, Enum):
    """Role of a message in a session."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessagePart(BaseModel):
    """A part of a message (text, image, tool call, etc.)."""

    type: str = Field(description="Type of the part: text, image, tool_call, tool_result")
    content: str | None = Field(default=None, description="Content of the part")
    mime_type: str | None = Field(default=None, description="MIME type for images")
    tool_name: str | None = Field(default=None, description="Tool name for tool calls")
    tool_params: dict[str, Any] | None = Field(default=None, description="Tool parameters")
    tool_result: Any | None = Field(default=None, description="Tool execution result")


class Message(BaseModel):
    """A message in a session."""

    id: str = Field(description="Message ID")
    role: MessageRole = Field(description="Role of the message sender")
    parts: list[MessagePart] = Field(default_factory=list, description="Message parts")
    timestamp: int = Field(description="Timestamp in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SessionStatus(str, Enum):
    """Status of a session."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SessionSummary(BaseModel):
    """Summary of a session."""

    title: str | None = Field(default=None, description="Session title")
    description: str | None = Field(default=None, description="Session description")
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")


class Session(BaseModel):
    """A conversation session."""

    id: str = Field(description="Session ID")
    project_id: str = Field(description="Project ID")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    created_at: int = Field(description="Creation timestamp")
    updated_at: int = Field(description="Last update timestamp")
    summary: SessionSummary = Field(default_factory=SessionSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionManager:
    """Manages sessions and their messages."""

    def __init__(self) -> None:
        pass

    async def create(
        self,
        project_id: str,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session."""
        now = int(datetime.now().timestamp() * 1000)
        session_id = create_id("session", False)

        session = Session(
            id=session_id,
            project_id=project_id,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            summary=SessionSummary(title=title),
            metadata=metadata or {},
        )

        # Save session
        await write(["session", project_id, session_id], session.model_dump())

        log.info("Created session", {"session_id": session_id, "project_id": project_id})
        return session

    async def get(self, session_id: str, project_id: str) -> Session | None:
        """Get a session by ID."""
        try:
            data = await read(["session", project_id, session_id])
            return Session(**data)
        except Exception:
            return None

    async def update(self, session_id: str, project_id: str, updates: dict[str, Any]) -> Session | None:
        """Update a session."""
        try:
            data = await read(["session", project_id, session_id])
            data.update(updates)
            data["updated_at"] = int(datetime.now().timestamp() * 1000)
            await write(["session", project_id, session_id], data)
            return Session(**data)
        except Exception as e:
            log.error("Failed to update session", {"error": str(e), "session_id": session_id})
            return None

    async def delete(self, session_id: str, project_id: str) -> bool:
        """Delete a session."""
        from opencode.storage import remove

        try:
            await remove(["session", project_id, session_id])
            log.info("Deleted session", {"session_id": session_id})
            return True
        except Exception as e:
            log.error("Failed to delete session", {"error": str(e), "session_id": session_id})
            return False

    async def list_sessions(self, project_id: str) -> list[Session]:
        """List all sessions for a project."""
        from opencode.storage import list_keys

        try:
            keys = await list_keys(["session", project_id])
            sessions = []
            for key in keys:
                if len(key) >= 3:
                    session_id = key[2]
                    data = await read(["session", project_id, session_id])
                    sessions.append(Session(**data))
            return sorted(sessions, key=lambda s: s.created_at, reverse=True)
        except Exception as e:
            log.error("Failed to list sessions", {"error": str(e), "project_id": project_id})
            return []

    # Message management

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        parts: list[MessagePart],
    ) -> Message:
        """Add a message to a session."""
        now = int(datetime.now().timestamp() * 1000)
        message_id = create_id("message", False)

        message = Message(
            id=message_id,
            role=role,
            parts=parts,
            timestamp=now,
        )

        # Get session to find project_id
        # For now, we need to search or have project_id passed in
        # This is a simplification - real implementation would track this better

        await write(
            ["message", session_id, message_id],
            message.model_dump(),
        )

        log.info("Added message", {"session_id": session_id, "message_id": message_id})
        return message

    async def get_messages(self, session_id: str, limit: int = 100) -> list[Message]:
        """Get messages for a session."""
        from opencode.storage import list_keys

        try:
            keys = await list_keys(["message", session_id])
            messages = []
            for key in keys:
                if len(key) >= 3:
                    message_id = key[2]
                    data = await read(["message", session_id, message_id])
                    messages.append(Message(**data))
            return sorted(messages, key=lambda m: m.timestamp)[:limit]
        except Exception as e:
            log.error("Failed to get messages", {"error": str(e), "session_id": session_id})
            return []


# Global instance
_manager: SessionManager | None = None


def get_manager() -> SessionManager:
    """Get the global session manager."""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
