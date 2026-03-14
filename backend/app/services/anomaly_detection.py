"""Anomaly detection: sentiment drift and topic spikes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import AnomalyAlert, AnomalyType, SentimentResult

logger = get_logger(__name__)


def detect_sentiment_anomalies(
    sentiments: list[SentimentResult],
    window: Optional[int] = None,
    threshold: Optional[float] = None,
) -> list[AnomalyAlert]:
    """Detect when sentiment drops below rolling average - threshold * std."""
    window = window or settings.anomaly_rolling_window
    threshold = threshold or settings.anomaly_sentiment_threshold

    if len(sentiments) < window:
        return []

    scores = np.array([s.score for s in sentiments])
    alerts = []

    for i in range(window, len(scores)):
        window_slice = scores[i - window : i]
        mean = np.mean(window_slice)
        std = np.std(window_slice)

        if std == 0:
            continue

        z_score = (scores[i] - mean) / std

        if z_score < -threshold:
            alerts.append(
                AnomalyAlert(
                    id=uuid.uuid4().hex[:12],
                    type=AnomalyType.SENTIMENT_DROP,
                    severity="high" if z_score < -2 * threshold else "medium",
                    message=f"Sentiment dropped to {scores[i]:.3f} (rolling avg: {mean:.3f}, z-score: {z_score:.2f})",
                    detected_at=datetime.utcnow(),
                    details={
                        "index": i,
                        "value": float(scores[i]),
                        "rolling_mean": float(mean),
                        "rolling_std": float(std),
                        "z_score": float(z_score),
                    },
                )
            )

    return alerts


def detect_topic_spikes(
    topic_assignments: list[int],
    window: Optional[int] = None,
    threshold: Optional[float] = None,
) -> list[AnomalyAlert]:
    """Detect unusual spikes in topic frequency."""
    window = window or settings.anomaly_rolling_window
    threshold = threshold or settings.anomaly_topic_spike_threshold

    if len(topic_assignments) < window:
        return []

    alerts = []
    unique_topics = set(topic_assignments)

    for topic_id in unique_topics:
        if topic_id == -1:
            continue

        occurrences = [1 if t == topic_id else 0 for t in topic_assignments]

        for i in range(window, len(occurrences)):
            window_slice = occurrences[i - window : i]
            mean = np.mean(window_slice)
            std = np.std(window_slice)

            if std == 0:
                continue

            # Check for spike in last 10% of window
            recent = occurrences[max(0, i - window // 10) : i]
            recent_rate = np.mean(recent) if recent else 0

            z_score = (recent_rate - mean) / std if std > 0 else 0

            if z_score > threshold:
                alerts.append(
                    AnomalyAlert(
                        id=uuid.uuid4().hex[:12],
                        type=AnomalyType.TOPIC_SPIKE,
                        severity="high" if z_score > 2 * threshold else "medium",
                        message=f"Topic {topic_id} spike detected (rate: {recent_rate:.3f}, avg: {mean:.3f})",
                        detected_at=datetime.utcnow(),
                        details={
                            "topic_id": topic_id,
                            "recent_rate": float(recent_rate),
                            "rolling_mean": float(mean),
                            "z_score": float(z_score),
                        },
                    )
                )
                break  # One alert per topic

    return alerts


def run_anomaly_detection(
    sentiments: list[SentimentResult],
    topic_assignments: list[int],
    thresholds: Optional[dict] = None,
) -> list[AnomalyAlert]:
    """Run all anomaly detection checks."""
    window = thresholds.get("rolling_window") if thresholds else None
    sent_thresh = thresholds.get("sentiment_threshold") if thresholds else None
    topic_thresh = thresholds.get("topic_spike_threshold") if thresholds else None

    alerts = []
    alerts.extend(detect_sentiment_anomalies(sentiments, window, sent_thresh))
    alerts.extend(detect_topic_spikes(topic_assignments, window, topic_thresh))
    return alerts
