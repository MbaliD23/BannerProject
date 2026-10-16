from __future__ import annotations

from datetime import date, datetime, time, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .database import session_scope
from .models import Banner, CaptureRun, Website


EXPORT_COLUMNS = [
    "capture_date",
    "website",
    "position",
    "headline",
    "categories",
    "ocr_text",
    "monetary_values",
    "detected_dates",
    "keywords",
    "brands",
    "image_path",
    "is_new",
]


def load_banner_frame() -> pd.DataFrame:
    with session_scope() as session:
        rows = session.execute(
            select(Banner)
            .options(
                selectinload(Banner.website),
                selectinload(Banner.categories),
                selectinload(Banner.monetary_values),
                selectinload(Banner.detected_dates),
            )
            .order_by(Banner.captured_at.desc())
        ).scalars().all()
        data = []
        for banner in rows:
            data.append(
                {
                    "id": str(banner.id),
                    "capture_date": banner.captured_at,
                    "website": banner.website.name,
                    "position": banner.position,
                    "headline": banner.headline or "Untitled promotion",
                    "categories": ", ".join(item.category for item in banner.categories),
                    "category_list": [item.category for item in banner.categories],
                    "ocr_text": banner.ocr_text,
                    "monetary_values": ", ".join(str(item.amount) for item in banner.monetary_values),
                    "max_prize": max((float(item.amount) for item in banner.monetary_values), default=0.0),
                    "detected_dates": ", ".join(str(item.parsed_date or item.raw_text) for item in banner.detected_dates),
                    "keywords": ", ".join(banner.promotional_keywords),
                    "brands": ", ".join(banner.detected_brands),
                    "image_path": banner.image_path,
                    "description": banner.automated_description or "",
                    "is_new": banner.is_new,
                    "is_active": banner.is_active,
                    "colours": banner.primary_colours,
                }
            )
    return pd.DataFrame(data)


def load_runs_frame() -> pd.DataFrame:
    with session_scope() as session:
        rows = session.execute(
            select(CaptureRun, Website.name)
            .join(Website, Website.id == CaptureRun.website_id)
            .order_by(CaptureRun.started_at.desc())
            .limit(100)
        ).all()
        return pd.DataFrame(
            [
                {
                    "website": name,
                    "started_at": run.started_at,
                    "finished_at": run.finished_at,
                    "status": run.status,
                    "banners_found": run.banners_found,
                    "error": run.error_message,
                }
                for run, name in rows
            ]
        )


def filter_frame(
    frame: pd.DataFrame,
    websites: list[str] | None = None,
    categories: list[str] | None = None,
    date_range: tuple[date, date] | None = None,
    keyword: str = "",
    min_prize: float = 0,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    filtered = frame.copy()
    if websites:
        filtered = filtered[filtered["website"].isin(websites)]
    if categories:
        filtered = filtered[filtered["category_list"].apply(lambda values: bool(set(values) & set(categories)))]
    if date_range:
        start = datetime.combine(date_range[0], time.min, tzinfo=timezone.utc)
        end = datetime.combine(date_range[-1], time.max, tzinfo=timezone.utc)
        dates = pd.to_datetime(filtered["capture_date"], utc=True)
        filtered = filtered[(dates >= start) & (dates <= end)]
    if keyword.strip():
        needle = keyword.strip().lower()
        haystack = filtered[["headline", "ocr_text", "keywords", "brands"]].fillna("").agg(" ".join, axis=1).str.lower()
        filtered = filtered[haystack.str.contains(needle, regex=False)]
    if min_prize:
        filtered = filtered[filtered["max_prize"] >= min_prize]
    return filtered

