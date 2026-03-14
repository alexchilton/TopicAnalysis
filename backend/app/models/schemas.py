"""Pydantic schemas for all data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# --- Enums ---


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class AnomalyType(str, Enum):
    SENTIMENT_DROP = "sentiment_drop"
    TOPIC_SPIKE = "topic_spike"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Request Models ---


class FeedbackEntry(BaseModel):
    id: str | None = None
    text: str = Field(..., min_length=1, max_length=50000)
    source: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None


class AnalysisRequest(BaseModel):
    entries: list[FeedbackEntry] = Field(..., min_items=1)
    options: AnalysisOptions | None = None


class AnalysisOptions(BaseModel):
    min_cluster_size: int = Field(default=5, ge=2, le=100)
    min_samples: int = Field(default=3, ge=1, le=50)
    detect_anomalies: bool = True
    language_filter: str | None = None


class FilterParams(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    sentiment_min: float | None = Field(default=None, ge=-1.0, le=1.0)
    sentiment_max: float | None = Field(default=None, ge=-1.0, le=1.0)
    topics: list[int] | None = None
    languages: list[str] | None = None
    sources: list[str] | None = None
    search_text: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class ComparisonRequest(BaseModel):
    segment_a: FilterParams
    segment_b: FilterParams


class WebhookPayload(BaseModel):
    event_type: str
    data: list[FeedbackEntry]
    source: str | None = None


class AnomalyThresholds(BaseModel):
    sentiment_threshold: float = Field(default=1.5, ge=0.1, le=5.0)
    topic_spike_threshold: float = Field(default=3.0, ge=1.0, le=10.0)
    rolling_window: int = Field(default=50, ge=10, le=1000)


# --- Response Models ---


class SentimentResult(BaseModel):
    label: SentimentLabel
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class LanguageResult(BaseModel):
    language: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: str  # "langdetect" or "cld3"


class TopicInfo(BaseModel):
    topic_id: int
    label: str
    keywords: list[str]
    size: int
    representative_docs: list[str] = Field(default_factory=list)


class AnalyzedEntry(BaseModel):
    id: str
    text: str
    source: str | None = None
    timestamp: datetime | None = None
    sentiment: SentimentResult
    language: LanguageResult
    topic_id: int
    topic_label: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] | None = None


class TopicCluster(BaseModel):
    topic_id: int
    label: str
    keywords: list[str]
    size: int
    avg_sentiment: float
    sentiment_distribution: dict[str, int]
    languages: dict[str, int]
    representative_docs: list[str]


class SentimentTrend(BaseModel):
    period: str
    avg_sentiment: float
    count: int
    positive: int
    negative: int
    neutral: int
    confidence_lower: float
    confidence_upper: float


class TopicLink(BaseModel):
    source: int
    target: int
    weight: float


class TopicGraph(BaseModel):
    nodes: list[TopicCluster]
    links: list[TopicLink]


class DataQualityReport(BaseModel):
    total_entries: int
    low_confidence_count: int
    low_confidence_entries: list[str]
    mixed_language_count: int
    mixed_language_entries: list[str]
    duplicate_count: int
    duplicate_entries: list[str]
    avg_confidence: float
    language_distribution: dict[str, int]


class AnomalyAlert(BaseModel):
    id: str
    type: AnomalyType
    severity: str
    message: str
    detected_at: datetime
    details: dict[str, Any]


class AnalysisResult(BaseModel):
    job_id: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: datetime | None = None
    total_entries: int
    entries: list[AnalyzedEntry] = Field(default_factory=list)
    topics: list[TopicCluster] = Field(default_factory=list)
    sentiment_trends: list[SentimentTrend] = Field(default_factory=list)
    topic_graph: TopicGraph | None = None
    data_quality: DataQualityReport | None = None
    anomalies: list[AnomalyAlert] = Field(default_factory=list)
    summary: AnalysisSummary | None = None


class AnalysisSummary(BaseModel):
    total_entries: int
    avg_sentiment: float
    dominant_sentiment: SentimentLabel
    num_topics: int
    top_topics: list[TopicInfo]
    languages_detected: list[str]
    date_range: dict[str, str] | None = None


class ComparisonResult(BaseModel):
    segment_a: AnalysisSummary
    segment_b: AnalysisSummary
    sentiment_delta: float
    topic_changes: list[dict[str, Any]]
    new_topics: list[TopicInfo]
    disappeared_topics: list[TopicInfo]


class JobStatus(BaseModel):
    job_id: str
    status: AnalysisStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""
    created_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool
    redis_connected: bool
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail: str
    correlation_id: str | None = None
    code: str | None = None


# Fix forward references
AnalysisRequest.model_rebuild()
