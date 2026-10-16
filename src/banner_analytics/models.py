from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Website(Base):
    __tablename__ = "websites"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaptureRun(Base):
    __tablename__ = "capture_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("websites.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="running", nullable=False)
    banners_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    website: Mapped[Website] = relationship()


class Banner(Base):
    __tablename__ = "banners"
    __table_args__ = (
        UniqueConstraint("capture_run_id", "position", "content_hash"),
        Index("ix_banners_captured_source", "captured_at", "website_id"),
        Index("ix_banners_content_hash", "content_hash"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capture_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capture_runs.id"), nullable=False)
    website_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("websites.id"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    unique_identifier: Mapped[str] = mapped_column(String(160), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    perceptual_hash: Mapped[str | None] = mapped_column(String(32))
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary)
    source_image_url: Mapped[str | None] = mapped_column(Text)
    clickthrough_url: Mapped[str | None] = mapped_column(Text)
    ocr_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    headline: Mapped[str | None] = mapped_column(Text)
    subheadline: Mapped[str | None] = mapped_column(Text)
    cta_text: Mapped[str | None] = mapped_column(String(160))
    terms_reference: Mapped[str | None] = mapped_column(Text)
    detected_brands: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    social_platforms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    promotional_keywords: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    primary_colours: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    visual_flags: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    automated_description: Mapped[str | None] = mapped_column(Text)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    website: Mapped[Website] = relationship()
    categories: Mapped[list[BannerCategory]] = relationship(cascade="all, delete-orphan")
    monetary_values: Mapped[list[MonetaryValue]] = relationship(cascade="all, delete-orphan")
    detected_dates: Mapped[list[DetectedDate]] = relationship(cascade="all, delete-orphan")


class BannerCategory(Base):
    __tablename__ = "banner_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    banner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("banners.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1"))
    rule_version: Mapped[str] = mapped_column(String(40), default="v1")


class MonetaryValue(Base):
    __tablename__ = "monetary_values"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    banner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("banners.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class DetectedDate(Base):
    __tablename__ = "detected_dates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    banner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("banners.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(String(150), nullable=False)
    date_type: Mapped[str] = mapped_column(String(40), default="unspecified")
    parsed_date: Mapped[date | None] = mapped_column(Date)


class SchedulerSetting(Base):
    __tablename__ = "scheduler_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

