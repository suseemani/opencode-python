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


def load_opencode_config() -> dict[str, Any]:
    """Load opencode.json configuration file."""
    import json
    from pathlib import Path
    
    # Search for opencode.json in standard locations
    search_paths = [
        Path("opencode.json"),
        Path(".opencode") / "opencode.json",
        Path.home() / ".config" / "opencode" / "opencode.json",
    ]
    
    for config_path in search_paths:
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception):
                continue
    
    return {}


def parse_permission_config(perm_config: dict[str, Any] | str) -> list[PermissionRule]:
    """Parse permission configuration from opencode.json format."""
    rules = []
    
    if isinstance(perm_config, str):
        # Simple string like "allow" or "deny"
        action = PermissionAction(perm_config)
        rules.append(PermissionRule(permission="*", pattern="*", action=action))
    elif isinstance(perm_config, dict):
        # Complex permission object
        for perm_name, perm_value in perm_config.items():
            if isinstance(perm_value, str):
                # Simple action
                rules.append(PermissionRule(
                    permission=perm_name,
                    pattern="*",
                    action=PermissionAction(perm_value)
                ))
            elif isinstance(perm_value, dict):
                # Pattern-based permissions
                for pattern, action in perm_value.items():
                    rules.append(PermissionRule(
                        permission=perm_name,
                        pattern=pattern,
                        action=PermissionAction(action)
                    ))
    
    return rules


def load_agents_from_config() -> dict[str, AgentInfo]:
    """Load custom agents from opencode.json config."""
    config = load_opencode_config()
    agents = {}
    
    # Check for legacy 'agents' field first, then 'agent' field
    agent_config = config.get("agents") or config.get("agent", {})
    
    if not isinstance(agent_config, dict):
        return agents
    
    for agent_name, agent_data in agent_config.items():
        if not isinstance(agent_data, dict):
            continue
        
        # Skip disabled agents
        if agent_data.get("disable", False):
            continue
        
        # Parse mode
        mode_str = agent_data.get("mode", "primary")
        try:
            mode = AgentMode(mode_str.lower())
        except ValueError:
            mode = AgentMode.PRIMARY
        
        # Parse model config
        model_config = None
        if "model" in agent_data:
            model_str = agent_data["model"]
            if "/" in model_str:
                provider_id, model_id = model_str.split("/", 1)
                model_config = {"providerID": provider_id, "modelID": model_id}
            else:
                model_config = {"providerID": "opencode", "modelID": model_str}
        
        # Parse permissions
        permissions = []
        if "permission" in agent_data:
            permissions = parse_permission_config(agent_data["permission"])
        elif "tools" in agent_data:
            # Legacy tools format
            for tool, enabled in agent_data["tools"].items():
                action = PermissionAction.ALLOW if enabled else PermissionAction.DENY
                permissions.append(PermissionRule(permission=tool, pattern="*", action=action))
        
        # Create agent
        agent = AgentInfo(
            name=agent_name,
            description=agent_data.get("description", ""),
            mode=mode,
            native=False,
            hidden=agent_data.get("hidden", False),
            temperature=agent_data.get("temperature"),
            top_p=agent_data.get("top_p"),
            color=agent_data.get("color"),
            permissions=permissions,
            model=model_config,
            variant=agent_data.get("variant"),
            prompt=agent_data.get("prompt"),
            options=agent_data.get("options", {}),
            steps=agent_data.get("steps") or agent_data.get("maxSteps"),
        )
        
        agents[agent_name] = agent
    
    return agents


class AgentManager:
    """Manages AI agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._register_default_agents()
        self._load_config_agents()

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

    def _load_config_agents(self) -> None:
        """Load and merge custom agents from opencode.json."""
        config_agents = load_agents_from_config()
        
        for name, agent in config_agents.items():
            if name in self._agents:
                # Merge with existing agent (config overrides defaults)
                existing = self._agents[name]
                
                # Override fields if provided in config
                if agent.description:
                    existing.description = agent.description
                if agent.temperature is not None:
                    existing.temperature = agent.temperature
                if agent.top_p is not None:
                    existing.top_p = agent.top_p
                if agent.color:
                    existing.color = agent.color
                if agent.model:
                    existing.model = agent.model
                if agent.variant:
                    existing.variant = agent.variant
                if agent.prompt:
                    existing.prompt = agent.prompt
                if agent.steps is not None:
                    existing.steps = agent.steps
                if agent.mode:
                    existing.mode = agent.mode
                if agent.hidden is not None:
                    existing.hidden = agent.hidden
                if agent.permissions:
                    # Merge permissions
                    existing.permissions.extend(agent.permissions)
                if agent.options:
                    existing.options.update(agent.options)
            else:
                # Add new custom agent
                self._agents[name] = agent

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


# Agent generation prompt template
AGENT_GENERATION_PROMPT = """You are an elite AI agent architect specializing in crafting high-performance agent configurations.

