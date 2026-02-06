"""ACP (Agent Communication Protocol) implementation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ACPSessionState(BaseModel):
    """State of an ACP session."""
    
    id: str = Field(description="Session ID")
    cwd: str = Field(description="Current working directory")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    model: dict[str, str] | None = Field(default=None, description="Model configuration")
    variant: str | None = Field(default=None, description="Session variant")
    mode_id: str | None = Field(default=None, description="Mode ID")


class ACPConfig(BaseModel):
    """Configuration for ACP."""
    
    default_model: dict[str, str] | None = Field(default=None, description="Default model configuration")


class AgentConnection(Protocol):
    """Protocol for agent connections."""
    
    async def send(self, message: dict[str, Any]) -> None:
        """Send a message."""
        ...
    
    async def receive(self) -> dict[str, Any]:
        """Receive a message."""
        ...


class ACPSessionManager:
    """Manages ACP sessions."""
    
    def __init__(self) -> None:
        self._sessions: dict[str, ACPSessionState] = {}
    
    def create_session(
        self,
        session_id: str,
        cwd: str,
        model: dict[str, str] | None = None,
    ) -> ACPSessionState:
        """Create a new session."""
        session = ACPSessionState(
            id=session_id,
            cwd=cwd,
            model=model,
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> ACPSessionState | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    def list_sessions(self) -> list[ACPSessionState]:
        """List all sessions."""
        return list(self._sessions.values())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


class ACPAgent:
    """ACP Agent implementation."""
    
    def __init__(self, connection: AgentConnection, config: ACPConfig) -> None:
        self.connection = connection
        self.config = config
        self.session_manager = ACPSessionManager()
        self._running = False
    
    async def initialize(self) -> dict[str, Any]:
        """Initialize the agent."""
        self._running = True
        return {
            "status": "initialized",
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
            },
        }
    
    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming request."""
        method = request.get("method")
        
        if method == "initialize":
            return await self.initialize()
        elif method == "sessions/list":
            return {"sessions": [s.model_dump() for s in self.session_manager.list_sessions()]}
        elif method == "sessions/create":
            params = request.get("params", {})
            session = self.session_manager.create_session(
                session_id=params.get("id", "default"),
                cwd=params.get("cwd", "."),
                model=params.get("model"),
            )
            return {"session": session.model_dump()}
        else:
            return {"error": f"Unknown method: {method}"}
    
    async def run(self) -> None:
        """Main agent loop."""
        while self._running:
            try:
                request = await self.connection.receive()
                response = await self.handle_request(request)
                await self.connection.send(response)
            except Exception as e:
                await self.connection.send({"error": str(e)})
    
    def stop(self) -> None:
        """Stop the agent."""
        self._running = False


def init(config: ACPConfig) -> "ACPAgent":
    """Initialize ACP with configuration."""
    # This is a factory function that would create an agent
    # In practice, you'd pass a real connection
    from typing import Any
    
    class MockConnection:
        async def send(self, message: dict[str, Any]) -> None:
            pass
        
        async def receive(self) -> dict[str, Any]:
            return {}
    
    return ACPAgent(MockConnection(), config)


# Convenience exports
get_session_manager = ACPSessionManager
