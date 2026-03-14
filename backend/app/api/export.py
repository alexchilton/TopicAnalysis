"""Export API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.security import get_api_key
from app.models.schemas import AnalysisStatus, ExportFormat, FilterParams
from app.services.analysis_pipeline import filter_entries, get_job
from app.services.export import export_entries

router = APIRouter(prefix="/api/v1", tags=["export"])


CONTENT_TYPES = {
    ExportFormat.CSV: "text/csv",
    ExportFormat.JSON: "application/json",
    ExportFormat.PDF: "application/pdf",
}

FILE_EXTENSIONS = {
    ExportFormat.CSV: "csv",
    ExportFormat.JSON: "json",
    ExportFormat.PDF: "pdf",
}


@router.post("/jobs/{job_id}/export")
async def export_results(
    job_id: str,
    fmt: ExportFormat = ExportFormat.CSV,
    filters: FilterParams | None = None,
    api_key: str = Depends(get_api_key),
):
    """Export filtered analysis results."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis not yet completed")

    entries = job.entries
    if filters:
        entries = filter_entries(
            entries,
            date_from=filters.date_from,
            date_to=filters.date_to,
            sentiment_min=filters.sentiment_min,
            sentiment_max=filters.sentiment_max,
            topics=filters.topics,
            languages=filters.languages,
            sources=filters.sources,
            search_text=filters.search_text,
        )

    summary = None
    if job.summary:
        summary = {
            "Total Entries": job.summary.total_entries,
            "Average Sentiment": job.summary.avg_sentiment,
            "Dominant Sentiment": job.summary.dominant_sentiment.value,
            "Topics Found": job.summary.num_topics,
            "Languages": ", ".join(job.summary.languages_detected),
        }

    content = export_entries(entries, fmt, summary)

    return Response(
        content=content,
        media_type=CONTENT_TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename=analysis_{job_id}.{FILE_EXTENSIONS[fmt]}"},
    )
