"""Tests for API endpoints."""

from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, patch


class TestHealthEndpoints:
    def test_health(self, client, api_headers):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "uptime_seconds" in data

    def test_liveness(self, client):
        resp = client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"


class TestUploadEndpoints:
    def test_upload_csv(self, client, api_headers, sample_csv_content):
        with patch("app.api.analysis.run_analysis", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = None
            resp = client.post(
                "/api/v1/upload",
                files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
                headers=api_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data
            assert data["status"] == "pending"

    def test_upload_json(self, client, api_headers, sample_json_content):
        with patch("app.api.analysis.run_analysis", new_callable=AsyncMock):
            resp = client.post(
                "/api/v1/upload",
                files={"file": ("test.json", io.BytesIO(sample_json_content), "application/json")},
                headers=api_headers,
            )
            assert resp.status_code == 200

    def test_upload_unsupported_format(self, client, api_headers):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
            headers=api_headers,
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_upload_no_api_key(self, client, sample_csv_content):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert resp.status_code == 403

    def test_upload_invalid_api_key(self, client, sample_csv_content):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 403

    def test_upload_empty_file(self, client, api_headers):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.csv", io.BytesIO(b"text\n"), "text/csv")},
            headers=api_headers,
        )
        assert resp.status_code == 400


class TestJobEndpoints:
    def test_list_jobs(self, client, api_headers):
        resp = client.get("/api/v1/jobs", headers=api_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent_job(self, client, api_headers):
        resp = client.get("/api/v1/jobs/nonexistent", headers=api_headers)
        assert resp.status_code == 404


class TestWebhookEndpoints:
    def test_webhook_invalid_signature(self, client):
        payload = json.dumps({
            "event_type": "feedback",
            "data": [{"text": "test feedback"}],
        })
        resp = client.post(
            "/api/v1/webhooks/ingest",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Signature": "v1=invalid",
                "X-Timestamp": "0",
            },
        )
        assert resp.status_code == 401

    def test_webhook_missing_signature(self, client):
        payload = json.dumps({"event_type": "feedback", "data": [{"text": "test"}]})
        resp = client.post(
            "/api/v1/webhooks/ingest",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401
