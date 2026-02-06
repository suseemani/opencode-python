"""Skill tool for loading specialized skills."""

import os
from pathlib import Path
from typing import Any

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "skill"})

# Default skills directory
SKILLS_DIR = Path(".opencode") / "skill"

# Built-in skills (these match the TypeScript implementation)
BUILTIN_SKILLS = {
    "bun-file-io": {
        "description": "Use this when you are working on file operations like reading, writing, scanning, or deleting files. It summarizes the preferred file APIs and patterns used in this repo. It also notes when to use filesystem helpers for directories.",
        "location": ".opencode/skill/bun-file-io/SKILL.md",
    },
}


class SkillTool(Tool):
    """Tool for loading specialized skills that provide domain-specific instructions."""

    @property
    def definition(self) -> ToolDefinition:
        # Build available skills list
        skills_list = "\n".join([
            f"  - {name}: {info['description']}"
            for name, info in BUILTIN_SKILLS.items()
        ])

        description = f"""Load a specialized skill that provides domain-specific instructions and workflows.

The skill will inject detailed instructions, workflows, and access to bundled resources into the conversation context.

Tool output includes a `<skill_content name="...">` block with the loaded content.

Available skills:
{skills_list}"""

        return ToolDefinition(
            name="skill",
            description=description,
            parameters=[
                ToolParameter(
                    name="name",
                    type="string",
                    description="The name of the skill to load (e.g., 'bun-file-io')",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "output": {"type": "string"},
                    "title": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
        )

    def _get_skill_path(self, name: str) -> Path | None:
        """Get the path to a skill file."""
        # Check if it's a built-in skill
        if name in BUILTIN_SKILLS:
            skill_file = Path(BUILTIN_SKILLS[name]["location"])
            if skill_file.exists():
                return skill_file

        # Check in skills directory
        skill_dir = SKILLS_DIR / name
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            return skill_file

        # Check current directory
        local_skill = Path(f"{name}.md")
        if local_skill.exists():
            return local_skill

        return None

    def _list_skill_files(self, skill_dir: Path) -> list[str]:
        """List files in the skill directory (excluding SKILL.md)."""
        files = []
        if skill_dir.exists() and skill_dir.is_dir():
            for item in skill_dir.iterdir():
                if item.name != "SKILL.md":
                    files.append(str(item))
                    if len(files) >= 10:  # Limit to 10 files
                        break
        return files

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Load and return a skill's content."""
        name = params.get("name", "")

        if not name:
            available = ", ".join(BUILTIN_SKILLS.keys())
            return {
                "output": f"No skill name provided. Available skills: {available}",
                "title": "Skill error",
                "name": "",
            }

        log.info("Loading skill", {"name": name})

        skill_path = self._get_skill_path(name)

        if not skill_path:
            available = ", ".join(BUILTIN_SKILLS.keys())
            return {
                "output": f'Skill "{name}" not found. Available skills: {available}',
                "title": "Skill error",
                "name": name,
            }

        try:
            # Read the skill content
            content = skill_path.read_text(encoding="utf-8")

            # Get skill directory for file listing
            skill_dir = skill_path.parent
            base_url = skill_dir.resolve().as_uri()

            # List related files
            files = self._list_skill_files(skill_dir)
            files_xml = "\n".join([f"  <file>{f}</file>" for f in files])

            # Build output
            output = f"""<skill_content name="{name}">
# Skill: {name}

{content.strip()}

Base directory for this skill: {base_url}
Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.
Note: file list is sampled.

<skill_files>
{files_xml}
</skill_files>
</skill_content>"""

            return {
                "output": output,
                "title": f"Loaded skill: {name}",
                "name": name,
            }

        except Exception as e:
            log.error("Failed to load skill", {"name": name, "error": str(e)})
            return {
                "output": f'Failed to load skill "{name}": {e}',
                "title": "Skill error",
                "name": name,
            }


# Singleton instance
_skill_tool = SkillTool()


def get_tool() -> SkillTool:
    """Get the skill tool instance."""
    return _skill_tool
