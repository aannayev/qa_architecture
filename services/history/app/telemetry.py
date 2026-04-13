from __future__ import annotations

import logging

from fastapi import FastAPI

from app.config import Settings

logger = logging.getLogger(__name__)


def configure_telemetry(settings: Settings) -> None:
    if not settings.otlp_endpoint:
        logger.info("OTLP endpoint not set; telemetry disabled")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True))
        )
        trace.set_tracer_provider(provider)
        logger.info("OTel tracer provider configured for %s", settings.service_name)
    except Exception as exc:
        logger.warning("OTel setup failed: %s", exc)


def instrument_app(app: FastAPI) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:
        logger.debug("FastAPI instrumentation skipped: %s", exc)

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        from app.db import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except Exception as exc:
        logger.debug("SQLAlchemy instrumentation skipped: %s", exc)