When a user describes what they want an agent to do, you will:

1. **Extract Core Intent**: Identify the fundamental purpose, key responsibilities, and success criteria for the agent.

2. **Design Expert Persona**: Create a compelling expert identity that embodies deep domain knowledge relevant to the task.

3. **Architect Comprehensive Instructions**: Develop a system prompt that:
   - Establishes clear behavioral boundaries and operational parameters
   - Provides specific methodologies and best practices for task execution
   - Anticipates edge cases and provides guidance for handling them
   - Defines output format expectations when relevant

4. **Optimize for Performance**: Include decision-making frameworks, quality control mechanisms, and efficient workflow patterns.

5. **Create Identifier**: Design a concise, descriptive identifier that:
   - Uses lowercase letters, numbers, and hyphens only
   - Is typically 2-4 words joined by hyphens
   - Clearly indicates the agent's primary function
   - Avoids generic terms like "helper" or "assistant"

Your output must be a valid JSON object with exactly these fields:
{{
  "identifier": "A unique, descriptive identifier using lowercase letters, numbers, and hyphens (e.g., 'code-reviewer', 'api-docs-writer')",
  "whenToUse": "A precise, actionable description starting with 'Use this agent when...' that clearly defines the triggering conditions and use cases.",
  "systemPrompt": "The complete system prompt that will govern the agent's behavior, written in second person ('You are...', 'You will...')"
}}

Key principles for your system prompts:
- Be specific rather than generic
- Include concrete examples when they would clarify behavior
- Balance comprehensiveness with clarity
- Ensure the agent has enough context to handle variations of the core task
- Make the agent proactive in seeking clarification when needed

IMPORTANT: The following identifiers already exist and must NOT be used: {existing_agents}
"""


class GeneratedAgent(BaseModel):
    """Result of AI agent generation."""
    identifier: str
    whenToUse: str
    systemPrompt: str


async def generate_agent(
    description: str,
    model: dict[str, str] | None = None,
    temperature: float = 0.3,
) -> GeneratedAgent:
    """Generate an agent configuration using AI.
    
    Args:
        description: What the agent should do
        model: Optional model config {providerID, modelID}
        temperature: Generation temperature
        
    Returns:
        GeneratedAgent with identifier, whenToUse, and systemPrompt
    """
    from opencode.provider import get_manager as get_provider_manager, CompletionRequest, Message
    
    # Get list of existing agents to avoid duplicates
    manager = get_manager()
    existing_agents = ", ".join([a.name for a in manager.list_agents(include_hidden=True)])
    
    # Prepare system prompt
    system_prompt = AGENT_GENERATION_PROMPT.format(existing_agents=existing_agents)
    
    # Prepare user prompt
    user_prompt = f'Create an agent configuration based on this request: "{description}".\n\nReturn ONLY the JSON object, no other text, do not wrap in backticks.'
    
    # Get provider
    provider_manager = get_provider_manager()
    
    if model:
        provider_id = model.get("providerID", "opencode")
        model_id = model.get("modelID", "big-pickle")
    else:
        provider_id = "opencode"
        model_id = "big-pickle"
    
    provider = provider_manager.get(provider_id)
    if not provider:
        raise ValueError(f"Provider '{provider_id}' not found")
    
    # Create completion request
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_prompt)
    ]
    
    request = CompletionRequest(
        model=model_id,
        messages=messages,
        temperature=temperature,
        stream=False
    )
    
    # Generate agent configuration
    response = ""
    async for chunk in provider.complete(request):
        if chunk.content:
            response += chunk.content
        if chunk.finish_reason:
            break
    
    # Parse JSON response
    import json
    import re
    
    # Clean up response - remove markdown code blocks if present
    response = response.strip()
    if response.startswith("```"):
        # Extract content between code fences
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            response = match.group(1)
    
    try:
        data = json.loads(response)
        return GeneratedAgent(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse generated agent configuration: {e}\nResponse: {response}")


def generate_agent_sync(
    description: str,
    model: dict[str, str] | None = None,
    temperature: float = 0.3,
) -> GeneratedAgent:
    """Synchronous version of generate_agent."""
    import asyncio
    return asyncio.run(generate_agent(description, model, temperature))
