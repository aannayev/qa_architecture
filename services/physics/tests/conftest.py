from __future__ import annotations

import os

os.environ.setdefault("PHYSICS_SEED_ON_STARTUP", "false")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://placeholder:placeholder@localhost/placeholder"
)

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_session


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer(
        "postgres:16-alpine", username="test", password="test", dbname="test"
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5432)
        yield f"postgresql+asyncpg://test:test@{host}:{port}/test"
    finally:
        container.stop()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine(postgres_url: str):
    eng = create_async_engine(postgres_url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def session(engine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE questions RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture(loop_scope="session")
async def client(engine) -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://physics") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE questions RESTART IDENTITY CASCADE"))
