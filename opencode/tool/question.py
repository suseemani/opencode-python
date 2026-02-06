"""Question tool for OpenCode."""

from typing import Any

from pydantic import BaseModel, Field

from opencode.tool import Tool, ToolContext, ToolDefinition, ToolParameter
from opencode.util import create as create_logger

log = create_logger({"service": "tool", "tool": "question"})


class Question(BaseModel):
    """A question to ask the user."""

    id: str = Field(description="Question ID")
    question: str = Field(description="The question text")
    options: list[str] | None = Field(default=None, description="Optional predefined answers")


class QuestionManager:
    """Manages pending questions for sessions."""

    def __init__(self) -> None:
        self._questions: dict[str, list[Question]] = {}
        self._answers: dict[str, dict[str, str]] = {}

    def ask(self, session_id: str, questions: list[Question]) -> None:
        """Add questions for a session."""
        if session_id not in self._questions:
            self._questions[session_id] = []
        self._questions[session_id].extend(questions)

    def get_pending(self, session_id: str) -> list[Question]:
        """Get pending questions for a session."""
        return self._questions.get(session_id, [])

    def answer(self, session_id: str, question_id: str, answer: str) -> None:
        """Record an answer to a question."""
        if session_id not in self._answers:
            self._answers[session_id] = {}
        self._answers[session_id][question_id] = answer

        # Remove from pending
        if session_id in self._questions:
            self._questions[session_id] = [
                q for q in self._questions[session_id] if q.id != question_id
            ]

    def get_answers(self, session_id: str) -> dict[str, str]:
        """Get all answers for a session."""
        return self._answers.get(session_id, {})


# Global question manager
_question_manager = QuestionManager()


class QuestionTool(Tool):
    """Tool for asking questions to the user."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="question",
            description="Ask the user one or more questions to clarify requirements or make decisions",
            parameters=[
                ToolParameter(
                    name="questions",
                    type="array",
                    description="Questions to ask the user",
                    required=True,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "object",
                        "description": "User's answers to the questions",
                    },
                },
            },
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute question tool."""
        questions_data = params.get("questions", [])

        if not questions_data:
            return {"error": "No questions provided"}

        import uuid

        questions = []
        for q_data in questions_data:
            q = Question(
                id=q_data.get("id") or str(uuid.uuid4())[:8],
                question=q_data.get("question", ""),
                options=q_data.get("options"),
            )
            questions.append(q)

        # Store questions
        session_id = context.session_id or "default"
        _question_manager.ask(session_id, questions)

        log.info("Questions asked", {"count": len(questions), "session": session_id})

        # In a real implementation, this would wait for user answers
        # For now, return pending status
        return {
            "status": "pending",
            "questions": [q.model_dump() for q in questions],
            "message": f"Asked {len(questions)} question(s). Waiting for user answers...",
        }


# Singleton instance
_question_tool = QuestionTool()


def get_tool() -> QuestionTool:
    """Get the question tool instance."""
    return _question_tool


def get_manager() -> QuestionManager:
    """Get the question manager."""
    return _question_manager
