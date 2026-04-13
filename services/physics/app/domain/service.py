from __future__ import annotations

import uuid

from app.domain.models import Difficulty, Question
from app.domain.repository import QuestionRepository
from app.domain.schemas import SubmitResult


class QuestionNotFoundError(Exception):
    def __init__(self, question_id: uuid.UUID) -> None:
        super().__init__(f"question {question_id} not found")
        self.question_id = question_id


class InvalidOptionError(Exception):
    def __init__(self, selected_index: int, option_count: int) -> None:
        super().__init__(
            f"selected_index={selected_index} is out of range (0..{option_count - 1})"
        )
        self.selected_index = selected_index
        self.option_count = option_count


class QuestionService:
    def __init__(self, repo: QuestionRepository) -> None:
        self._repo = repo

    async def list_questions(
        self,
        *,
        topic: str | None,
        difficulty: Difficulty | None,
        limit: int,
    ) -> list[Question]:
        return list(await self._repo.list_(topic=topic, difficulty=difficulty, limit=limit))

    async def get_question(self, question_id: uuid.UUID) -> Question:
        q = await self._repo.get(question_id)
        if q is None:
            raise QuestionNotFoundError(question_id)
        return q

    async def submit(self, question_id: uuid.UUID, selected_index: int) -> SubmitResult:
        question = await self.get_question(question_id)
        if selected_index >= len(question.options):
            raise InvalidOptionError(selected_index, len(question.options))
        return SubmitResult(
            question_id=question.id,
            correct=selected_index == question.correct_index,
            correct_index=question.correct_index,
            explanation=question.explanation,
        )

    async def topics(self) -> list[tuple[str, int]]:
        return list(await self._repo.topics())
