"""Tests for OpenCode Python SDK."""

import pytest
import asyncio
from pathlib import Path

# Test ID generation
def test_id_creation():
    from opencode.id import create, ascending, descending

    id1 = ascending("session")
    assert id1.startswith("ses_")

    id2 = ascending("session")
    assert id1 != id2

    id3 = descending("session")
    assert id3.startswith("ses_")


# Test environment management
def test_env_manager():
    from opencode.env import EnvManager

    env = EnvManager()
    env.set("TEST_VAR", "test_value")
    assert env.get("TEST_VAR") == "test_value"

    env.remove("TEST_VAR")
    assert env.get("TEST_VAR") is None


# Test logging
@pytest.mark.asyncio
async def test_logger():
    from opencode.util import create, LogOptions, init, LogLevel

    await init(LogOptions(print_only=True, level=LogLevel.DEBUG))
    logger = create({"service": "test"})
    logger.info("Test message")


# Test storage
@pytest.mark.asyncio
async def test_storage():
    from opencode.storage import write, read, remove

    test_data = {"key": "value", "number": 42}
    await write(["test", "data"], test_data)

    result = await read(["test", "data"])
    assert result["key"] == "value"
    assert result["number"] == 42

    await remove(["test", "data"])


# Test event bus
def test_event_bus():
    from opencode.bus import get_bus

    bus = get_bus()
    events = []

    def handler(event):
        events.append(event)

    unsub = bus.subscribe("test.event", handler)
    bus.publish("test.event", {"data": "test"})

    assert len(events) == 1
    assert events[0]["properties"]["data"] == "test"

    unsub()


# Test tools
@pytest.mark.asyncio
async def test_bash_tool():
    from opencode.tool.bash import get_tool
    from opencode.tool import ToolContext

    tool = get_tool()
    context = ToolContext(session_id="test", project_dir=".")

    result = await tool.execute({"command": "echo hello", "timeout": 5000}, context)

    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]


@pytest.mark.asyncio
async def test_read_tool(tmp_path):
    from opencode.tool.read import get_tool
    from opencode.tool import ToolContext

    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    tool = get_tool()
    context = ToolContext(session_id="test", project_dir=str(tmp_path))

    result = await tool.execute({"path": "test.txt"}, context)

    assert result["type"] == "text"
    assert "Hello, World!" in result["content"]


@pytest.mark.asyncio
async def test_write_tool(tmp_path):
    from opencode.tool.write import get_tool
    from opencode.tool import ToolContext

    tool = get_tool()
    context = ToolContext(session_id="test", project_dir=str(tmp_path))

    result = await tool.execute({"path": "output.txt", "content": "Test content"}, context)

    assert result["success"] is True
    assert (tmp_path / "output.txt").read_text() == "Test content"


@pytest.mark.asyncio
async def test_glob_tool(tmp_path):
    from opencode.tool.glob import get_tool
    from opencode.tool import ToolContext

    # Create test files
    (tmp_path / "file1.py").touch()
    (tmp_path / "file2.py").touch()
    (tmp_path / "file.txt").touch()

    tool = get_tool()
    context = ToolContext(session_id="test", project_dir=str(tmp_path))

    result = await tool.execute({"pattern": "*.py"}, context)

    assert len(result["files"]) == 2


# Test session management
@pytest.mark.asyncio
async def test_session_manager():
    from opencode.session import get_manager, SessionStatus

    manager = get_manager()

    # Create session
    session = await manager.create(
        project_id="test_project",
        title="Test Session",
    )

    assert session.project_id == "test_project"
    assert session.status == SessionStatus.ACTIVE

    # Get session
    retrieved = await manager.get(session.id, session.project_id)
    assert retrieved is not None
    assert retrieved.id == session.id


# Test agent management
def test_agent_manager():
    from opencode.agent import get_manager, AgentType

    manager = get_manager()

    # Get general agent
    agent = manager.get("general")
    assert agent is not None
    assert agent.type == AgentType.GENERAL

    # Get best agent for task
    build_agent = manager.get_for_task("fix build error")
    assert build_agent.type == AgentType.BUILD


# Test provider management
def test_provider_manager():
    from opencode.provider import get_manager, ProviderType, OpenAIProvider, AnthropicProvider

    manager = get_manager()

    # Register providers
    manager.register(OpenAIProvider())
    manager.register(AnthropicProvider())

    # List models
    models = manager.list_models()
    assert len(models) > 0

    # Get provider by model
    provider = manager.get_by_model("gpt-4o")
    assert provider is not None
    assert provider.type == ProviderType.OPENAI


# Test file operations
@pytest.mark.asyncio
async def test_file_manager(tmp_path):
    from opencode.file import FileManager

    # Create test files
    (tmp_path / "test.txt").write_text("Test content")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file.py").touch()

    manager = FileManager(str(tmp_path))

    # List directory
    nodes = await manager.list()
    assert len(nodes) >= 2

    # Read file
    content = await manager.read("test.txt")
    assert content.type == "text"
    assert "Test content" in content.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
