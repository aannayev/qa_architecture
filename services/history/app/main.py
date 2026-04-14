from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import get_settings
from app.db import SessionLocal
from app.domain.repository import QuestionRepository
from app.domain.seed import build_seed_questions
from app.feature_flags import FeatureFlags
from app.health import router as health_router
from app.telemetry import configure_telemetry, instrument_app

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    configure_telemetry(settings)

    app.state.feature_flags = FeatureFlags(settings)

    if settings.seed_on_startup:
        try:
            async with SessionLocal() as session:
                repo = QuestionRepository(session)
                if await repo.count() == 0:
                    await repo.upsert_many(build_seed_questions())
                    logger.info("Seeded history questions on startup")
        except Exception as exc:
            logger.warning("Startup seed skipped: %s", exc)

    try:
        yield
    finally:
        app.state.feature_flags.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="History Service",
        version="0.1.0",
        description="Subject service — history questions for the exam platform.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(api_router)
    instrument_app(app)
    return app


app = create_app()
