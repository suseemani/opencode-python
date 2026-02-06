"""Agent prompt module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    """Agent prompt."""
    name: str = Field(description="Prompt name")
    content: str = Field(description="Prompt content")
    variables: dict[str, Any] = Field(default_factory=dict, description="Prompt variables")


async def load(name: str) -> Prompt | None:
    """Load a prompt by name."""
    return None


async def render(prompt: Prompt, **kwargs: Any) -> str:
    """Render a prompt with variables."""
    content = prompt.content
    for key, value in {**prompt.variables, **kwargs}.items():
        content = content.replace(f"{{{key}}}", str(value))
    return content
