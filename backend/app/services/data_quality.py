"""Data quality analysis: low confidence, mixed language, duplicate detection."""

from __future__ import annotations

from collections import Counter

from app.models.schemas import AnalyzedEntry, DataQualityReport


def analyze_data_quality(entries: list[AnalyzedEntry]) -> DataQualityReport:
    """Generate data quality report from analyzed entries."""
    if not entries:
        return DataQualityReport(
            total_entries=0,
            low_confidence_count=0,
            low_confidence_entries=[],
            mixed_language_count=0,
            mixed_language_entries=[],
            duplicate_count=0,
            duplicate_entries=[],
            avg_confidence=0.0,
            language_distribution={},
        )

    # Low confidence predictions (< 0.5)
    low_conf = [e for e in entries if e.sentiment.confidence < 0.5]
    low_conf_ids = [e.id for e in low_conf[:50]]

    # Mixed language: entries where detected language differs from majority
    lang_counts = Counter(e.language.language for e in entries)
    majority_lang = lang_counts.most_common(1)[0][0] if lang_counts else "unknown"
    mixed_lang = [e for e in entries if e.language.language != majority_lang and e.language.language != "unknown"]
    mixed_lang_ids = [e.id for e in mixed_lang[:50]]

    # Duplicate detection via text similarity (exact and near-duplicates)
    seen_texts: dict[str, str] = {}
    duplicate_ids = []
    for e in entries:
        normalized = e.text.strip().lower()[:200]
        if normalized in seen_texts:
            duplicate_ids.append(e.id)
        else:
            seen_texts[normalized] = e.id

    # Average confidence
    avg_conf = sum(e.sentiment.confidence for e in entries) / len(entries)

    return DataQualityReport(
        total_entries=len(entries),
        low_confidence_count=len(low_conf),
        low_confidence_entries=low_conf_ids,
        mixed_language_count=len(mixed_lang),
        mixed_language_entries=mixed_lang_ids,
        duplicate_count=len(duplicate_ids),
        duplicate_entries=duplicate_ids[:50],
        avg_confidence=round(avg_conf, 4),
        language_distribution=dict(lang_counts),
    )
