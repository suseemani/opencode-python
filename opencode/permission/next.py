"""Next-generation permission management for opencode."""

import os
from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import bus_event
from opencode.id import id
from opencode.project import instance
from opencode.storage import storage
from opencode.util import log
from opencode.util import wildcard


logger = log.create({"service": "permission"})


class Action:
    """Permission action types."""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class Rule(BaseModel):
    """Permission rule."""
    permission: str = Field(description="Permission name")
    pattern: str = Field(default="*", description="Pattern to match")
    action: str = Field(default="ask", description="Action to take")


class Request(BaseModel):
    """Permission request."""
    id: str = Field(description="Request ID")
    session_id: str = Field(description="Session ID")
    permission: str = Field(description="Permission name")
    patterns: list[str] = Field(description="Patterns to check")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Request metadata")
    always: list[str] = Field(default_factory=list, description="Patterns to always approve")
    tool: dict[str, str] | None = Field(default=None, description="Tool information")


class Reply:
    """Permission reply types."""
    ONCE = "once"
    ALWAYS = "always"
    REJECT = "reject"


class RequestReplied(BaseModel):
    """Permission request replied event."""
    session_id: str = Field(description="Session ID")
    request_id: str = Field(description="Request ID")
    reply: str = Field(description="Reply type")


Event = {
    "Asked": bus_event.BusEvent.define("permission.asked", Request),
    "Replied": bus_event.BusEvent.define("permission.replied", RequestReplied),
}


class RejectedError(Exception):
    """User rejected without message - halts execution."""
    def __init__(self):
        super().__init__("The user rejected permission to use this specific tool call.")


class CorrectedError(Exception):
    """User rejected with message - continues with guidance."""
    def __init__(self, message: str):
        super().__init__(f"The user rejected permission to use this specific tool call with the following feedback: {message}")


class DeniedError(Exception):
    """Auto-rejected by config rule - halts execution."""
    def __init__(self, ruleset: list[Rule]):
        self.ruleset = ruleset
        super().__init__(f"The user has specified a rule which prevents you from using this specific tool call. Here are some of the relevant rules {ruleset}")


def expand(pattern: str) -> str:
    """Expand environment variables and home directory in pattern."""
    if pattern.startswith("~/"):
        return os.path.expanduser(pattern)
    if pattern == "~":
        return os.path.expanduser("~")
    if pattern.startswith("$HOME/"):
        return os.path.expanduser(pattern.replace("$HOME", "~", 1))
    if pattern.startswith("$HOME"):
        return os.path.expanduser(pattern.replace("$HOME", "~", 1))
    return pattern


def from_config(permission: dict[str, Any]) -> list[Rule]:
    """Convert config permission to ruleset."""
    ruleset = []
    for key, value in permission.items():
        if isinstance(value, str):
            ruleset.append(Rule(permission=key, action=value, pattern="*"))
        elif isinstance(value, dict):
            for pattern, action in value.items():
                ruleset.append(Rule(permission=key, pattern=expand(pattern), action=action))
    return ruleset


def merge(*rulesets: list[Rule]) -> list[Rule]:
    """Merge multiple rulesets."""
    result = []
    for ruleset in rulesets:
        result.extend(ruleset)
    return result


def evaluate(permission: str, pattern: str, *rulesets: list[Rule]) -> Rule:
    """Evaluate permission against rulesets."""
    merged = merge(*rulesets)
    logger.info("evaluate", {"permission": permission, "pattern": pattern, "ruleset": merged})
    
    # Find last matching rule
    for rule in reversed(merged):
        if wildcard.match(permission, rule.permission) and wildcard.match(pattern, rule.pattern):
            return rule
    
    return Rule(action="ask", permission=permission, pattern="*")


EDIT_TOOLS = ["edit", "write", "patch", "multiedit"]


def disabled(tools: list[str], ruleset: list[Rule]) -> set[str]:
    """Get set of disabled tools."""
    result = set()
    for tool in tools:
        permission = "edit" if tool in EDIT_TOOLS else tool
        
        for rule in reversed(ruleset):
            if wildcard.match(permission, rule.permission):
                if rule.pattern == "*" and rule.action == "deny":
                    result.add(tool)
                break
    
    return result


