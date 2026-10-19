"""SQLAlchemy database models for Knowledge Brain."""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    JSON, ForeignKey, Index, create_engine, event,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Article(Base):
    """A help center article."""
    __tablename__ = "articles"

    id = Column(String(64), primary_key=True)  # stable hash of URL
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(512), nullable=False, default="")
    content_raw = Column(Text, nullable=False, default="")
    content_text = Column(Text, nullable=False, default="")
    content_hash = Column(String(64), nullable=False, default="")
    category = Column(String(256), default="")
    folder = Column(String(256), default="")
    headings = Column(JSON, default=list)
    links = Column(JSON, default=list)
    image_urls = Column(JSON, default=list)
    metadata_extra = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    last_modified = Column(String(64), default="")
    first_ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    ingestion_status = Column(String(32), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, default="")
    retry_count = Column(Integer, default=0)

    chunks = relationship("Chunk", back_populates="article", cascade="all, delete-orphan")
    images = relationship("ArticleImage", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_articles_status", "ingestion_status"),
        Index("ix_articles_active", "is_active"),
    )


class Chunk(Base):
    """A text chunk from an article, ready for embedding."""
    __tablename__ = "chunks"

    id = Column(String(64), primary_key=True)
    article_id = Column(String(64), ForeignKey("articles.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    heading = Column(String(512), default="")
    metadata_extra = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    article = relationship("Article", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_article", "article_id"),
        Index("ix_chunks_active", "is_active"),
    )


class ArticleImage(Base):
    """An image associated with an article."""
    __tablename__ = "article_images"

    id = Column(String(64), primary_key=True)
    article_id = Column(String(64), ForeignKey("articles.id"), nullable=False)
    image_url = Column(String(2048), nullable=False)
    local_path = Column(String(512), default="")
    alt_text = Column(Text, default="")
    surrounding_text = Column(Text, default="")
    vision_description = Column(Text, default="")
    content_hash = Column(String(64), default="")
    is_downloaded = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    article = relationship("Article", back_populates="images")

    __table_args__ = (Index("ix_images_article", "article_id"),)


class Escalation(Base):
    """A question escalated to a human expert."""
    __tablename__ = "escalations"

    id = Column(String(64), primary_key=True)
    question = Column(Text, nullable=False)
    context = Column(Text, default="")
    retrieved_evidence = Column(JSON, default=list)
    reason = Column(Text, default="")
    status = Column(String(32), default="open")  # open, resolved, dismissed
    expert_answer = Column(Text, default="")
    expert_sources = Column(JSON, default=list)
    expert_name = Column(String(256), default="")
    resolution_notes = Column(Text, default="")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_escalations_status", "status"),)


class IngestionJob(Base):
    """Tracks ingestion runs."""
    __tablename__ = "ingestion_jobs"

    id = Column(String(64), primary_key=True)
    job_type = Column(String(32), default="full")  # full, incremental
    status = Column(String(32), default="pending")  # pending, running, completed, failed
    total_urls = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    added = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    removed = Column(Integer, default=0)
    unchanged = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PromptVersion(Base):
    """Versioned prompt registry."""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False)
    purpose = Column(Text, default="")
    template = Column(Text, nullable=False)
    model = Column(String(128), default="")
    output_schema = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    change_reason = Column(Text, default="")
    eval_results = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_prompts_name_version", "name", "version", unique=True),
        Index("ix_prompts_active", "name", "is_active"),
    )


# Engine and session
engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if "aiosqlite" not in settings.database_url
    else settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session() as session:
        yield session
