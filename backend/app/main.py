"""FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import analysis, export, health, webhooks
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import register_middleware
from app.core.security import limiter
from app.core.telemetry import setup_telemetry
from app.services.redis_client import close_redis

setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        env=settings.app_env,
    )
    settings.upload_path  # Ensure upload directory exists
    yield
    logger.info("application_shutting_down")
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    description="Sentiment & Topic Analysis Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)
setup_telemetry(app)

# Routes
app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(export.router)
app.include_router(webhooks.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from app.core.logging import get_correlation_id

    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": get_correlation_id(),
        },
    )


# Serve frontend static files in production (when static/ dir exists)
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA index.html for all non-API routes."""
        # Don't intercept API, docs, health, or metrics paths
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "metrics")):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
