"""Language detection with langdetect primary and cld3 fallback."""

from __future__ import annotations

from app.core.logging import get_logger
from app.models.schemas import LanguageResult

logger = get_logger(__name__)


def detect_language(text: str) -> LanguageResult:
    """Detect language using langdetect with cld3 fallback."""
    if not text or len(text.strip()) < 3:
        return LanguageResult(language="unknown", confidence=0.0, method="none")

    # Primary: langdetect
    try:
        from langdetect import DetectorFactory, detect_langs

        DetectorFactory.seed = 42
        results = detect_langs(text)
        if results:
            top = results[0]
            return LanguageResult(
                language=str(top.lang),
                confidence=round(top.prob, 4),
                method="langdetect",
            )
    except Exception as exc:
        logger.debug("langdetect_failed", error=str(exc))

    # Fallback: cld3
    try:
        import cld3

        result = cld3.get_language(text)
        if result and result.is_reliable:
            return LanguageResult(
                language=result.language,
                confidence=round(result.probability, 4),
                method="cld3",
            )
        elif result:
            return LanguageResult(
                language=result.language,
                confidence=round(result.probability, 4),
                method="cld3",
            )
    except ImportError:
        logger.warning("cld3_not_available", detail="Install pycld3 for fallback detection")
    except Exception as exc:
        logger.debug("cld3_failed", error=str(exc))

    return LanguageResult(language="unknown", confidence=0.0, method="none")


def detect_languages_batch(texts: list[str]) -> list[LanguageResult]:
    return [detect_language(t) for t in texts]
