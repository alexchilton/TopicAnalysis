"""Webhook and SSE endpoints for real-time ingestion."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.core.logging import get_logger
from app.core.security import get_api_key, verify_webhook_signature
from app.models.schemas import AnalysisStatus, FeedbackEntry, JobStatus, WebhookPayload
from app.services.analysis_pipeline import run_analysis
from app.services.redis_client import subscribe_events

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["realtime"])


@router.post("/webhooks/ingest", response_model=JobStatus)
async def webhook_ingest(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Receive data via webhook with Stripe-style signature verification."""
    body = await request.body()
    signature = request.headers.get("X-Signature", "")
    timestamp = request.headers.get("X-Timestamp", "")

    if not verify_webhook_signature(body, signature, timestamp):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = WebhookPayload.model_validate_json(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}")

    if not payload.data:
        raise HTTPException(status_code=400, detail="No data entries in payload")

    import uuid

    job_id = uuid.uuid4().hex[:12]
    logger.info("webhook_received", job_id=job_id, event=payload.event_type, entries=len(payload.data))

    entries = [
        FeedbackEntry(
            id=e.id,
            text=e.text,
            source=payload.source or e.source or "webhook",
            timestamp=e.timestamp or datetime.utcnow(),
            metadata=e.metadata,
        )
        for e in payload.data
    ]

    background_tasks.add_task(run_analysis, entries, job_id)

    return JobStatus(
        job_id=job_id,
        status=AnalysisStatus.PENDING,
        progress=0.0,
        message=f"Webhook: processing {len(entries)} entries",
        created_at=datetime.utcnow(),
    )


@router.get("/events/analysis")
async def analysis_events(request: Request, api_key: str = Depends(get_api_key)):
    """Server-Sent Events stream for live analysis updates."""

    async def event_generator():
        try:
            async for data in subscribe_events("analysis_updates"):
                if await request.is_disconnected():
                    break
                yield {
                    "event": "analysis_update",
                    "data": json.dumps(data),
                }
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("sse_error", error=str(exc))

    return EventSourceResponse(event_generator())


@router.get("/events/anomalies")
async def anomaly_events(request: Request, api_key: str = Depends(get_api_key)):
    """SSE stream for anomaly alerts."""

    async def event_generator():
        try:
            async for data in subscribe_events("anomaly_alerts"):
                if await request.is_disconnected():
                    break
                yield {
                    "event": "anomaly_alert",
                    "data": json.dumps(data),
                }
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())
