"""FastAPI middleware for correlation IDs, request logging, and error handling."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import correlation_id_var, get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Correlation-ID", uuid.uuid4().hex[:16])
        correlation_id_var.set(cid)
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Correlation-ID"] = cid
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(CorrelationIdMiddleware)
