"""Question module for opencode."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from opencode.bus import index as bus
from opencode.bus.bus_event import BusEvent
from opencode.id import id as identifier
from opencode.project import instance
from opencode.util import log

logger = log.create(service="question")


class QuestionOption(BaseModel):
    """Question option."""
    label: str = Field(description="Display text (1-5 words, concise)")
    description: str = Field(description="Explanation of choice")


class QuestionInfo(BaseModel):
    """Question info."""
    question: str = Field(description="Complete question")
    header: str = Field(description="Very short label (max 30 chars)")
    options: list[QuestionOption] = Field(description="Available choices")
    multiple: bool = Field(default=False, description="Allow selecting multiple choices")
    custom: bool = Field(default=True, description="Allow typing a custom answer")


class QuestionToolInfo(BaseModel):
    """Tool info for question."""
    message_id: str = Field(alias="messageID")
    call_id: str = Field(alias="callID")


class QuestionRequest(BaseModel):
    """Question request."""
    id: str = Field(description="Question ID")
    session_id: str = Field(alias="sessionID", description="Session ID")
    questions: list[QuestionInfo] = Field(description="Questions to ask")
    tool: QuestionToolInfo | None = Field(default=None)


QuestionAnswer = list[str]


class QuestionReply(BaseModel):
    """Question reply."""
    answers: list[QuestionAnswer] = Field(
        description="User answers in order of questions (each answer is an array of selected labels)"
    )


class RepliedEvent(BaseModel):
    """Question replied event."""
    session_id: str = Field(alias="sessionID")
    request_id: str = Field(alias="requestID")
    answers: list[QuestionAnswer]


class RejectedEvent(BaseModel):
    """Question rejected event."""
    session_id: str = Field(alias="sessionID")
    request_id: str = Field(alias="requestID")


Event = {
    "Asked": BusEvent.define("question.asked", QuestionRequest),
    "Replied": BusEvent.define("question.replied", RepliedEvent),
    "Rejected": BusEvent.define("question.rejected", RejectedEvent),
}


class _PendingEntry:
    """Pending question entry."""
    def __init__(
        self,
        info: QuestionRequest,
        resolve: asyncio.Future[list[QuestionAnswer]],
    ):
        self.info = info
        self.resolve = resolve


_pending: dict[str, _PendingEntry] = {}


class RejectedError(Exception):
    """Error raised when a question is rejected."""
    def __init__(self) -> None:
        super().__init__("The user dismissed this question")


async def ask(
    session_id: str,
    questions: list[QuestionInfo],
    tool: dict[str, str] | None = None,
) -> list[QuestionAnswer]:
    """Ask the user questions."""
    id = identifier.ascending("question")
    
    logger.info("asking", {"id": id, "questions": len(questions)})
    
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    
    info = QuestionRequest(
        id=id,
        session_id=session_id,
        questions=questions,
        tool=QuestionToolInfo.model_validate(tool) if tool else None,
    )
    
    _pending[id] = _PendingEntry(info, future)
    
    await bus.publish(Event["Asked"], info)
    
    return await future


async def reply(request_id: str, answers: list[QuestionAnswer]) -> None:
    """Reply to a question request."""
    existing = _pending.get(request_id)
    if not existing:
        logger.warn("reply for unknown request", {"request_id": request_id})
        return
    
    del _pending[request_id]
    
    logger.info("replied", {"request_id": request_id, "answers": answers})
    
    await bus.publish(
        Event["Replied"],
        RepliedEvent(
            session_id=existing.info.session_id,
            request_id=existing.info.id,
            answers=answers,
        ),
    )
    
    existing.resolve.set_result(answers)


async def reject(request_id: str) -> None:
    """Reject a question request."""
    existing = _pending.get(request_id)
    if not existing:
        logger.warn("reject for unknown request", {"request_id": request_id})
        return
    
    del _pending[request_id]
    
    logger.info("rejected", {"request_id": request_id})
    
    await bus.publish(
        Event["Rejected"],
        RejectedEvent(
            session_id=existing.info.session_id,
            request_id=existing.info.id,
        ),
    )
    
    existing.resolve.set_exception(RejectedError())


async def list_pending() -> list[QuestionRequest]:
    """List all pending questions."""
    return [entry.info for entry in _pending.values()]


__all__ = [
    "QuestionOption",
    "QuestionInfo",
    "QuestionRequest",
    "QuestionReply",
    "QuestionAnswer",
    "RejectedError",
    "ask",
    "reply",
    "reject",
    "list_pending",
    "Event",
]
