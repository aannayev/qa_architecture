from __future__ import annotations

import uuid

import pytest

from app.domain.models import Difficulty, Question
from app.domain.service import (
    InvalidOptionError,
    QuestionNotFoundError,
    QuestionService,
)


class FakeRepository:
    def __init__(self, questions: list[Question]) -> None:
        self._by_id = {q.id: q for q in questions}
        self._questions = questions

    async def list_(self, *, topic=None, difficulty=None, limit=20):
        items = self._questions
        if topic:
            items = [q for q in items if q.topic == topic]
        if difficulty:
            items = [q for q in items if q.difficulty == difficulty]
        return items[:limit]

    async def get(self, question_id):
        return self._by_id.get(question_id)

    async def topics(self):
        counts: dict[str, int] = {}
        for q in self._questions:
            counts[q.topic] = counts.get(q.topic, 0) + 1
        return list(counts.items())


def make_question(**overrides) -> Question:
    defaults: dict = {
        "id": uuid.uuid4(),
        "external_id": f"q-{uuid.uuid4().hex[:6]}",
        "topic": "mechanics",
        "difficulty": Difficulty.EASY,
        "prompt": "?",
        "options": ["A", "B", "C"],
        "correct_index": 1,
        "explanation": "because",
    }
    defaults.update(overrides)
    return Question(**defaults)


@pytest.fixture
def populated_service() -> tuple[QuestionService, list[Question]]:
    questions = [
        make_question(topic="mechanics", difficulty=Difficulty.EASY),
        make_question(topic="mechanics", difficulty=Difficulty.HARD),
        make_question(topic="thermodynamics", difficulty=Difficulty.MEDIUM),
    ]
    return QuestionService(FakeRepository(questions)), questions


async def test_list_filters_by_topic(populated_service):
    svc, _ = populated_service
    results = await svc.list_questions(topic="mechanics", difficulty=None, limit=20)
    assert len(results) == 2
    assert all(q.topic == "mechanics" for q in results)


async def test_list_filters_by_difficulty(populated_service):
    svc, _ = populated_service
    results = await svc.list_questions(topic=None, difficulty=Difficulty.HARD, limit=20)
    assert len(results) == 1
    assert results[0].difficulty == Difficulty.HARD


async def test_list_respects_limit(populated_service):
    svc, _ = populated_service
    results = await svc.list_questions(topic=None, difficulty=None, limit=2)
    assert len(results) == 2


async def test_get_question_missing_raises(populated_service):
    svc, _ = populated_service
    with pytest.raises(QuestionNotFoundError):
        await svc.get_question(uuid.uuid4())


async def test_submit_correct_answer(populated_service):
    svc, questions = populated_service
    q = questions[0]
    result = await svc.submit(q.id, 1)
    assert result.correct is True
    assert result.correct_index == 1
    assert result.explanation == "because"


async def test_submit_wrong_answer(populated_service):
    svc, questions = populated_service
    q = questions[0]
    result = await svc.submit(q.id, 0)
    assert result.correct is False
    assert result.correct_index == 1


async def test_submit_out_of_range_raises(populated_service):
    svc, questions = populated_service
    q = questions[0]
    with pytest.raises(InvalidOptionError):
        await svc.submit(q.id, 99)


async def test_submit_nonexistent_raises(populated_service):
    svc, _ = populated_service
    with pytest.raises(QuestionNotFoundError):
        await svc.submit(uuid.uuid4(), 0)


async def test_topics_counts(populated_service):
    svc, _ = populated_service
    topics = await svc.topics()
    as_dict = dict(topics)
    assert as_dict == {"mechanics": 2, "thermodynamics": 1}
