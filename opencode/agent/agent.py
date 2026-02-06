"""Agent management for OpenCode."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentMode(str, Enum):
    """Mode of agent operation."""

    PRIMARY = "primary"
    SUBAGENT = "subagent"
    ALL = "all"


class PermissionAction(str, Enum):
    """Permission action types."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PermissionRule(BaseModel):
    """A permission rule."""

    permission: str = Field(description="Permission name (tool name or '*')")
    pattern: str = Field(default="*", description="Pattern to match")
    action: PermissionAction = Field(default=PermissionAction.ALLOW, description="Action to take")


class AgentInfo(BaseModel):
    """Full agent information matching TypeScript Agent.Info."""

    name: str = Field(description="Agent name/ID")
    description: str = Field(default="", description="Agent description")
    mode: AgentMode = Field(default=AgentMode.PRIMARY, description="Agent mode")
    native: bool = Field(default=False, description="Whether this is a built-in agent")
    hidden: bool = Field(default=False, description="Whether to hide from listings")
    temperature: float | None = Field(default=None, description="Temperature setting")
    top_p: float | None = Field(default=None, description="Top-p sampling setting")
    color: str | None = Field(default=None, description="Color for UI")
    permissions: list[PermissionRule] = Field(default_factory=list, description="Permission rules")
    model: dict[str, str] | None = Field(default=None, description="Model config {modelID, providerID}")
    variant: str | None = Field(default=None, description="Model variant")
    prompt: str | None = Field(default=None, description="Custom system prompt")
    options: dict[str, Any] = Field(default_factory=dict, description="Additional options")
    steps: int | None = Field(default=None, description="Max steps for this agent")


class AgentType(str, Enum):
    """Type of agent (legacy - use AgentInfo instead)."""

    GENERAL = "general"
    BUILD = "build"
    PLAN = "plan"
    EXPLORE = "explore"
    COMPACTION = "compaction"
    TITLE = "title"
    SUMMARY = "summary"


