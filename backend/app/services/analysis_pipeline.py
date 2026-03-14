"""Analysis pipeline orchestrator — coordinates all ML services."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from app.core.logging import get_logger
from app.models.schemas import (
    AnalysisResult,
    AnalysisSummary,
    AnalysisStatus,
    AnalyzedEntry,
    FeedbackEntry,
    SentimentLabel,
    SentimentTrend,
    TopicInfo,
)
from app.services.anomaly_detection import run_anomaly_detection
from app.services.data_quality import analyze_data_quality
from app.services.language_detection import detect_languages_batch
from app.services.notifications import notify_anomalies
from app.services.redis_client import publish_event
from app.services.sentiment import (
    analyze_sentiment,
    get_fallback_sentiment,
    is_model_available,
)
from app.services.topic_clustering import (
    build_topic_graph,
    cluster_topics,
    compute_embeddings,
    is_embedding_model_available,
)

logger = get_logger(__name__)

# In-memory job store (production would use a database)
_jobs: Dict[str, AnalysisResult] = {}


async def run_analysis(
    entries: list[FeedbackEntry],
    job_id: Optional[str] = None,
    detect_anomalies: bool = True,
    min_cluster_size: Optional[int] = None,
    min_samples: Optional[int] = None,
) -> AnalysisResult:
    """Run the full analysis pipeline."""
    job_id = job_id or uuid.uuid4().hex[:12]
    now = datetime.utcnow()

    result = AnalysisResult(
        job_id=job_id,
        status=AnalysisStatus.PROCESSING,
        created_at=now,
        total_entries=len(entries),
    )
    _jobs[job_id] = result

    await publish_event("analysis_updates", {"job_id": job_id, "status": "processing", "progress": 0.0})

    try:
        import time as _time

        texts = [e.text for e in entries]
        logger.info("pipeline_started", job_id=job_id, entry_count=len(texts),
                     sample_text=texts[0][:100] if texts else "")

        # Step 1: Language detection
        t0 = _time.time()
        logger.info("pipeline_step", step="language_detection", count=len(texts))
        languages = detect_languages_batch(texts)
        lang_counts = {}
        for l in languages:
            lang_counts[l.language] = lang_counts.get(l.language, 0) + 1
        logger.info("language_detection_complete", elapsed=round(_time.time() - t0, 2),
                     language_distribution=str(lang_counts))
        await publish_event("analysis_updates", {"job_id": job_id, "status": "processing", "progress": 0.2})

        # Step 2: Sentiment analysis
        t0 = _time.time()
        model_available = is_model_available()
        logger.info("pipeline_step", step="sentiment_analysis", count=len(texts),
                     model_available=model_available)
        if model_available:
            sentiments = await analyze_sentiment(texts)
        else:
            logger.warning("sentiment_model_unavailable_using_fallback",
                           reason="ML model could not be loaded — using keyword fallback")
            sentiments = [get_fallback_sentiment(t) for t in texts]

        # Log sentiment distribution
        sent_dist = {}
        scores = [s.score for s in sentiments]
        for s in sentiments:
            sent_dist[s.label.value] = sent_dist.get(s.label.value, 0) + 1
        logger.info("sentiment_analysis_complete",
                     elapsed=round(_time.time() - t0, 2),
                     distribution=str(sent_dist),
                     avg_score=round(sum(scores) / len(scores), 4) if scores else 0,
                     min_score=round(min(scores), 4) if scores else 0,
                     max_score=round(max(scores), 4) if scores else 0,
                     sample_label=sentiments[0].label.value if sentiments else "none",
                     sample_score=sentiments[0].score if sentiments else 0)
        await publish_event("analysis_updates", {"job_id": job_id, "status": "processing", "progress": 0.4})

        # Step 3: Embeddings + Topic Clustering
        t0 = _time.time()
        logger.info("pipeline_step", step="topic_clustering", count=len(texts))
        topic_assignments = [-1] * len(texts)
        clusters = []
        topic_graph = None
        reduced_embeddings = None

        if is_embedding_model_available() and len(texts) >= 5:
            embeddings = await compute_embeddings(texts)
            topic_assignments, clusters, reduced_embeddings = await cluster_topics(
                texts, embeddings, min_cluster_size, min_samples
            )

            # Enrich clusters with sentiment/language data
            for cluster in clusters:
                indices = [i for i, t in enumerate(topic_assignments) if t == cluster.topic_id]
                if indices:
                    cluster_sentiments = [sentiments[i] for i in indices]
                    cluster.avg_sentiment = round(
                        np.mean([s.score for s in cluster_sentiments]), 4
                    )
                    cluster.sentiment_distribution = dict(
                        Counter(s.label.value for s in cluster_sentiments)
                    )
                    cluster.languages = dict(
                        Counter(languages[i].language for i in indices)
                    )

            topic_graph = build_topic_graph(clusters, embeddings, topic_assignments)
        else:
            logger.warning("topic_clustering_skipped", reason="model unavailable or too few entries")

        await publish_event("analysis_updates", {"job_id": job_id, "status": "processing", "progress": 0.7})

        # Step 4: Build analyzed entries
        analyzed_entries = []
        for i, entry in enumerate(entries):
            topic_id = topic_assignments[i]
            topic_label = "Uncategorized"
            for c in clusters:
                if c.topic_id == topic_id:
                    topic_label = c.label
                    break

            analyzed_entries.append(
                AnalyzedEntry(
                    id=entry.id or uuid.uuid4().hex[:12],
                    text=entry.text,
                    source=entry.source,
                    timestamp=entry.timestamp,
                    sentiment=sentiments[i],
                    language=languages[i],
                    topic_id=topic_id,
                    topic_label=topic_label,
                    metadata=entry.metadata,
                )
            )

        # Step 5: Sentiment trends
        trends = _compute_sentiment_trends(analyzed_entries)

        # Step 6: Data quality
        data_quality = analyze_data_quality(analyzed_entries)

        # Step 7: Anomaly detection
        anomalies = []
        if detect_anomalies and len(sentiments) >= 20:
            anomalies = run_anomaly_detection(sentiments, topic_assignments)
            if anomalies:
                await notify_anomalies(anomalies)

        await publish_event("analysis_updates", {"job_id": job_id, "status": "processing", "progress": 0.9})

        # Build summary
        sentiment_counts = Counter(s.label.value for s in sentiments)
        dominant = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"
        top_topics = [
            TopicInfo(
                topic_id=c.topic_id,
                label=c.label,
                keywords=c.keywords,
                size=c.size,
            )
            for c in sorted(clusters, key=lambda c: c.size, reverse=True)[:5]
            if c.topic_id != -1
        ]

        summary = AnalysisSummary(
            total_entries=len(entries),
            avg_sentiment=round(np.mean([s.score for s in sentiments]), 4),
            dominant_sentiment=SentimentLabel(dominant),
            num_topics=len([c for c in clusters if c.topic_id != -1]),
            top_topics=top_topics,
            languages_detected=list(set(l.language for l in languages if l.language != "unknown")),
            date_range=_get_date_range(entries),
        )

        # Final result
        result.status = AnalysisStatus.COMPLETED
        result.completed_at = datetime.utcnow()
        result.entries = analyzed_entries
        result.topics = clusters
        result.sentiment_trends = trends
        result.topic_graph = topic_graph
        result.data_quality = data_quality
        result.anomalies = anomalies
        result.summary = summary
        _jobs[job_id] = result

        await publish_event("analysis_updates", {
            "job_id": job_id,
            "status": "completed",
            "progress": 1.0,
            "total_entries": len(entries),
        })

        logger.info("analysis_completed", job_id=job_id, entries=len(entries), topics=len(clusters))
        return result

    except Exception as exc:
        result.status = AnalysisStatus.FAILED
        _jobs[job_id] = result
        await publish_event("analysis_updates", {"job_id": job_id, "status": "failed", "error": str(exc)})
        logger.error("analysis_failed", job_id=job_id, error=str(exc))
        raise


def _compute_sentiment_trends(entries: list[AnalyzedEntry]) -> list[SentimentTrend]:
    """Compute sentiment trends over time periods."""
    dated = [e for e in entries if e.timestamp]
    if not dated:
        return [_single_period_trend(entries, "all")]

    dated.sort(key=lambda e: e.timestamp)

    # Determine grouping: daily if span > 7 days, else hourly
    span = (dated[-1].timestamp - dated[0].timestamp).days
    if span > 30:
        fmt = "%Y-%m"
    elif span > 7:
        fmt = "%Y-%m-%d"
    else:
        fmt = "%Y-%m-%d %H:00"

    groups: dict[str, list[AnalyzedEntry]] = {}
    for e in dated:
        key = e.timestamp.strftime(fmt)
        groups.setdefault(key, []).append(e)

    trends = []
    for period, group_entries in groups.items():
        trends.append(_single_period_trend(group_entries, period))

    return trends


def _single_period_trend(entries: list[AnalyzedEntry], period: str) -> SentimentTrend:
    scores = [e.sentiment.score for e in entries]
    mean = np.mean(scores) if scores else 0.5
    std = np.std(scores) if scores else 0
    n = len(scores)
    se = std / np.sqrt(n) if n > 0 else 0

    return SentimentTrend(
        period=period,
        avg_sentiment=round(float(mean), 4),
        count=n,
        positive=sum(1 for e in entries if e.sentiment.label == SentimentLabel.POSITIVE),
        negative=sum(1 for e in entries if e.sentiment.label == SentimentLabel.NEGATIVE),
        neutral=sum(1 for e in entries if e.sentiment.label == SentimentLabel.NEUTRAL),
        confidence_lower=round(float(max(0, mean - 1.96 * se)), 4),
        confidence_upper=round(float(min(1, mean + 1.96 * se)), 4),
    )


def _get_date_range(entries: list[FeedbackEntry]) -> dict[str, str] | None:
    dated = [e.timestamp for e in entries if e.timestamp]
    if not dated:
        return None
    return {
        "start": min(dated).isoformat(),
        "end": max(dated).isoformat(),
    }


def get_job(job_id: str) -> AnalysisResult | None:
    return _jobs.get(job_id)


def get_all_jobs() -> list[AnalysisResult]:
    return list(_jobs.values())


def filter_entries(
    entries: list[AnalyzedEntry],
    date_from=None,
    date_to=None,
    sentiment_min=None,
    sentiment_max=None,
    topics=None,
    languages=None,
    sources=None,
    search_text=None,
) -> list[AnalyzedEntry]:
    """Apply filters to analyzed entries."""
    result = entries

    if date_from:
        result = [e for e in result if e.timestamp and e.timestamp >= date_from]
    if date_to:
        result = [e for e in result if e.timestamp and e.timestamp <= date_to]
    if sentiment_min is not None:
        result = [e for e in result if e.sentiment.score >= sentiment_min]
    if sentiment_max is not None:
        result = [e for e in result if e.sentiment.score <= sentiment_max]
    if topics:
        result = [e for e in result if e.topic_id in topics]
    if languages:
        result = [e for e in result if e.language.language in languages]
    if sources:
        result = [e for e in result if e.source in sources]
    if search_text:
        search_lower = search_text.lower()
        result = [e for e in result if search_lower in e.text.lower()]

    return result
