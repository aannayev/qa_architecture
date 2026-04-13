from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Difficulty


class QuestionPublic(BaseModel):
    """Public view — intentionally excludes correct_index and explanation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    topic: str
    difficulty: Difficulty
    prompt: str
    options: list[str]


class TopicInfo(BaseModel):
    topic: str
    question_count: int


class SubmitRequest(BaseModel):
    selected_index: Annotated[int, Field(ge=0)]


class SubmitResult(BaseModel):
    question_id: uuid.UUID
    correct: bool
    correct_index: int
    explanation: str
