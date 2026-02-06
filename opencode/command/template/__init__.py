"""Command template module for opencode."""

from typing import Any

from pydantic import BaseModel, Field


class Template(BaseModel):
    """Command template."""
    name: str = Field(description="Template name")
    content: str = Field(description="Template content")


async def render(template: Template, **kwargs: Any) -> str:
    """Render a template with variables."""
    content = template.content
    for key, value in kwargs.items():
        content = content.replace(f"{{{key}}}", str(value))
    return content
