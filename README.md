# OpenCode Python

Python port of the OpenCode AI-powered development tool.

## Overview

This is a complete Python reimplementation of the OpenCode TypeScript codebase, maintaining the same architecture, behavior, and features while using idiomatic Python patterns.

## Installation

```bash
pip install -e .
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy opencode

# Linting
ruff check opencode
black opencode
```

## Architecture

The package follows the same modular structure as the TypeScript original:

- `acp/` - Agent Communication Protocol
- `agent/` - Agent definitions and management
- `auth/` - Authentication
- `bus/` - Event bus system
- `cli/` - Command-line interface
- `config/` - Configuration management
- `file/` - File operations
- `lsp/` - Language Server Protocol
- `mcp/` - Model Context Protocol
- `provider/` - AI provider management
- `server/` - HTTP/WebSocket server
- `session/` - Session management
- `skill/` - Skills system
- `storage/` - Data persistence
- `tool/` - AI tools
- `util/` - Utility functions

## Key Differences from TypeScript

- **Validation**: Pydantic replaces Zod
- **HTTP**: FastAPI/httpx replace Hono/fetch
- **CLI**: Typer replaces yargs
- **AI SDK**: litellm/openai/anthropic replace Vercel AI SDK
- **File Operations**: aiofiles/pathlib replace Bun APIs
- **Async**: asyncio throughout

## License

MIT
