"""OpenTelemetry and Prometheus instrumentation setup."""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    """Initialize OpenTelemetry tracing and Prometheus metrics."""
    # Prometheus metrics
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # OpenTelemetry — only in production to avoid dev noise
    if settings.is_production:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": settings.otel_service_name})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)

            FastAPIInstrumentor.instrument_app(app)
            logger.info("opentelemetry_initialized")
        except ImportError:
            logger.warning("opentelemetry_not_available", detail="Install opentelemetry packages")
        except Exception as exc:
            logger.error("opentelemetry_setup_failed", error=str(exc))
