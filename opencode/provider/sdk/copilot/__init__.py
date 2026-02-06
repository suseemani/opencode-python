"""Provider SDK Copilot module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class CopilotConfig(BaseModel):
    """Copilot provider configuration."""
    api_key: str | None = Field(default=None, description="API key")
    base_url: str = Field(default="https://api.github.com", description="Base URL")
    model: str = Field(default="gpt-4", description="Model name")


async def chat(messages: list[dict[str, Any]], config: CopilotConfig) -> str:
    """Send a chat request to Copilot."""
    # Implement Copilot API integration
    return ""


async def complete(prompt: str, config: CopilotConfig) -> str:
    """Send a completion request to Copilot."""
    # Implement Copilot completion API
    return ""
