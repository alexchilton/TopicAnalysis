"""Upload and analysis API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import get_api_key
from app.models.schemas import (
    AnalysisResult,
    AnalysisStatus,
    ComparisonRequest,
    ComparisonResult,
    FilterParams,
    JobStatus,
    TopicInfo,
)
from app.services.analysis_pipeline import (
    filter_entries,
    get_all_jobs,
    get_job,
    run_analysis,
)
from app.services.file_processing import parse_file

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str | None = Query(None, description="Data source label"),
    api_key: str = Depends(get_api_key),
):
    """Upload a file for analysis. Supports CSV, JSON, Excel, ZIP."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Maximum: {settings.max_upload_size_mb}MB",
        )

    try:
        entries = parse_file(content, file.filename, source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not entries:
        raise HTTPException(status_code=400, detail="No valid entries found in the uploaded file")

    job_id = uuid.uuid4().hex[:12]
    logger.info(
        "upload_received", job_id=job_id, filename=file.filename, entries=len(entries), size_mb=round(size_mb, 2)
    )

    background_tasks.add_task(run_analysis, entries, job_id)

    from datetime import datetime

    return JobStatus(
        job_id=job_id,
        status=AnalysisStatus.PENDING,
        progress=0.0,
        message=f"Processing {len(entries)} entries from {file.filename}",
        created_at=datetime.utcnow(),
    )


@router.post("/upload/chunked", response_model=JobStatus)
async def upload_chunked(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_index: int = Query(0, ge=0),
    total_chunks: int = Query(1, ge=1),
    upload_id: str | None = Query(None),
    source: str | None = Query(None),
    api_key: str = Depends(get_api_key),
):
    """Chunked upload for files >10MB."""

    upload_id = upload_id or uuid.uuid4().hex[:12]
    chunk_dir = settings.upload_path / f"chunks_{upload_id}"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    chunk_path = chunk_dir / f"chunk_{chunk_index:04d}"
    chunk_path.write_bytes(content)

    logger.info("chunk_received", upload_id=upload_id, chunk=chunk_index, total=total_chunks)

    if chunk_index + 1 < total_chunks:
        from datetime import datetime

        return JobStatus(
            job_id=upload_id,
            status=AnalysisStatus.PENDING,
            progress=chunk_index / total_chunks,
            message=f"Received chunk {chunk_index + 1}/{total_chunks}",
            created_at=datetime.utcnow(),
        )

    # All chunks received — reassemble
    chunks = sorted(chunk_dir.glob("chunk_*"))
    combined = b"".join(c.read_bytes() for c in chunks)

    # Clean up chunks
    for c in chunks:
        c.unlink()
    chunk_dir.rmdir()

    try:
        filename = file.filename or "upload.csv"
        entries = parse_file(combined, filename, source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not entries:
        raise HTTPException(status_code=400, detail="No valid entries found")

    background_tasks.add_task(run_analysis, entries, upload_id)

    from datetime import datetime

    return JobStatus(
        job_id=upload_id,
        status=AnalysisStatus.PROCESSING,
        progress=0.0,
        message=f"All chunks received. Processing {len(entries)} entries.",
        created_at=datetime.utcnow(),
    )


@router.get("/jobs", response_model=list[JobStatus])
async def list_jobs(api_key: str = Depends(get_api_key)):
    """List all analysis jobs."""
    jobs = get_all_jobs()
    return [
        JobStatus(
            job_id=j.job_id,
            status=j.status,
            progress=1.0 if j.status == AnalysisStatus.COMPLETED else 0.5,
            message="",
            created_at=j.created_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=AnalysisResult)
async def get_job_result(job_id: str, api_key: str = Depends(get_api_key)):
    """Get analysis results for a specific job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str, api_key: str = Depends(get_api_key)):
    """Get status of an analysis job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=1.0 if job.status == AnalysisStatus.COMPLETED else 0.5,
        message="",
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs/{job_id}/filter")
async def filter_job_results(
    job_id: str,
    filters: FilterParams,
    api_key: str = Depends(get_api_key),
):
    """Filter analysis results."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis not yet completed")

    filtered = filter_entries(
        job.entries,
        date_from=filters.date_from,
        date_to=filters.date_to,
        sentiment_min=filters.sentiment_min,
        sentiment_max=filters.sentiment_max,
        topics=filters.topics,
        languages=filters.languages,
        sources=filters.sources,
        search_text=filters.search_text,
    )

    # Paginate
    start = (filters.page - 1) * filters.page_size
    end = start + filters.page_size

    return {
        "total": len(filtered),
        "page": filters.page,
        "page_size": filters.page_size,
        "entries": filtered[start:end],
    }


@router.post("/jobs/{job_id}/compare", response_model=ComparisonResult)
async def compare_segments(
    job_id: str,
    comparison: ComparisonRequest,
    api_key: str = Depends(get_api_key),
):
    """Compare two data segments from the same job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis not yet completed")

    from collections import Counter

    import numpy as np

    from app.models.schemas import AnalysisSummary, SentimentLabel

    seg_a_entries = filter_entries(job.entries, **comparison.segment_a.model_dump(exclude={"page", "page_size"}))
    seg_b_entries = filter_entries(job.entries, **comparison.segment_b.model_dump(exclude={"page", "page_size"}))

    def make_summary(entries):
        if not entries:
            return AnalysisSummary(
                total_entries=0,
                avg_sentiment=0.5,
                dominant_sentiment=SentimentLabel.NEUTRAL,
                num_topics=0,
                top_topics=[],
                languages_detected=[],
            )
        sentiments = [e.sentiment for e in entries]
        topic_counts = Counter(e.topic_id for e in entries)
        return AnalysisSummary(
            total_entries=len(entries),
            avg_sentiment=round(float(np.mean([s.score for s in sentiments])), 4),
            dominant_sentiment=SentimentLabel(Counter(s.label.value for s in sentiments).most_common(1)[0][0]),
            num_topics=len(set(e.topic_id for e in entries) - {-1}),
            top_topics=[
                TopicInfo(topic_id=tid, label=f"Topic {tid}", keywords=[], size=cnt)
                for tid, cnt in topic_counts.most_common(5)
                if tid != -1
            ],
            languages_detected=list(set(e.language.language for e in entries)),
        )

    sum_a = make_summary(seg_a_entries)
    sum_b = make_summary(seg_b_entries)

    topics_a = set(e.topic_id for e in seg_a_entries) - {-1}
    topics_b = set(e.topic_id for e in seg_b_entries) - {-1}

    return ComparisonResult(
        segment_a=sum_a,
        segment_b=sum_b,
        sentiment_delta=round(sum_b.avg_sentiment - sum_a.avg_sentiment, 4),
        topic_changes=[],
        new_topics=[TopicInfo(topic_id=t, label=f"Topic {t}", keywords=[], size=0) for t in topics_b - topics_a],
        disappeared_topics=[
            TopicInfo(topic_id=t, label=f"Topic {t}", keywords=[], size=0) for t in topics_a - topics_b
        ],
    )
