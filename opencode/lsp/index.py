"""LSP (Language Server Protocol) client for opencode."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import bus_event
from opencode.project import instance
from opencode.util import log


logger = log.create({"service": "lsp"})


class Range(BaseModel):
    """LSP Range."""
    start: dict[str, int] = Field(description="Start position")
    end: dict[str, int] = Field(description="End position")


class Symbol(BaseModel):
    """LSP Symbol."""
    name: str = Field(description="Symbol name")
    kind: int = Field(description="Symbol kind")
    location: dict[str, Any] = Field(description="Symbol location")


class DocumentSymbol(BaseModel):
    """LSP Document Symbol."""
    name: str = Field(description="Symbol name")
    detail: str | None = Field(default=None, description="Symbol detail")
    kind: int = Field(description="Symbol kind")
    range: Range = Field(description="Symbol range")
    selection_range: Range = Field(alias="selectionRange", description="Selection range")


class Status(BaseModel):
    """LSP status."""
    id: str = Field(description="Server ID")
    name: str = Field(description="Server name")
    root: str = Field(description="Server root")
    status: str = Field(description="Server status")


Event = {
    "Updated": bus_event.BusEvent.define("lsp.updated", dict),
}


# Symbol kinds
class SymbolKind:
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


USFUL_KINDS = [
    SymbolKind.CLASS,
    SymbolKind.FUNCTION,
    SymbolKind.METHOD,
    SymbolKind.INTERFACE,
    SymbolKind.VARIABLE,
    SymbolKind.CONSTANT,
    SymbolKind.STRUCT,
    SymbolKind.ENUM,
]


_servers: dict[str, Any] = {}
_clients: list[Any] = []


async def init() -> None:
    """Initialize LSP subsystem."""
    # Initialize LSP servers from config
    logger.info("initializing LSP")


async def status() -> list[Status]:
    """Get LSP status."""
    result = []
    for client in _clients:
        result.append(Status(
            id=client.server_id,
            name=client.server_id,
            root=str(Path(client.root).relative_to(instance.get_directory())),
            status="connected",
        ))
    return result


async def has_clients(file: str) -> bool:
    """Check if there are clients for a file."""
    ext = Path(file).suffix or file
    # Check if any server handles this extension
    # This is a simplified check
    return ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"]


async def touch_file(file: str, wait_for_diagnostics: bool = False) -> None:
    """Touch a file to trigger diagnostics."""
    logger.info("touching file", {"file": file})
    # Notify clients to open the file


async def diagnostics() -> dict[str, list[Any]]:
    """Get diagnostics from all clients."""
    results = {}
    # Collect diagnostics from all clients
    return results


async def hover(file: str, line: int, character: int) -> Any:
    """Get hover information."""
    # Request hover from appropriate client
    return None


async def workspace_symbol(query: str) -> list[Symbol]:
    """Search workspace symbols."""
    result = []
    # Search symbols from all clients
    return result[:10]


async def document_symbol(uri: str) -> list[DocumentSymbol | Symbol]:
    """Get document symbols."""
    # Request document symbols from appropriate client
    return []


async def definition(file: str, line: int, character: int) -> list[Any]:
    """Get definition locations."""
    # Request definition from appropriate client
    return []


async def references(file: str, line: int, character: int) -> list[Any]:
    """Get reference locations."""
    # Request references from appropriate client
    return []


async def implementation(file: str, line: int, character: int) -> list[Any]:
    """Get implementation locations."""
    # Request implementation from appropriate client
    return []


async def prepare_call_hierarchy(file: str, line: int, character: int) -> list[Any]:
    """Prepare call hierarchy."""
    # Request call hierarchy from appropriate client
    return []


async def incoming_calls(file: str, line: int, character: int) -> list[Any]:
    """Get incoming calls."""
    # Request incoming calls from appropriate client
    return []


async def outgoing_calls(file: str, line: int, character: int) -> list[Any]:
    """Get outgoing calls."""
    # Request outgoing calls from appropriate client
    return []


def diagnostic_pretty(diagnostic: Any) -> str:
    """Format diagnostic for display."""
    severity_map = {
        1: "ERROR",
        2: "WARN",
        3: "INFO",
        4: "HINT",
    }
    
    severity = severity_map.get(getattr(diagnostic, "severity", 1), "ERROR")
    line = getattr(diagnostic, "range", {}).get("start", {}).get("line", 0) + 1
    col = getattr(diagnostic, "range", {}).get("start", {}).get("character", 0) + 1
    message = getattr(diagnostic, "message", "")
    
    return f"{severity} [{line}:{col}] {message}"
