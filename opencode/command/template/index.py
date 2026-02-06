"""Command templates."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "command", "component": "template"})


class CommandTemplate(BaseModel):
    """A command template definition."""
    
    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    template: str = Field(description="Command template string")
    variables: list[str] = Field(default_factory=list, description="Template variables")
    example: str | None = Field(default=None, description="Usage example")


class TemplateManager:
    """Manages command templates."""
    
    def __init__(self) -> None:
        self._templates: dict[str, CommandTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self) -> None:
        """Initialize default command templates."""
        self.register(CommandTemplate(
            name="test",
            description="Run project tests",
            template="{package_manager} test",
            variables=["package_manager"],
            example="npm test",
        ))
        
        self.register(CommandTemplate(
            name="build",
            description="Build the project",
            template="{package_manager} run build",
            variables=["package_manager"],
            example="npm run build",
        ))
        
        self.register(CommandTemplate(
            name="lint",
            description="Run linter",
            template="{package_manager} run lint",
            variables=["package_manager"],
            example="npm run lint",
        ))
        
        self.register(CommandTemplate(
            name="install",
            description="Install dependencies",
            template="{package_manager} install",
            variables=["package_manager"],
            example="npm install",
        ))
        
        self.register(CommandTemplate(
            name="dev",
            description="Start development server",
            template="{package_manager} run dev",
            variables=["package_manager"],
            example="npm run dev",
        ))
    
    def register(self, template: CommandTemplate) -> None:
        """Register a command template."""
        self._templates[template.name] = template
        log.info("Registered template", {"name": template.name})
    
    def get(self, name: str) -> CommandTemplate | None:
        """Get a template by name."""
        return self._templates.get(name)
    
    def render(self, name: str, **kwargs: Any) -> str:
        """Render a template with variables."""
        template = self.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        
        result = template.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
    
    def list_templates(self) -> list[CommandTemplate]:
        """List all registered templates."""
        return list(self._templates.values())
    
    def load_from_file(self, file_path: Path) -> CommandTemplate:
        """Load a template from a file."""
        content = file_path.read_text()
        
        # Parse template file
        # Format expected:
        # # Template Name
        # Description here
        # ---
        # command template here
        # ---
        
        lines = content.split("\n")
        name = lines[0].lstrip("# ").strip() if lines else "unnamed"
        
        description = ""
        template_str = ""
        
        in_template = False
        for line in lines[1:]:
            if line.strip() == "---":
                in_template = not in_template
                continue
            
            if in_template:
                template_str += line + "\n"
            elif line.strip() and not description:
                description = line.strip()
        
        # Extract variables from template
        import re
        variables = re.findall(r"\{(\w+)\}", template_str)
        
        cmd_template = CommandTemplate(
            name=name.lower().replace(" ", "_"),
            description=description,
            template=template_str.strip(),
            variables=list(set(variables)),
        )
        
        self.register(cmd_template)
        return cmd_template


# Global instance
_manager: TemplateManager | None = None


def get_manager() -> TemplateManager:
    """Get the global template manager."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager
