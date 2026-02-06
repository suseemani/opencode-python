# Building and Running OpenCode Python

## 📋 Prerequisites

- **Python 3.11+** (required for modern async/await features)
- **pip** (package installer)
- **Git** (for version control)

## 🚀 Quick Start

### 1. Navigate to the Python Directory

```bash
cd python
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install with development dependencies (includes testing tools)
pip install -e ".[dev]"
```

## 🏃 Running the Application

### Option 1: Using the CLI

```bash
# Show help
opencode --help

# Run with logging
opencode --print-logs

# Run with specific log level
opencode --log-level DEBUG
```

### Option 2: Using Python Module

```bash
# Run as module
python -m opencode.cli --help

# Or directly
python -m opencode.cli.main --help
```

### Option 3: Programmatic Usage

```python
import asyncio
from opencode.tool import register_all_tools, get_registry
from opencode.tool import ToolContext

async def main():
    # Register all tools
    register_all_tools()
    
    # Create context
    context = ToolContext(session_id="test", project_dir=".")
    
    # Get registry
    registry = get_registry()
    
    # Execute a tool
    result = await registry.execute(
        "bash",
        {"command": "echo 'Hello World'"},
        context
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_opencode.py -v

# Run with coverage
pytest tests/ --cov=opencode --cov-report=html
```

## 📊 Running Examples

```bash
# Run the basic usage examples
python examples/basic_usage.py
```

This will demonstrate:
1. Basic tools usage
2. Session management
3. Agent selection
4. AI providers
5. File operations

## 🌐 Running the Server

```python
import asyncio
from opencode.server import Server

async def main():
    server = Server(host="127.0.0.1", port=8080)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

Or using uvicorn directly:

```bash
# If you have a server module
uvicorn opencode.server.server:app --reload --host 127.0.0.1 --port 8080
```

## 🔧 Development Workflow

### Code Quality Checks

```bash
# Format code with black
black opencode/ tests/

# Lint with ruff
ruff check opencode/ tests/

# Type check with mypy
mypy opencode/

# Run all checks
black --check opencode/ tests/ && ruff check opencode/ tests/ && mypy opencode/
```

### Adding New Tools

1. Create a new file in `opencode/tool/`:

```python
# opencode/tool/my_tool.py
from typing import Any
from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter

class MyTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="My custom tool",
            parameters=[
                ToolParameter(
                    name="param",
                    type="string",
                    description="A parameter",
                    required=True,
                ),
            ],
        )
    
    async def execute(self, params: dict[str, Any], context: ToolContext) -> Any:
        # Your tool logic here
        return {"result": "success"}
```

2. Register it in `opencode/tool/__init__.py`:

```python
from opencode.tool.my_tool import get_tool as get_my_tool

def register_all_tools() -> None:
    # ... existing tools ...
    registry.register(get_my_tool())
```

## 🐛 Debugging

### Enable Debug Logging

```python
import asyncio
from opencode.util import init, LogOptions, LogLevel

async def main():
    await init(LogOptions(
        print_only=True,
        level=LogLevel.DEBUG,
    ))
    # Your code here

asyncio.run(main())
```

### View Logs

```bash
# Show logs using CLI
opencode debug logs

# Or directly
python -m opencode.cli.cmd.debug logs
```

## 📦 Building for Distribution

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# This creates:
# - dist/opencode-0.1.0-py3-none-any.whl
# - dist/opencode-0.1.0.tar.gz

# Upload to PyPI (if you have credentials)
python -m twine upload dist/*
```

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY opencode/ ./opencode/

RUN pip install -e .

EXPOSE 8080

CMD ["opencode", "serve"]
```

Build and run:

```bash
docker build -t opencode .
docker run -p 8080:8080 opencode
```

## 📝 Common Issues

### Issue: Module not found

**Solution**: Make sure you're in the `python/` directory and have installed the package:

```bash
cd python
pip install -e .
```

### Issue: Type errors with mypy

**Solution**: Some type errors are expected due to complex generics. The code will still run correctly.

### Issue: Async errors

**Solution**: Make sure to use `asyncio.run()` or `await` when calling async functions.

## 🎯 Next Steps

1. **Explore the examples**: Check `examples/basic_usage.py` for usage patterns
2. **Run tests**: Execute `pytest tests/ -v` to ensure everything works
3. **Try the CLI**: Run `opencode --help` to see available commands
4. **Customize**: Add your own tools, agents, or providers

## 📚 Additional Resources

- **API Documentation**: See docstrings in the source code
- **Architecture**: See `CONVERSION_COMPLETE.md` and `FINAL_REPORT.md`
- **TypeScript Original**: Compare with `packages/opencode/src/` for reference

## ✅ Verification Checklist

Before using in production:

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] Package installed with `pip install -e .`
- [ ] Tests passing with `pytest tests/ -v`
- [ ] Examples running with `python examples/basic_usage.py`
- [ ] CLI working with `opencode --help`

## 🎉 You're Ready!

The OpenCode Python package is now ready to use. Start with the examples and explore the codebase!
