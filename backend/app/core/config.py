"""Application configuration using pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "TopicAnalysis"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    api_key_header: str = "X-API-Key"
    allowed_api_keys: list[str] = ["dev-key-1"]

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # File Upload
    max_upload_size_mb: int = 500
    chunk_size_mb: int = 10
    upload_dir: str = "./uploads"

    # ML Models
    sentiment_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    model_cache_dir: str = "./model_cache"
    model_load_timeout: int = 120

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Anomaly Detection
    anomaly_rolling_window: int = 50
    anomaly_sentiment_threshold: float = 1.5
    anomaly_topic_spike_threshold: float = 3.0

    # Notifications
    slack_webhook_url: str = ""
    notification_email_from: str = ""
    notification_email_to: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Webhook
    webhook_secret: str = "whsec_change-me"

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "topic-analysis"
    log_level: str = "INFO"
    log_format: str = "json"

    # Database
    database_url: str = "sqlite:///./data/analysis.db"

    @field_validator("allowed_api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