class Agent(BaseModel):
    """An AI agent definition (legacy model)."""

    id: str = Field(description="Agent ID")
    name: str = Field(description="Agent name")
    type: AgentType = Field(description="Agent type")
    description: str = Field(description="Agent description")
    system_prompt: str = Field(description="System prompt for the agent")
    permissions: list[str] = Field(default_factory=list, description="Agent permissions (tool names)")
    model: str | None = Field(default=None, description="Model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    metadata: dict[str, Any] = Field(default_factory=dict)


def create_default_permissions() -> list[PermissionRule]:
    """Create default permission rules."""
    return [
        PermissionRule(permission="*", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="doom_loop", pattern="*", action=PermissionAction.ASK),
        PermissionRule(permission="question", pattern="*", action=PermissionAction.DENY),
        PermissionRule(permission="plan_enter", pattern="*", action=PermissionAction.DENY),
        PermissionRule(permission="plan_exit", pattern="*", action=PermissionAction.DENY),
        # Special handling for .env files
        PermissionRule(permission="read", pattern="*.env", action=PermissionAction.ASK),
        PermissionRule(permission="read", pattern="*.env.*", action=PermissionAction.ASK),
        PermissionRule(permission="read", pattern="*.env.example", action=PermissionAction.ALLOW),
    ]


def create_build_agent() -> AgentInfo:
    """Create the build agent."""
    perms = create_default_permissions()
    perms.append(PermissionRule(permission="question", pattern="*", action=PermissionAction.ALLOW))
    perms.append(PermissionRule(permission="plan_enter", pattern="*", action=PermissionAction.ALLOW))

    return AgentInfo(
        name="build",
        description="The default agent. Executes tools based on configured permissions.",
        mode=AgentMode.PRIMARY,
        native=True,
        permissions=perms,
    )


def create_plan_agent() -> AgentInfo:
    """Create the plan agent."""
    perms = create_default_permissions()
    perms.append(PermissionRule(permission="question", pattern="*", action=PermissionAction.ALLOW))
    perms.append(PermissionRule(permission="plan_exit", pattern="*", action=PermissionAction.ALLOW))
    # Edit only allowed in .opencode/plans/*.md
    perms.append(PermissionRule(permission="edit", pattern="*", action=PermissionAction.DENY))
    perms.append(PermissionRule(permission="edit", pattern=".opencode/plans/*.md", action=PermissionAction.ALLOW))

    return AgentInfo(
        name="plan",
        description="Plan mode. Disallows all edit tools except in plans directory.",
        mode=AgentMode.PRIMARY,
        native=True,
        permissions=perms,
    )


def create_general_agent() -> AgentInfo:
    """Create the general agent."""
    perms = create_default_permissions()
    perms.append(PermissionRule(permission="todoread", pattern="*", action=PermissionAction.DENY))
    perms.append(PermissionRule(permission="todowrite", pattern="*", action=PermissionAction.DENY))

    return AgentInfo(
        name="general",
        description="General-purpose agent for researching complex questions and executing multi-step tasks.",
        mode=AgentMode.SUBAGENT,
        native=True,
        permissions=perms,
    )


def create_explore_agent() -> AgentInfo:
    """Create the explore agent."""
    perms = [
        PermissionRule(permission="grep", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="glob", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="ls", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="bash", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="webfetch", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="websearch", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="codesearch", pattern="*", action=PermissionAction.ALLOW),
        PermissionRule(permission="read", pattern="*", action=PermissionAction.ALLOW),
        # Deny editing tools
        PermissionRule(permission="write", pattern="*", action=PermissionAction.DENY),
        PermissionRule(permission="edit", pattern="*", action=PermissionAction.DENY),
        PermissionRule(permission="apply_patch", pattern="*", action=PermissionAction.DENY),
        PermissionRule(permission="multiedit", pattern="*", action=PermissionAction.DENY),
    ]

    return AgentInfo(
        name="explore",
        description="Fast agent specialized for exploring codebases. Use this when you need to quickly find files by patterns, search code for keywords, or answer questions about the codebase.",
        mode=AgentMode.SUBAGENT,
        native=True,
        permissions=perms,
    )


def create_compaction_agent() -> AgentInfo:
    """Create the compaction agent (hidden, for context compaction)."""
    perms = [PermissionRule(permission="*", pattern="*", action=PermissionAction.DENY)]

    return AgentInfo(
        name="compaction",
        description="Context compaction agent (internal use only)",
        mode=AgentMode.PRIMARY,
        native=True,
        hidden=True,
        permissions=perms,
    )


def create_title_agent() -> AgentInfo:
    """Create the title agent (hidden, for generating session titles)."""
    perms = [PermissionRule(permission="*", pattern="*", action=PermissionAction.DENY)]

    return AgentInfo(
        name="title",
        description="Title generation agent (internal use only)",
        mode=AgentMode.PRIMARY,
        native=True,
        hidden=True,
        temperature=0.5,
        permissions=perms,
    )


def create_summary_agent() -> AgentInfo:
    """Create the summary agent (hidden, for generating summaries)."""
    perms = [PermissionRule(permission="*", pattern="*", action=PermissionAction.DENY)]

    return AgentInfo(
        name="summary",
        description="Summary generation agent (internal use only)",
        mode=AgentMode.PRIMARY,
        native=True,
        hidden=True,
        permissions=perms,
    )


class AgentManager:
    """Manages AI agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Register the built-in agents."""
        # Register all native agents
        agents = [
            create_build_agent(),
            create_plan_agent(),
            create_general_agent(),
            create_explore_agent(),
            create_compaction_agent(),
            create_title_agent(),
            create_summary_agent(),
        ]

        for agent in agents:
            self._agents[agent.name] = agent

    def register(self, agent: AgentInfo) -> None:
        """Register an agent."""
        self._agents[agent.name] = agent

    def get(self, agent_id: str) -> AgentInfo | None:
        """Get an agent by ID/name."""
        return self._agents.get(agent_id)

    def list_agents(self, include_hidden: bool = False) -> list[AgentInfo]:
        """List all registered agents."""
        agents = list(self._agents.values())
        if not include_hidden:
            agents = [a for a in agents if not a.hidden]
        return agents

    def list_primary_agents(self) -> list[AgentInfo]:
        """List primary (non-subagent) agents."""
        return [a for a in self.list_agents() if a.mode != AgentMode.SUBAGENT]

    def list_subagents(self) -> list[AgentInfo]:
        """List subagents only."""
        return [a for a in self.list_agents() if a.mode == AgentMode.SUBAGENT]

    def get_default_agent(self) -> AgentInfo:
        """Get the default agent (build or first primary)."""
        if "build" in self._agents:
            return self._agents["build"]

        primary = self.list_primary_agents()
        if primary:
            return primary[0]

        # Fallback to first available
        return list(self._agents.values())[0]

    def check_permission(self, agent_name: str, tool_name: str, pattern: str = "*") -> PermissionAction:
        """Check if an agent has permission for a tool.

        More specific rules override less specific ones.
        Priority: (specific tool, specific pattern) > (specific tool, *) > (*, specific pattern) > (*, *)
        """
        import fnmatch

        agent = self.get(agent_name)
        if not agent:
            return PermissionAction.DENY

        best_match: PermissionRule | None = None
        best_specificity = 0

        for rule in agent.permissions:
            # Calculate specificity: higher = more specific
            # 3: exact tool + glob pattern match
            # 2: exact tool + wildcard pattern
            # 1: wildcard tool + glob pattern match
            # 0: wildcard tool + wildcard pattern
            specificity = 0
            matches = False

            if rule.permission == tool_name:
                if fnmatch.fnmatch(pattern, rule.pattern):
                    specificity = 3
                    matches = True
                elif rule.pattern == "*":
                    specificity = 2
                    matches = True
            elif rule.permission == "*":
                if fnmatch.fnmatch(pattern, rule.pattern):
                    specificity = 1
                    matches = True
                elif rule.pattern == "*":
                    specificity = 0
                    matches = True

            if matches and specificity >= best_specificity:
                best_match = rule
                best_specificity = specificity

        return best_match.action if best_match else PermissionAction.DENY


# Global instance
_manager: AgentManager | None = None


def get_manager() -> AgentManager:
    """Get the global agent manager."""
    global _manager
    if _manager is None:
        _manager = AgentManager()
    return _manager


# Convenience functions for backward compatibility
def get_agent(agent_id: str) -> AgentInfo | None:
    """Get an agent by ID."""
    return get_manager().get(agent_id)


def list_agents(include_hidden: bool = False) -> list[AgentInfo]:
    """List all agents."""
    return get_manager().list_agents(include_hidden)


def get_default_agent() -> AgentInfo:
    """Get the default agent."""
    return get_manager().get_default_agent()
