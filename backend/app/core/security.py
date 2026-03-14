"""Security utilities: API key validation, webhook signature verification, rate limiting."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    if not api_key or api_key not in settings.allowed_api_keys:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


def _key_func(request: Request) -> str:
    api_key = request.headers.get(settings.api_key_header, "")
    if api_key:
        return api_key
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


def verify_webhook_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """Verify Stripe-style webhook signature (t=timestamp,v1=signature)."""
    if not signature or not timestamp:
        return False

    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(time.time() - ts) > 300:
        return False

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected = hmac.new(
        settings.webhook_secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    parts = signature.split(",")
    for part in parts:
        if part.startswith("v1="):
            sig_value = part[3:]
            if hmac.compare_digest(expected, sig_value):
                return True

    return False
