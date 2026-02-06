"""HTTP/WebSocket server for OpenCode."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from opencode.util import create as create_logger

log = create_logger({"service": "server"})


class Server:
    """HTTP/WebSocket server for OpenCode API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.app = self._create_app()
        self._clients: list[WebSocket] = []

    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            log.info("Server starting", {"host": self.host, "port": self.port})
            yield
            log.info("Server shutting down")

        app = FastAPI(
            title="OpenCode API",
            description="AI-powered development tool API",
            version="0.1.0",
            lifespan=lifespan,
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self._add_routes(app)

        return app

    def _add_routes(self, app: FastAPI) -> None:
        """Add API routes."""

        @app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        @app.get("/api/version")
        async def version() -> dict[str, str]:
            return {"version": "0.1.0"}

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            self._clients.append(websocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    # Handle incoming messages
                    await self._handle_websocket_message(websocket, data)
            except Exception:
                pass
            finally:
                self._clients.remove(websocket)

    async def _handle_websocket_message(
        self, websocket: WebSocket, data: dict[str, Any]
    ) -> None:
        """Handle a WebSocket message."""
        msg_type = data.get("type")
        log.info("WebSocket message", {"type": msg_type})

        if msg_type == "ping":
            await websocket.send_json({"type": "pong"})

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected WebSocket clients."""
        disconnected = []
        for client in self._clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            if client in self._clients:
                self._clients.remove(client)

    def run(self) -> None:
        """Run the server."""
        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)

    async def start(self) -> None:
        """Start the server (async version)."""
        import uvicorn

        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
