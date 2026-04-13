from __future__ import annotations

import pytest_asyncio

from app.domain.repository import QuestionRepository
from app.domain.seed import build_seed_questions


@pytest_asyncio.fixture(loop_scope="session")
async def seeded(session):
    repo = QuestionRepository(session)
    await repo.upsert_many(build_seed_questions())
    yield


async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz(client):
    response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_list_questions_does_not_leak_correct_answer(client, seeded):
    response = await client.get("/v1/questions?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert "correct_index" not in item
        assert "explanation" not in item
        assert set(item.keys()) >= {
            "id",
            "external_id",
            "topic",
            "difficulty",
            "prompt",
            "options",
        }


async def test_list_questions_filter_by_topic(client, seeded):
    response = await client.get("/v1/questions?topic=modern")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(q["topic"] == "modern" for q in data)


async def test_list_questions_filter_by_difficulty(client, seeded):
    response = await client.get("/v1/questions?difficulty=hard")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["difficulty"] == "hard"


async def test_get_question_by_id(client, seeded):
    list_resp = await client.get("/v1/questions?topic=modern&limit=1")
    question_id = list_resp.json()[0]["id"]

    response = await client.get(f"/v1/questions/{question_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == question_id
    assert "correct_index" not in body


async def test_submit_correct_answer(client, seeded):
    list_resp = await client.get("/v1/questions?topic=modern")
    question = next(q for q in list_resp.json() if q["external_id"] == "hist-modern-001")

    response = await client.post(
        f"/v1/questions/{question['id']}/submit",
        json={"selected_index": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["correct_index"] == 2
    assert "1945" in body["explanation"]


async def test_submit_wrong_answer(client, seeded):
    list_resp = await client.get("/v1/questions?topic=modern")
    question = next(q for q in list_resp.json() if q["external_id"] == "hist-modern-001")

    response = await client.post(
        f"/v1/questions/{question['id']}/submit",
        json={"selected_index": 0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["correct_index"] == 2


async def test_submit_out_of_range_returns_422(client, seeded):
    list_resp = await client.get("/v1/questions?limit=1")
    question_id = list_resp.json()[0]["id"]

    response = await client.post(
        f"/v1/questions/{question_id}/submit",
        json={"selected_index": 99},
    )
    assert response.status_code == 422


async def test_submit_negative_index_rejected_by_pydantic(client, seeded):
    list_resp = await client.get("/v1/questions?limit=1")
    question_id = list_resp.json()[0]["id"]

    response = await client.post(
        f"/v1/questions/{question_id}/submit",
        json={"selected_index": -1},
    )
    assert response.status_code == 422


async def test_submit_nonexistent_returns_404(client):
    response = await client.post(
        "/v1/questions/00000000-0000-0000-0000-000000000000/submit",
        json={"selected_index": 0},
    )
    assert response.status_code == 404


async def test_list_topics(client, seeded):
    response = await client.get("/v1/topics")
    assert response.status_code == 200
    data = response.json()
    topics = {t["topic"] for t in data}
    assert topics == {"ancient-world", "medieval", "modern"}
