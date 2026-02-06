"""Skill module for opencode."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

from opencode import config
from opencode.bus import index as bus
from opencode.flag import index as flag
from opencode.project import instance
from opencode.session import index as session
from opencode.util import filesystem, log

logger = log.create(service="skill")

EXTERNAL_DIRS = [".claude", ".agents"]


class SkillInfo(BaseModel):
    """Skill information."""
    name: str = Field(description="Skill name")
    description: str = Field(description="Skill description")
    location: str = Field(description="Skill location")
    content: str = Field(description="Skill content")


class InvalidError(Exception):
    """Error raised when a skill is invalid."""
    def __init__(self, path: str, message: str | None = None, issues: list | None = None) -> None:
        self.path = path
        self.message = message or f"Failed to parse skill {path}"
        self.issues = issues or []
        super().__init__(self.message)


class NameMismatchError(Exception):
    """Error raised when skill name doesn't match."""
    def __init__(self, path: str, expected: str, actual: str) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(f"Skill name mismatch: expected {expected}, got {actual}")


_skills: dict[str, SkillInfo] = {}
_dirs: set[str] = set()
_initialized = False


async def _load_skill(match: str) -> None:
    """Load a skill from a path."""
    global _skills, _dirs
    
    try:
        # Parse markdown with frontmatter
        from opencode.config import markdown
        md = await markdown.parse(match)
    except Exception as err:
        message = str(err)
        await bus.publish(
            session.Event.Error,
            {"error": {"message": f"Failed to load skill {match}: {message}"}},
        )
        logger.error("failed to load skill", {"skill": match, "err": err})
        return
    
    if not md:
        return
    
    # Validate required fields
    data = md.get("data", {})
    name = data.get("name")
    description = data.get("description")
    
    if not name or not description:
        return
    
    # Warn on duplicate skill names
    if name in _skills:
        logger.warn(
            "duplicate skill name",
            {
                "name": name,
                "existing": _skills[name].location,
                "duplicate": match,
            },
        )
    
    _dirs.add(str(Path(match).parent))
    
    _skills[name] = SkillInfo(
        name=name,
        description=description,
        location=match,
        content=md.get("content", ""),
    )


async def _scan_external(root: str, scope: str) -> None:
    """Scan external skill directories."""
    skills_dir = Path(root) / "skills"
    if not skills_dir.exists():
        return
    
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    await _load_skill(str(skill_md))
                except Exception as error:
                    logger.error(f"failed to scan {scope} skills", {"dir": root, "error": error})


async def _initialize() -> None:
    """Initialize skills."""
    global _initialized, _skills, _dirs
    
    if _initialized:
        return
    
    _skills = {}
    _dirs = set()
    
    # Scan external skill directories (.claude/skills/, .agents/skills/, etc.)
    # Load global (home) first, then project-level (so project-level overwrites)
    if not flag.OPENCODE_DISABLE_EXTERNAL_SKILLS:
        for dir_name in EXTERNAL_DIRS:
            root = Path.home() / dir_name
            if await filesystem.is_dir(str(root)):
                await _scan_external(str(root), "global")
        
        # Scan project-level external directories
        instance_dir = await instance.directory()
        worktree = await instance.worktree()
        
        current = Path(instance_dir)
        while current and current != Path(worktree).parent:
            for dir_name in EXTERNAL_DIRS:
                root = current / dir_name
                if await filesystem.is_dir(str(root)):
                    await _scan_external(str(root), "project")
            current = current.parent
    
    # Scan .opencode/skill/ directories
    try:
        config_dirs = await config.directories()
        for dir_path in config_dirs:
            skill_dir = Path(dir_path) / "skill"
            if skill_dir.exists():
                for skill_md in skill_dir.rglob("SKILL.md"):
                    await _load_skill(str(skill_md))
            
            skills_dir = Path(dir_path) / "skills"
            if skills_dir.exists():
                for skill_md in skills_dir.rglob("SKILL.md"):
                    await _load_skill(str(skill_md))
    except Exception as err:
        logger.error("failed to scan config skill directories", {"err": err})
    
    # Scan additional skill paths from config
    try:
        cfg = await config.get()
        skill_paths = cfg.get("skills", {}).get("paths", [])
        for skill_path in skill_paths:
            expanded = Path(skill_path).expanduser() if skill_path.startswith("~/") else Path(skill_path)
            resolved = expanded if expanded.is_absolute() else Path(instance_dir) / expanded
            
            if not await filesystem.is_dir(str(resolved)):
                logger.warn("skill path not found", {"path": str(resolved)})
                continue
            
            for skill_md in resolved.rglob("SKILL.md"):
                await _load_skill(str(skill_md))
    except Exception as err:
        logger.error("failed to scan additional skill paths", {"err": err})
    
    _initialized = True


async def get(name: str) -> SkillInfo | None:
    """Get a skill by name."""
    await _initialize()
    return _skills.get(name)


async def all() -> list[SkillInfo]:
    """Get all skills."""
    await _initialize()
    return list(_skills.values())


async def dirs() -> list[str]:
    """Get all skill directories."""
    await _initialize()
    return list(_dirs)


def reset() -> None:
    """Reset the skills cache."""
    global _initialized, _skills, _dirs
    _initialized = False
    _skills = {}
    _dirs = set()


__all__ = [
    "SkillInfo",
    "InvalidError",
    "NameMismatchError",
    "get",
    "all",
    "dirs",
    "reset",
]
