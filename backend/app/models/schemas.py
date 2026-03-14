"""Pydantic schemas for all data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
    id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=50000)
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    entries: List[FeedbackEntry] = Field(..., min_items=1)
    options: Optional[AnalysisOptions] = None


class AnalysisOptions(BaseModel):
    min_cluster_size: int = Field(default=5, ge=2, le=100)
    min_samples: int = Field(default=3, ge=1, le=50)
    detect_anomalies: bool = True
    language_filter: Optional[str] = None


class FilterParams(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sentiment_min: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    sentiment_max: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    topics: Optional[List[int]] = None
    languages: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    search_text: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class ComparisonRequest(BaseModel):
    segment_a: FilterParams
    segment_b: FilterParams


class WebhookPayload(BaseModel):
    event_type: str
    data: List[FeedbackEntry]
    source: Optional[str] = None


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
    keywords: List[str]
    size: int
    representative_docs: List[str] = Field(default_factory=list)


class AnalyzedEntry(BaseModel):
    id: str
    text: str
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    sentiment: SentimentResult
    language: LanguageResult
    topic_id: int
    topic_label: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class TopicCluster(BaseModel):
    topic_id: int
    label: str
    keywords: List[str]
    size: int
    avg_sentiment: float
    sentiment_distribution: Dict[str, int]
    languages: Dict[str, int]
    representative_docs: List[str]


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
    nodes: List[TopicCluster]
    links: List[TopicLink]


class DataQualityReport(BaseModel):
    total_entries: int
    low_confidence_count: int
    low_confidence_entries: List[str]
    mixed_language_count: int
    mixed_language_entries: List[str]
    duplicate_count: int
    duplicate_entries: List[str]
    avg_confidence: float
    language_distribution: Dict[str, int]


class AnomalyAlert(BaseModel):
    id: str
    type: AnomalyType
    severity: str
    message: str
    detected_at: datetime
    details: Dict[str, Any]


class AnalysisResult(BaseModel):
    job_id: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_entries: int
    entries: List[AnalyzedEntry] = Field(default_factory=list)
    topics: List[TopicCluster] = Field(default_factory=list)
    sentiment_trends: List[SentimentTrend] = Field(default_factory=list)
    topic_graph: Optional[TopicGraph] = None
    data_quality: Optional[DataQualityReport] = None
    anomalies: List[AnomalyAlert] = Field(default_factory=list)
    summary: Optional[AnalysisSummary] = None


class AnalysisSummary(BaseModel):
    total_entries: int
    avg_sentiment: float
    dominant_sentiment: SentimentLabel
    num_topics: int
    top_topics: List[TopicInfo]
    languages_detected: List[str]
    date_range: Optional[Dict[str, str]] = None


class ComparisonResult(BaseModel):
    segment_a: AnalysisSummary
    segment_b: AnalysisSummary
    sentiment_delta: float
    topic_changes: List[Dict[str, Any]]
    new_topics: List[TopicInfo]
    disappeared_topics: List[TopicInfo]


class JobStatus(BaseModel):
    job_id: str
    status: AnalysisStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool
    redis_connected: bool
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail: str
    correlation_id: Optional[str] = None
    code: Optional[str] = None


# Fix forward references
AnalysisRequest.model_rebuild()
