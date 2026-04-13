from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Difficulty, Question


class QuestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_(
        self,
        *,
        topic: str | None = None,
        difficulty: Difficulty | None = None,
        limit: int = 20,
    ) -> Sequence[Question]:
        stmt = select(Question)
        if topic is not None:
            stmt = stmt.where(Question.topic == topic)
        if difficulty is not None:
            stmt = stmt.where(Question.difficulty == difficulty)
        stmt = stmt.order_by(Question.external_id).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get(self, question_id: uuid.UUID) -> Question | None:
        return await self._session.get(Question, question_id)

    async def topics(self) -> Sequence[tuple[str, int]]:
        stmt = (
            select(Question.topic, func.count(Question.id))
            .group_by(Question.topic)
            .order_by(Question.topic)
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def upsert_many(self, questions: list[Question]) -> None:
        for q in questions:
            existing = await self._session.execute(
                select(Question).where(Question.external_id == q.external_id)
            )
            row = existing.scalar_one_or_none()
            if row is None:
                self._session.add(q)
            else:
                row.topic = q.topic
                row.difficulty = q.difficulty
                row.prompt = q.prompt
                row.options = q.options
                row.correct_index = q.correct_index
                row.explanation = q.explanation
        await self._session.commit()

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Question))
        return int(result.scalar_one())
