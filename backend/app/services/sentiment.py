"""Sentiment analysis using cardiffnlp/twitter-xlm-roberta-base-sentiment."""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import SentimentLabel, SentimentResult

logger = get_logger(__name__)

_model = None
_tokenizer = None
_executor = ThreadPoolExecutor(max_workers=2)

LABEL_MAP = {
    "negative": SentimentLabel.NEGATIVE,
    "neutral": SentimentLabel.NEUTRAL,
    "positive": SentimentLabel.POSITIVE,
    "LABEL_0": SentimentLabel.NEGATIVE,
    "LABEL_1": SentimentLabel.NEUTRAL,
    "LABEL_2": SentimentLabel.POSITIVE,
}


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_name = settings.sentiment_model
        logger.info("loading_sentiment_model", model=model_name)
        t0 = time.time()

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=settings.model_cache_dir,
            use_fast=False,
        )
        logger.info("tokenizer_loaded", model=model_name, elapsed=round(time.time() - t0, 2))

        _model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=settings.model_cache_dir,
        )
        _model.eval()
        label_config = getattr(_model.config, "id2label", {})
        logger.info(
            "sentiment_model_loaded",
            model=model_name,
            elapsed=round(time.time() - t0, 2),
            model_labels=str(label_config),
            num_labels=getattr(_model.config, "num_labels", "unknown"),
        )
    except Exception as exc:
        logger.error("sentiment_model_load_failed", error=str(exc), exc_type=type(exc).__name__)
        raise


def _predict_batch_sync(texts: list[str]) -> list[SentimentResult]:
    import torch
    from scipy.special import softmax

    _load_model()

    results = []
    batch_size = 32
    t0 = time.time()

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        truncated = [t[:512] for t in batch]

        inputs = _tokenizer(
            truncated,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = _model(**inputs)

        scores = outputs.logits.detach().numpy()

        for j, score_row in enumerate(scores):
            probs = softmax(score_row)
            label_idx = int(probs.argmax())
            # Use model's own id2label mapping (0=negative, 1=neutral, 2=positive)
            id2label = {0: SentimentLabel.NEGATIVE, 1: SentimentLabel.NEUTRAL, 2: SentimentLabel.POSITIVE}
            label = id2label.get(label_idx, SentimentLabel.NEUTRAL)
            confidence = float(probs[label_idx])

            # Sentiment score: -1 (negative) to +1 (positive)
            sentiment_score = float(probs[2] - probs[0])

            results.append(
                SentimentResult(
                    label=label,
                    score=round(max(0, min(1, (sentiment_score + 1) / 2)), 4),
                    confidence=round(confidence, 4),
                )
            )

        # Log first batch for debugging
        if i == 0 and len(results) > 0:
            sample = results[0]
            logger.info(
                "sentiment_first_batch_sample",
                text_preview=truncated[0][:80],
                label=sample.label.value,
                score=sample.score,
                confidence=sample.confidence,
            )

    elapsed = round(time.time() - t0, 2)
    logger.info(
        "sentiment_batch_complete",
        total_texts=len(texts),
        elapsed_seconds=elapsed,
        texts_per_second=round(len(texts) / max(elapsed, 0.001), 1),
    )

    return results


async def analyze_sentiment(texts: list[str]) -> list[SentimentResult]:
    """Analyze sentiment for a batch of texts asynchronously."""
    logger.info("analyze_sentiment_called", count=len(texts), using="ml_model")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _predict_batch_sync, texts)


def analyze_sentiment_sync(texts: list[str]) -> list[SentimentResult]:
    """Synchronous sentiment analysis."""
    logger.info("analyze_sentiment_sync_called", count=len(texts))
    return _predict_batch_sync(texts)


_models_available: Optional[bool] = None


def is_model_available() -> bool:
    """Check if ML model is available. Re-checks on each call until successful."""
    global _models_available
    if _models_available is True:
        return True
    # Always retry if previously failed — deps may have been installed since last check
    try:
        _load_model()
        _models_available = True
        logger.info("model_availability_check", available=True)
    except Exception as exc:
        _models_available = False
        logger.warning("model_availability_check", available=False, error=str(exc))
    return _models_available


def get_fallback_sentiment(text: str) -> SentimentResult:
    """Simple keyword-based fallback when ML model unavailable."""
    logger.debug("using_fallback_sentiment", text_preview=text[:60])
    text_lower = text.lower()
    positive_words = {"good", "great", "excellent", "love", "amazing", "happy", "best", "wonderful", "fantastic"}
    negative_words = {"bad", "terrible", "awful", "hate", "worst", "horrible", "poor", "disappointing", "angry"}

    pos = sum(1 for w in text_lower.split() if w in positive_words)
    neg = sum(1 for w in text_lower.split() if w in negative_words)

    if pos > neg:
        return SentimentResult(label=SentimentLabel.POSITIVE, score=0.7, confidence=0.3)
    elif neg > pos:
        return SentimentResult(label=SentimentLabel.NEGATIVE, score=0.3, confidence=0.3)
    return SentimentResult(label=SentimentLabel.NEUTRAL, score=0.5, confidence=0.3)
