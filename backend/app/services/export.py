"""Export service: CSV, JSON, PDF report generation."""

from __future__ import annotations

import csv
import io
import json

from app.core.logging import get_logger
from app.models.schemas import AnalyzedEntry, ExportFormat

logger = get_logger(__name__)


def export_csv(entries: list[AnalyzedEntry]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "text", "source", "timestamp", "sentiment_label",
        "sentiment_score", "confidence", "language", "topic_id", "topic_label",
    ])
    for e in entries:
        writer.writerow([
            e.id, e.text, e.source or "", e.timestamp or "",
            e.sentiment.label.value, e.sentiment.score, e.sentiment.confidence,
            e.language.language, e.topic_id, e.topic_label,
        ])
    return output.getvalue().encode("utf-8")


def export_json(entries: list[AnalyzedEntry]) -> bytes:
    data = [
        {
            "id": e.id,
            "text": e.text,
            "source": e.source,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "sentiment": {
                "label": e.sentiment.label.value,
                "score": e.sentiment.score,
                "confidence": e.sentiment.confidence,
            },
            "language": {
                "language": e.language.language,
                "confidence": e.language.confidence,
            },
            "topic_id": e.topic_id,
            "topic_label": e.topic_label,
        }
        for e in entries
    ]
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def export_pdf(entries: list[AnalyzedEntry], summary: dict | None = None) -> bytes:
    """Generate a PDF report using reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch  # noqa: F401
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        logger.error("reportlab_not_installed")
        raise ImportError(
            "PDF export requires reportlab. Install it with: pip install reportlab"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18)
    elements.append(Paragraph("Topic Analysis Report", title_style))
    elements.append(Spacer(1, 12))

    # Summary
    if summary:
        elements.append(Paragraph("Summary", styles["Heading2"]))
        for key, val in summary.items():
            elements.append(Paragraph(f"<b>{key}:</b> {val}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Data table
    elements.append(Paragraph("Analysis Results", styles["Heading2"]))
    table_data = [["ID", "Sentiment", "Score", "Language", "Topic"]]

    for e in entries[:500]:  # Limit for PDF
        table_data.append([
            e.id[:8],
            e.sentiment.label.value,
            f"{e.sentiment.score:.2f}",
            e.language.language,
            e.topic_label[:30],
        ])

    table = Table(table_data, colWidths=[60, 70, 50, 60, 180])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))

    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()


def export_entries(entries: list[AnalyzedEntry], fmt: ExportFormat, summary: dict | None = None) -> bytes:
    if fmt == ExportFormat.CSV:
        return export_csv(entries)
    elif fmt == ExportFormat.JSON:
        return export_json(entries)
    elif fmt == ExportFormat.PDF:
        return export_pdf(entries, summary)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
