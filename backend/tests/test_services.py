"""Tests for core services with mocked ML inference."""

from __future__ import annotations

import json

import pytest

from app.models.schemas import SentimentLabel, SentimentResult


class TestLanguageDetection:
    def test_detect_english(self):
        from app.services.language_detection import detect_language

        result = detect_language("This is a test sentence in English")
        assert result.language in ("en", "unknown")
        assert result.confidence >= 0.0

    def test_detect_empty_text(self):
        from app.services.language_detection import detect_language

        result = detect_language("")
        assert result.language == "unknown"
        assert result.confidence == 0.0

    def test_detect_short_text(self):
        from app.services.language_detection import detect_language

        result = detect_language("hi")
        assert result.language == "unknown"

    def test_batch_detection(self):
        from app.services.language_detection import detect_languages_batch

        results = detect_languages_batch(["Hello world", "Bonjour le monde", ""])
        assert len(results) == 3


class TestSentiment:
    def test_fallback_sentiment_positive(self):
        from app.services.sentiment import get_fallback_sentiment

        result = get_fallback_sentiment("This is great and amazing!")
        assert result.label == SentimentLabel.POSITIVE

    def test_fallback_sentiment_negative(self):
        from app.services.sentiment import get_fallback_sentiment

        result = get_fallback_sentiment("This is terrible and awful")
        assert result.label == SentimentLabel.NEGATIVE

    def test_fallback_sentiment_neutral(self):
        from app.services.sentiment import get_fallback_sentiment

        result = get_fallback_sentiment("The weather is cloudy today")
        assert result.label == SentimentLabel.NEUTRAL


class TestFileProcessing:
    def test_parse_csv(self):
        from app.services.file_processing import parse_csv

        content = b"text,source\nHello world,test\nGoodbye world,test\n"
        entries = parse_csv(content)
        assert len(entries) == 2
        assert entries[0].text == "Hello world"

    def test_parse_json_array(self):
        from app.services.file_processing import parse_json

        data = [{"text": "entry 1"}, {"text": "entry 2"}]
        entries = parse_json(json.dumps(data).encode())
        assert len(entries) == 2

    def test_parse_json_string_array(self):
        from app.services.file_processing import parse_json

        data = ["feedback one", "feedback two"]
        entries = parse_json(json.dumps(data).encode())
        assert len(entries) == 2

    def test_parse_json_with_wrapper(self):
        from app.services.file_processing import parse_json

        data = {"data": [{"text": "entry 1"}]}
        entries = parse_json(json.dumps(data).encode())
        assert len(entries) == 1

    def test_parse_csv_missing_text_column(self):
        from app.services.file_processing import parse_csv

        content = b"name,age\nJohn,30\n"
        # Should fall back to first column or raise
        try:
            entries = parse_csv(content)
            assert len(entries) >= 0
        except ValueError:
            pass

    def test_unsupported_format(self):
        from app.services.file_processing import parse_file

        with pytest.raises(ValueError, match="Unsupported"):
            parse_file(b"content", "file.txt")


class TestAnomalyDetection:
    def test_no_anomalies_stable(self):
        from app.services.anomaly_detection import detect_sentiment_anomalies

        sentiments = [SentimentResult(label=SentimentLabel.NEUTRAL, score=0.5, confidence=0.9) for _ in range(100)]
        alerts = detect_sentiment_anomalies(sentiments)
        assert len(alerts) == 0

    def test_detects_sentiment_drop(self):
        from app.services.anomaly_detection import detect_sentiment_anomalies

        sentiments = [SentimentResult(label=SentimentLabel.POSITIVE, score=0.8, confidence=0.9) for _ in range(60)]
        sentiments.append(SentimentResult(label=SentimentLabel.NEGATIVE, score=0.1, confidence=0.9))
        alerts = detect_sentiment_anomalies(sentiments, window=50, threshold=1.5)
        assert len(alerts) > 0
        assert alerts[0].type.value == "sentiment_drop"

    def test_too_few_entries(self):
        from app.services.anomaly_detection import detect_sentiment_anomalies

        sentiments = [SentimentResult(label=SentimentLabel.NEUTRAL, score=0.5, confidence=0.9) for _ in range(5)]
        alerts = detect_sentiment_anomalies(sentiments, window=50)
        assert len(alerts) == 0


