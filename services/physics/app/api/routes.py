from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domain.models import Difficulty
from app.domain.repository import QuestionRepository
from app.domain.schemas import (
    QuestionPublic,
    SubmitRequest,
    SubmitResult,
    TopicInfo,
)
from app.domain.service import (
    InvalidOptionError,
    QuestionNotFoundError,
    QuestionService,
)

router = APIRouter(prefix="/v1", tags=["physics"])


def get_service(session: AsyncSession = Depends(get_session)) -> QuestionService:
    return QuestionService(QuestionRepository(session))


@router.get("/topics", response_model=list[TopicInfo])
async def list_topics(service: QuestionService = Depends(get_service)) -> list[TopicInfo]:
    rows = await service.topics()
    return [TopicInfo(topic=name, question_count=count) for name, count in rows]


@router.get("/questions", response_model=list[QuestionPublic])
async def list_questions(
    topic: str | None = Query(default=None, max_length=64),
    difficulty: Difficulty | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    service: QuestionService = Depends(get_service),
) -> list[QuestionPublic]:
    questions = await service.list_questions(topic=topic, difficulty=difficulty, limit=limit)
    return [QuestionPublic.model_validate(q) for q in questions]


@router.get("/questions/{question_id}", response_model=QuestionPublic)
async def get_question(
    question_id: uuid.UUID,
    service: QuestionService = Depends(get_service),
) -> QuestionPublic:
    try:
        question = await service.get_question(question_id)
    except QuestionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return QuestionPublic.model_validate(question)


@router.post(
    "/questions/{question_id}/submit",
    response_model=SubmitResult,
    status_code=status.HTTP_200_OK,
)
async def submit_answer(
    question_id: uuid.UUID,
    body: SubmitRequest,
    service: QuestionService = Depends(get_service),
) -> SubmitResult:
    try:
        return await service.submit(question_id, body.selected_index)
    except QuestionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidOptionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
