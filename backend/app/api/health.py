"""Health and system endpoints."""

from __future__ import annotations

import time
import traceback

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import HealthResponse
from app.services.redis_client import check_redis_health
from app.services.sentiment import is_model_available

router = APIRouter(tags=["system"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    redis_ok = await check_redis_health()
    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        version="1.0.0",
        models_loaded=is_model_available(),
        redis_connected=redis_ok,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    redis_ok = await check_redis_health()
    if not redis_ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Redis not available")
    return {"status": "ready"}


@router.get("/health/models")
async def model_diagnostics():
    """Diagnostic endpoint showing model loading details."""
    diag = {
        "sentiment_model": settings.sentiment_model,
        "embedding_model": settings.embedding_model,
        "model_cache_dir": settings.model_cache_dir,
        "checks": {},
    }

    # Check torch
    try:
        import torch

        diag["checks"]["torch"] = {"ok": True, "version": torch.__version__}
    except Exception as e:
        diag["checks"]["torch"] = {"ok": False, "error": str(e)}

    # Check transformers
    try:
        import transformers

        diag["checks"]["transformers"] = {"ok": True, "version": transformers.__version__}
    except Exception as e:
        diag["checks"]["transformers"] = {"ok": False, "error": str(e)}

    # Check scipy
    try:
        import scipy

        diag["checks"]["scipy"] = {"ok": True, "version": scipy.__version__}
    except Exception as e:
        diag["checks"]["scipy"] = {"ok": False, "error": str(e)}

    # Try loading model
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(
            settings.sentiment_model, cache_dir=settings.model_cache_dir, use_fast=False
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            settings.sentiment_model, cache_dir=settings.model_cache_dir
        )
        model.eval()
        elapsed = round(time.time() - t0, 2)
        diag["checks"]["model_load"] = {
            "ok": True,
            "elapsed": elapsed,
            "num_labels": model.config.num_labels,
            "id2label": model.config.id2label,
        }

        # Try an actual prediction
        import torch
        from scipy.special import softmax

        inputs = tok("I love this product, it's amazing!", return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        probs = softmax(outputs.logits.detach().numpy()[0])
        diag["checks"]["test_prediction"] = {
            "ok": True,
            "text": "I love this product, it's amazing!",
            "probs": {"negative": float(probs[0]), "neutral": float(probs[1]), "positive": float(probs[2])},
            "score": round(float((probs[2] - probs[0] + 1) / 2), 4),
        }
    except Exception as e:
        diag["checks"]["model_load"] = {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()[-500:],
        }

    # Check is_model_available state
    from app.services.sentiment import _model, _models_available, _tokenizer

    diag["state"] = {
        "is_model_available": is_model_available(),
        "_model_loaded": _model is not None,
        "_tokenizer_loaded": _tokenizer is not None,
        "_models_available_cache": _models_available,
    }

    return diag