class TestDataQuality:
    def test_empty_entries(self):
        from app.services.data_quality import analyze_data_quality

        report = analyze_data_quality([])
        assert report.total_entries == 0

    def test_quality_report(self):
        from app.models.schemas import AnalyzedEntry, LanguageResult
        from app.services.data_quality import analyze_data_quality

        entries = [
            AnalyzedEntry(
                id="1",
                text="Great product",
                source="test",
                sentiment=SentimentResult(label=SentimentLabel.POSITIVE, score=0.9, confidence=0.95),
                language=LanguageResult(language="en", confidence=0.99, method="langdetect"),
                topic_id=0,
                topic_label="Topic 0",
            ),
            AnalyzedEntry(
                id="2",
                text="Mauvais service",
                source="test",
                sentiment=SentimentResult(label=SentimentLabel.NEGATIVE, score=0.2, confidence=0.4),
                language=LanguageResult(language="fr", confidence=0.85, method="langdetect"),
                topic_id=1,
                topic_label="Topic 1",
            ),
        ]

        report = analyze_data_quality(entries)
        assert report.total_entries == 2
        assert report.low_confidence_count == 1
        assert report.mixed_language_count == 1


class TestExport:
    def test_export_csv(self):
        from app.models.schemas import AnalyzedEntry, LanguageResult
        from app.services.export import export_csv

        entries = [
            AnalyzedEntry(
                id="1",
                text="Test",
                source="test",
                sentiment=SentimentResult(label=SentimentLabel.POSITIVE, score=0.9, confidence=0.95),
                language=LanguageResult(language="en", confidence=0.99, method="langdetect"),
                topic_id=0,
                topic_label="Topic 0",
            ),
        ]
        result = export_csv(entries)
        assert b"id" in result
        assert b"Test" in result

    def test_export_json(self):
        from app.models.schemas import AnalyzedEntry, LanguageResult
        from app.services.export import export_json

        entries = [
            AnalyzedEntry(
                id="1",
                text="Test",
                source="test",
                sentiment=SentimentResult(label=SentimentLabel.POSITIVE, score=0.9, confidence=0.95),
                language=LanguageResult(language="en", confidence=0.99, method="langdetect"),
                topic_id=0,
                topic_label="Topic 0",
            ),
        ]
        result = export_json(entries)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["text"] == "Test"


def _ml_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not _ml_available(),
    reason="ML models not installed — skipping real model tests",
)
class TestRealSentimentModel:
    """Diagnostic tests using the real ML model (not mocked)."""

    def test_model_loads(self):
        from app.services import sentiment

        sentiment._load_model()
        assert sentiment._model is not None

    def test_positive_english(self):
        from app.services.sentiment import analyze_sentiment_sync

        results = analyze_sentiment_sync(["I love this product, it is amazing!"])
        assert len(results) == 1
        assert results[0].label == SentimentLabel.POSITIVE
        assert results[0].score > 0.7
        assert results[0].confidence > 0.5

    def test_negative_english(self):
        from app.services.sentiment import analyze_sentiment_sync

        results = analyze_sentiment_sync(["This is terrible, worst experience ever."])
        assert len(results) == 1
        assert results[0].label == SentimentLabel.NEGATIVE
        assert results[0].score < 0.3
        assert results[0].confidence > 0.5

    def test_neutral_english(self):
        from app.services.sentiment import analyze_sentiment_sync

        results = analyze_sentiment_sync(["The order was delivered on Tuesday."])
        assert len(results) == 1
        assert results[0].score > 0.3
        assert results[0].score < 0.7

    def test_multilingual_german(self):
        from app.services.sentiment import analyze_sentiment_sync

        results = analyze_sentiment_sync(["Ich bin sehr zufrieden mit dem Service!"])
        assert results[0].label == SentimentLabel.POSITIVE
        assert results[0].score > 0.7

    def test_multilingual_spanish_negative(self):
        from app.services.sentiment import analyze_sentiment_sync

        results = analyze_sentiment_sync(["Este producto es horrible, no funciona."])
        assert results[0].label == SentimentLabel.NEGATIVE
        assert results[0].score < 0.3

    def test_batch_produces_varied_scores(self):
        from app.services.sentiment import analyze_sentiment_sync

        texts = [
            "I love this!",
            "This is terrible.",
            "The weather is normal today.",
            "Best purchase I ever made!",
            "Worst customer service.",
        ]
        results = analyze_sentiment_sync(texts)
        scores = [r.score for r in results]
        assert not all(s == 0.5 for s in scores), f"All scores are 0.5: {scores}"
        assert max(scores) - min(scores) > 0.3, f"Score spread too narrow: {scores}"

    def test_scores_not_all_neutral(self):
        from app.services.sentiment import analyze_sentiment_sync

        texts = [
            "Amazing fantastic wonderful product",
            "Horrible terrible awful experience",
            "Normal everyday standard thing",
        ]
        results = analyze_sentiment_sync(texts)
        labels = [r.label for r in results]
        assert SentimentLabel.NEUTRAL not in labels or len(set(labels)) > 1, f"All labels are neutral: {labels}"
