# OpenCode Python Conversion Summary

This document summarizes the TypeScript to Python conversion of the OpenCode project.

## Conversion Overview

- **Original TypeScript**: ~29,000 lines across 209 files in `packages/opencode/`
- **Python Files Created**: 29 files covering core infrastructure
- **Conversion Status**: Core infrastructure complete, demonstrating patterns for remaining modules

## Files Converted

### Project Configuration
- `pyproject.toml` - Python project configuration with dependencies
- `README.md` - Package documentation

### Core Utility Modules (`opencode/util/`)
1. `abort.py` - Abort/timeout utilities for async operations
2. `defer.py` - Deferred execution context managers
3. `filesystem.py` - Async filesystem operations
4. `lock.py` - File and async locking mechanisms
5. `log.py` - Structured logging with Pydantic models
6. `queue.py` - Async queue implementation
7. `signal.py` - Signal handling utilities
8. `timeout.py` - Timeout wrappers for async operations

### ID Generation (`opencode/id/`)
1. `id.py` - ID generation with prefixes and timestamps

### Environment (`opencode/env/`)
1. `index.py` - Environment variable management with instance isolation

### Global Paths (`opencode/global/`)
1. `index.py` - XDG Base Directory paths and cache management

### Event Bus (`opencode/bus/`)
1. `bus_event.py` - Event definitions using Pydantic
2. `index.py` - Event bus implementation for pub/sub

### Storage (`opencode/storage/`)
1. `storage.py` - JSON file-based persistence with migrations

### File Operations (`opencode/file/`)
1. `index.py` - File reading, listing, searching with git integration

### Tool Framework (`opencode/tool/`)
1. `tool.py` - Abstract base class for AI tools with registry

### Server (`opencode/server/`)
1. `server.py` - FastAPI HTTP/WebSocket server

### CLI (`opencode/cli/`)
1. `main.py` - Typer-based CLI entry point

## Key Conversion Patterns

### 1. TypeScript Namespaces → Python Modules
**TypeScript:**
```typescript
export namespace Log {
  export function create(tags?: Record<string, any>) { ... }
}
```

**Python:**
```python
def create(tags: dict[str, Any] | None = None) -> Logger:
    ...
```

### 2. Zod Schemas → Pydantic Models
**TypeScript:**
```typescript
export const Info = z.object({
  path: z.string(),
  added: z.number().int(),
  removed: z.number().int(),
}).meta({ ref: "File" })
```

**Python:**
```python
class FileInfo(BaseModel):
    path: str = Field(description="File path")
    added: int = Field(description="Number of lines added")
    removed: int = Field(description="Number of lines removed")
```

### 3. Bun APIs → Python Standard Library
**TypeScript:**
```typescript
await Bun.file(path).text()
await Bun.write(path, content)
```

**Python:**
```python
Path(path).read_text()
Path(path).write_text(content)
```

### 4. Async/Await → asyncio
Maintained async/await pattern throughout, using `asyncio` for:
- Task management
- Event loops
- Concurrent execution

### 5. TypeScript Enums → Python Enums
**TypeScript:**
```typescript
export const Level = z.enum(["DEBUG", "INFO", "WARN", "ERROR"])
```

**Python:**
```python
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
```

## Dependency Mappings

| TypeScript | Python |
|------------|--------|
| zod | pydantic |
| bun (Bun.file, Bun.Glob) | pathlib, aiofiles |
| yargs | typer, click |
| hono | fastapi |
| fetch / axios | httpx, aiohttp |
| Vercel AI SDK | litellm, openai, anthropic |
| diff (npm) | diff-match-patch |
| fuzzysort | fuzzywuzzy |
| tree-sitter (WASM) | tree-sitter |
| vscode-jsonrpc | pygls |

## Project Structure

```
python/
├── pyproject.toml          # Project configuration
├── README.md               # Documentation
└── opencode/
    ├── __init__.py         # Package init
    ├── id/                 # ID generation
    ├── env/                # Environment management
    ├── global_/            # Global paths
    ├── util/               # Utilities
    ├── bus/                # Event bus
    ├── storage/            # Persistence
    ├── file/               # File operations
    ├── tool/               # Tool framework
    ├── server/             # HTTP/WebSocket server
    └── cli/                # CLI entry point
```

## Remaining Work

To complete the full conversion (~29K lines), the following modules would need to be converted:

### Session Management (`session/`)
- Session lifecycle (create, update, delete)
- Message handling (MessageV2 format)
- LLM interaction via `ai` SDK
- Token usage tracking
- Session forking and compaction

### Agent System (`agent/`)
- Agent definitions with permissions
- Built-in agents (build, plan, general, explore, etc.)
- Agent generation via LLM

### Provider System (`provider/`)
- Multi-provider AI support (20+ providers)
- Model discovery and loading
- Authentication management

### Tools (`tool/` - 24 tools)
- bash.ts - Shell command execution
- read.ts - File reading
- write.ts - File writing
- edit.ts - Code editing (21K+ lines)
- grep.ts - Code search
- glob.ts - File globbing
- ls.ts - Directory listing
- webfetch.ts - Web scraping
- websearch.ts - Web search
- And 15+ more tools

### MCP Integration (`mcp/`)
- Model Context Protocol client
- OAuth authentication

### LSP Integration (`lsp/`)
- Language Server Protocol client

### Configuration (`config/`)
- Multi-layer config loading
- JSON with comments support
- Agent/command/skill loading from markdown

### Additional Modules
- `permission/` - Permission system
- `project/` - Project management
- `question/` - Question system
- `scheduler/` - Task scheduler
- `skill/` - Skills system
- `snapshot/` - Code snapshots
- `shell/` - Shell integration
- `worktree/` - Git worktree management

## Usage

```bash
# Install the package
pip install -e python/

# Run the CLI
opencode --help

# Development
pip install -e "python/[dev]"
pytest
mypy python/opencode
```

## Notes

1. **Type Safety**: Full type annotations throughout using Pydantic and mypy
2. **Async**: All I/O operations are async using `asyncio`
3. **Testing**: pytest configured in pyproject.toml
4. **Code Quality**: black, ruff, and mypy configured
5. **Documentation**: Docstrings follow Python conventions

## Next Steps

To continue the conversion:
1. Convert remaining modules following the established patterns
2. Add comprehensive tests
3. Implement the AI provider integrations
4. Add the remaining 24 tools
5. Implement session and agent management
6. Add WebSocket event handlers
7. Complete CLI commands
