"""Example usage of OpenCode Python SDK."""

import asyncio
from pathlib import Path


async def example_1_basic_tools():
    """Example: Using basic tools."""
    print("=== Example 1: Basic Tools ===")

    from opencode.tool import ToolContext, get_registry
    from opencode.tool import register_all_tools

    # Register all tools
    register_all_tools()

    # Create context
    context = ToolContext(session_id="example-1", project_dir=".")

    # Get registry
    registry = get_registry()

    # Execute bash command
    print("\n1. Executing bash command:")
    result = await registry.execute("bash", {"command": "echo 'Hello from OpenCode!'"}, context)
    print(f"   stdout: {result['stdout'].strip()}")
    print(f"   exit_code: {result['exit_code']}")

    # Execute glob
    print("\n2. Finding Python files:")
    result = await registry.execute("glob", {"pattern": "*.py"}, context)
    print(f"   Found {result['total']} files")
    for f in result["files"][:3]:
        print(f"   - {f}")


async def example_2_session_management():
    """Example: Session management."""
    print("\n=== Example 2: Session Management ===")

    from opencode.session import get_manager, MessageRole, MessagePart

    manager = get_manager()

    # Create a session
    session = await manager.create(
        project_id="example-project",
        title="Example Session",
        metadata={"description": "Testing session management"},
    )
    print(f"1. Created session: {session.id}")
    print(f"   Title: {session.summary.title}")
    print(f"   Status: {session.status}")

    # Add messages
    print("\n2. Adding messages:")
    message1 = await manager.add_message(
        session.id,
        MessageRole.USER,
        [MessagePart(type="text", content="Hello, can you help me?")],
    )
    print(f"   Added user message: {message1.id}")

    message2 = await manager.add_message(
        session.id,
        MessageRole.ASSISTANT,
        [MessagePart(type="text", content="Of course! How can I assist you?")],
    )
    print(f"   Added assistant message: {message2.id}")

    # Retrieve messages
    print("\n3. Retrieving messages:")
    messages = await manager.get_messages(session.id)
    for msg in messages:
        print(f"   [{msg.role}]: {msg.parts[0].content[:50]}...")


async def example_3_agents():
    """Example: Using agents."""
    print("\n=== Example 3: Agents ===")

    from opencode.agent import get_manager

    manager = get_manager()

    # List all agents
    print("1. Available agents:")
    for agent in manager.list_agents():
        print(f"   - {agent.name} ({agent.type}): {agent.description}")

    # Get best agent for a task
    print("\n2. Agent selection:")
    task = "I need to fix a build error"
    agent = manager.get_for_task(task)
    print(f"   Task: {task}")
    print(f"   Selected agent: {agent.name}")
    print(f"   Permissions: {[p.value for p in agent.permissions]}")


async def example_4_providers():
    """Example: AI providers."""
    print("\n=== Example 4: AI Providers ===")

    from opencode.provider import get_manager, OpenAIProvider, AnthropicProvider

    manager = get_manager()

    # Register providers
    manager.register(OpenAIProvider())
    manager.register(AnthropicProvider())

    # List available models
    print("1. Available models:")
    for model in manager.list_models():
        vision = "(vision)" if model.supports_vision else ""
        print(f"   - {model.name}: {model.id} {vision}")

    print("\n2. Model selection:")
    model_id = "gpt-4o"
    provider = manager.get_by_model(model_id)
    if provider:
        print(f"   Model {model_id} uses provider: {provider.type.value}")


async def example_5_file_operations():
    """Example: File operations."""
    print("\n=== Example 5: File Operations ===")

    from opencode.file import FileManager

    # Create temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "main.py").write_text("print('Hello World')")
        Path(tmpdir, "README.md").write_text("# Example Project")
        Path(tmpdir, "src").mkdir()
        Path(tmpdir, "src", "utils.py").touch()

        manager = FileManager(tmpdir)

        # List files
        print("1. Directory listing:")
        nodes = await manager.list()
        for node in nodes:
            icon = "📁" if node.type == "directory" else "📄"
            print(f"   {icon} {node.name}")

        # Read file
        print("\n2. Reading file:")
        content = await manager.read("main.py")
        print(f"   Content: {content.content}")


async def main():
    """Run all examples."""
    print("OpenCode Python SDK Examples")
    print("=" * 50)

    try:
        await example_1_basic_tools()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        await example_2_session_management()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        await example_3_agents()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        await example_4_providers()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        await example_5_file_operations()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