_pending: dict[str, dict[str, Any]] = {}
_approved: list[Rule] = []


async def _get_state() -> tuple[dict[str, Any], list[Rule]]:
    """Get permission state."""
    global _approved
    
    if not _approved:
        # Load from storage
        project_id = instance.get_project().id
        stored = await storage.read(list[Rule], ["permission", project_id]).catch(lambda: [])
        _approved = stored or []
    
    return _pending, _approved


async def ask(
    permission: str,
    patterns: list[str],
    session_id: str,
    always: list[str],
    ruleset: list[Rule],
    metadata: dict[str, Any] | None = None,
    tool: dict[str, str] | None = None,
    request_id: str | None = None,
) -> None:
    """Ask for permission using ruleset."""
    s_pending, s_approved = await _get_state()
    
    for pattern in patterns or []:
        rule = evaluate(permission, pattern, ruleset, s_approved)
        logger.info("evaluated", {"permission": permission, "pattern": pattern, "action": rule.action})
        
        if rule.action == "deny":
            raise DeniedError([r for r in ruleset if wildcard.match(permission, r.permission)])
        
        if rule.action == "ask":
            req_id = request_id or id.ascending("permission")
            
            import asyncio
            future: asyncio.Future[None] = asyncio.get_event_loop().create_future()
            
            info = Request(
                id=req_id,
                session_id=session_id,
                permission=permission,
                patterns=patterns,
                metadata=metadata or {},
                always=always,
                tool=tool,
            )
            
            s_pending[req_id] = {
                "info": info,
                "resolve": lambda: future.set_result(None),
                "reject": lambda e: future.set_exception(e),
            }
            
            # Publish event
            from opencode.bus import index as bus
            bus.publish(Event["Asked"], info)
            
            await future
            return
        
        if rule.action == "allow":
            continue


async def reply(
    request_id: str,
    reply: str,
    message: str | None = None,
) -> None:
    """Reply to a permission request."""
    s_pending, s_approved = await _get_state()
    
    existing = s_pending.get(request_id)
    if not existing:
        return
    
    del s_pending[request_id]
    
    # Publish event
    from opencode.bus import index as bus
    bus.publish(Event["Replied"], RequestReplied(
        session_id=existing["info"].session_id,
        request_id=existing["info"].id,
        reply=reply,
    ))
    
    if reply == "reject":
        if message:
            existing["reject"](CorrectedError(message))
        else:
            existing["reject"](RejectedError())
        
        # Reject all other pending permissions for this session
        session_id = existing["info"].session_id
        for req_id, pending in list(s_pending.items()):
            if pending["info"].session_id == session_id:
                del s_pending[req_id]
                bus.publish(Event["Replied"], RequestReplied(
                    session_id=pending["info"].session_id,
                    request_id=pending["info"].id,
                    reply="reject",
                ))
                pending["reject"](RejectedError())
        return
    
    if reply == "once":
        existing["resolve"]()
        return
    
    if reply == "always":
        for pattern in existing["info"].always:
            s_approved.append(Rule(
                permission=existing["info"].permission,
                pattern=pattern,
                action="allow",
            ))
        
        existing["resolve"]()
        
        # Check other pending permissions
        session_id = existing["info"].session_id
        for req_id, pending in list(s_pending.items()):
            if pending["info"].session_id != session_id:
                continue
            
            ok = all(
                evaluate(pending["info"].permission, pattern, s_approved).action == "allow"
                for pattern in pending["info"].patterns
            )
            
            if not ok:
                continue
            
            del s_pending[req_id]
            bus.publish(Event["Replied"], RequestReplied(
                session_id=pending["info"].session_id,
                request_id=pending["info"].id,
                reply="always",
            ))
            pending["resolve"]()
        
        # TODO: Save to storage when UI is available
        # await storage.write(["permission", instance.get_project().id], s_approved)


async def list_requests() -> list[Request]:
    """List all pending permission requests."""
    s_pending, _ = await _get_state()
    return [item["info"] for item in s_pending.values()]
