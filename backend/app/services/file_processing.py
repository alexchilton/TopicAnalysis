"""File processing service: handles CSV, JSON, Excel, ZIP with chunked uploads."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import FeedbackEntry

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls", ".zip"}
TEXT_COLUMN_CANDIDATES = [
    "text",
    "content",
    "message",
    "body",
    "feedback",
    "review",
    "comment",
    "description",
    "note",
    "summary",
    "title",
    "Text",
    "Content",
    "Message",
    "Body",
    "Feedback",
    "Review",
]
TIMESTAMP_COLUMN_CANDIDATES = [
    "timestamp",
    "date",
    "created_at",
    "created",
    "time",
    "datetime",
    "Timestamp",
    "Date",
    "Created",
    "CreatedAt",
]
SOURCE_COLUMN_CANDIDATES = [
    "source",
    "channel",
    "platform",
    "origin",
    "category",
    "type",
    "Source",
    "Channel",
    "Platform",
]


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        for candidate in candidates:
            if candidate.lower() in col.lower():
                return col
    return None


def _df_to_entries(df: pd.DataFrame, source: str | None = None) -> list[FeedbackEntry]:
    text_col = _find_column(df, TEXT_COLUMN_CANDIDATES)
    if not text_col:
        if len(df.columns) == 1:
            text_col = df.columns[0]
        else:
            raise ValueError(
                f"No text column found. Expected one of: {TEXT_COLUMN_CANDIDATES}. Found columns: {list(df.columns)}"
            )

    ts_col = _find_column(df, TIMESTAMP_COLUMN_CANDIDATES)
    src_col = _find_column(df, SOURCE_COLUMN_CANDIDATES)

    entries = []
    other_cols = [c for c in df.columns if c not in {text_col, ts_col, src_col}]

    for _, row in df.iterrows():
        text = str(row[text_col]).strip()
        if not text or text == "nan":
            continue

        ts = None
        if ts_col and pd.notna(row.get(ts_col)):
            try:
                ts = pd.to_datetime(row[ts_col])
            except Exception:
                pass

        src = source
        if src_col and pd.notna(row.get(src_col)):
            src = str(row[src_col])

        metadata = {}
        for col in other_cols:
            val = row.get(col)
            if pd.notna(val):
                metadata[col] = str(val) if not isinstance(val, (int, float, bool)) else val

        entries.append(
            FeedbackEntry(
                id=uuid.uuid4().hex[:12],
                text=text,
                source=src,
                timestamp=ts,
                metadata=metadata if metadata else None,
            )
        )

    return entries


def parse_csv(content: bytes, source: str | None = None) -> list[FeedbackEntry]:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            return _df_to_entries(df, source)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to decode CSV file with supported encodings")


def parse_json(content: bytes, source: str | None = None) -> list[FeedbackEntry]:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list):
        if all(isinstance(item, str) for item in data):
            return [FeedbackEntry(id=uuid.uuid4().hex[:12], text=item, source=source) for item in data if item.strip()]
        df = pd.DataFrame(data)
        return _df_to_entries(df, source)
    elif isinstance(data, dict):
        if "data" in data:
            df = pd.DataFrame(data["data"])
        elif "entries" in data:
            df = pd.DataFrame(data["entries"])
        elif "results" in data:
            df = pd.DataFrame(data["results"])
        else:
            df = pd.DataFrame([data])
        return _df_to_entries(df, source)

    raise ValueError("Unsupported JSON structure")


def parse_excel(content: bytes, source: str | None = None) -> list[FeedbackEntry]:
    df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    return _df_to_entries(df, source)


def parse_zip(content: bytes, source: str | None = None) -> list[FeedbackEntry]:
    all_entries = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            if name.startswith("__MACOSX") or name.startswith("."):
                continue
            ext = Path(name).suffix.lower()
            inner = zf.read(name)
            file_source = source or Path(name).stem
            try:
                if ext == ".csv":
                    all_entries.extend(parse_csv(inner, file_source))
                elif ext == ".json":
                    all_entries.extend(parse_json(inner, file_source))
                elif ext in (".xlsx", ".xls"):
                    all_entries.extend(parse_excel(inner, file_source))
                else:
                    logger.warning("skipping_unsupported_file_in_zip", filename=name)
            except Exception as exc:
                logger.error("error_processing_zip_entry", filename=name, error=str(exc))
    return all_entries


def parse_file(content: bytes, filename: str, source: str | None = None) -> list[FeedbackEntry]:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    parsers = {
        ".csv": parse_csv,
        ".json": parse_json,
        ".xlsx": parse_excel,
        ".xls": parse_excel,
        ".zip": parse_zip,
    }

    return parsers[ext](content, source)


async def save_upload(content: bytes, filename: str) -> Path:
    upload_dir = settings.upload_path
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(filename).name}"
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)
    return file_path
