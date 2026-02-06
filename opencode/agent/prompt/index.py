"""Agent prompt management."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "agent", "component": "prompt"})


class PromptTemplate(BaseModel):
    """Agent prompt template."""
    
    name: str = Field(description="Prompt name")
    content: str = Field(description="Prompt content")
    description: str = Field(default="", description="Prompt description")
    variables: list[str] = Field(default_factory=list, description="Template variables")


class PromptManager:
    """Manages agent prompts."""
    
    def __init__(self) -> None:
        self._prompts: dict[str, PromptTemplate] = {}
        self._init_default_prompts()
    
    def _init_default_prompts(self) -> None:
        """Initialize default prompts."""
        self.register(PromptTemplate(
            name="system",
            content="""You are a helpful AI coding assistant. You help users write, understand, and improve code.

When helping with code:
- Provide clear, working solutions
- Explain your reasoning
- Follow best practices and conventions
- Consider edge cases and error handling
- Use appropriate design patterns

Always be helpful, accurate, and concise.""",
            description="Default system prompt",
        ))
        
        self.register(PromptTemplate(
            name="explore",
            content="""You are a code exploration specialist. Your task is to help understand codebases.

When exploring code:
- Identify the overall architecture and patterns
- Find relevant files and functions
- Explain how different parts connect
- Highlight important concepts and abstractions
- Ask clarifying questions when needed

Be thorough but focus on what's most important.""",
            description="Explore agent prompt",
        ))
        
        self.register(PromptTemplate(
            name="build",
            content="""You are a build and compilation specialist. You help fix build errors and compilation issues.

When fixing builds:
- Identify the root cause of errors
- Check dependencies and versions
- Look at build configuration files
- Suggest specific fixes with code
- Verify the solution works

Focus on getting the build working correctly.""",
            description="Build agent prompt",
        ))
        
        self.register(PromptTemplate(
            name="plan",
            content="""You are a software architecture and planning specialist. You help design systems and plan implementations.

When planning:
- Break down complex problems into steps
- Consider different approaches and trade-offs
- Think about scalability and maintainability
- Identify potential challenges early
- Create clear, actionable plans

Help create well-thought-out designs.""",
            description="Plan agent prompt",
        ))
    
    def register(self, prompt: PromptTemplate) -> None:
        """Register a prompt template."""
        self._prompts[prompt.name] = prompt
        log.info("Registered prompt", {"name": prompt.name})
    
    def get(self, name: str) -> PromptTemplate | None:
        """Get a prompt by name."""
        return self._prompts.get(name)
    
    def render(self, name: str, **kwargs: Any) -> str:
        """Render a prompt with variables."""
        prompt = self.get(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")
        
        content = prompt.content
        for key, value in kwargs.items():
            content = content.replace(f"{{{key}}}", str(value))
        
        return content
    
    def list_prompts(self) -> list[PromptTemplate]:
        """List all registered prompts."""
        return list(self._prompts.values())
    
    def load_from_file(self, file_path: Path) -> PromptTemplate:
        """Load a prompt from a markdown file."""
        content = file_path.read_text()
        
        # Extract name from filename
        name = file_path.stem
        
        # Parse frontmatter if present
        description = ""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                # Simple frontmatter parsing
                frontmatter = parts[1]
                for line in frontmatter.split("\n"):
                    if line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                content = parts[2].strip()
        
        prompt = PromptTemplate(
            name=name,
            content=content,
            description=description,
        )
        
        self.register(prompt)
        return prompt
    
    def load_from_directory(self, dir_path: Path) -> list[PromptTemplate]:
        """Load all prompts from a directory."""
        prompts = []
        for file in dir_path.glob("*.md"):
            try:
                prompt = self.load_from_file(file)
                prompts.append(prompt)
            except Exception as e:
                log.error("Failed to load prompt", {"file": str(file), "error": str(e)})
        return prompts


# Global instance
_manager: PromptManager | None = None


def get_manager() -> PromptManager:
    """Get the global prompt manager."""
    global _manager
    if _manager is None:
        _manager = PromptManager()
    return _manager
