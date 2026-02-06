"""ACP (Agent Communication Protocol) module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class AcpMessage(BaseModel):
    """ACP message."""
    type: str = Field(description="Message type")
    payload: dict[str, Any] = Field(default_factory=dict, description="Message payload")


async def send(message: AcpMessage) -> None:
    """Send an ACP message."""
    pass


async def receive() -> AcpMessage | None:
    """Receive an ACP message."""
    return None
