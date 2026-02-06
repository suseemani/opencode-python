"""Question routes for opencode server."""

from __future__ import annotations

from pydantic import BaseModel, Field

from opencode.question import index as question
from opencode.server.routes.index import RouteGroup


class ReplyRequest(BaseModel):
    """Reply request."""
    answers: list[list[str]] = Field(description="User answers")


def create_routes() -> RouteGroup:
    """Create question routes."""
    routes = RouteGroup("/questions")
    
    @routes.get(
        "/",
        operation_id="question.list",
        summary="List pending questions",
        description="Get all pending question requests across all sessions.",
        response_model=list[question.QuestionRequest],
    )
    async def list_questions() -> list[question.QuestionRequest]:
        """List pending questions."""
        return await question.list_pending()
    
    @routes.post(
        "/{request_id}/reply",
        operation_id="question.reply",
        summary="Reply to question request",
        description="Provide answers to a question request from the AI assistant.",
        request_model=ReplyRequest,
        response_model=bool,
    )
    async def reply_to_question(request_id: str, body: ReplyRequest) -> bool:
        """Reply to a question."""
        await question.reply(request_id, body.answers)
        return True
    
    @routes.post(
        "/{request_id}/reject",
        operation_id="question.reject",
        summary="Reject question request",
        description="Reject a question request from the AI assistant.",
        response_model=bool,
    )
    async def reject_question(request_id: str) -> bool:
        """Reject a question."""
        await question.reject(request_id)
        return True
    
    return routes


__all__ = ["create_routes"]
