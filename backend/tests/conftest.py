"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_env():
    os.environ["ALLOWED_API_KEYS"] = '["test-key"]'
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["APP_ENV"] = "testing"
    os.environ["LOG_FORMAT"] = "console"
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
    yield


@pytest.fixture
def api_headers():
    return {"X-API-Key": "test-key"}


@pytest.fixture
def mock_redis():
    with patch("app.services.redis_client.get_redis") as mock:
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.publish.return_value = 1
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_sentiment():
    with patch("app.services.sentiment._load_model"):
        with patch("app.services.sentiment.is_model_available", return_value=False):
            yield


@pytest.fixture
def mock_embeddings():
    with patch("app.services.topic_clustering._load_embedding_model"):
        with patch("app.services.topic_clustering.is_embedding_model_available", return_value=False):
            yield


@pytest.fixture
def client(mock_redis, mock_sentiment, mock_embeddings):
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_csv_content():
    return b"text,source,timestamp\nGreat product!,survey,2024-01-01\nTerrible service,email,2024-01-02\nOkay experience,chat,2024-01-03\n"


@pytest.fixture
def sample_json_content():
    import json
    data = [
        {"text": "Love this product!", "source": "app", "timestamp": "2024-01-01"},
        {"text": "Not happy with the service", "source": "email", "timestamp": "2024-01-02"},
        {"text": "It works fine", "source": "web", "timestamp": "2024-01-03"},
    ]
    return json.dumps(data).encode("utf-8")
