"""Database models for Inbox Agent."""
from __future__ import annotations

import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    JSON, Index,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


class Email(Base):
    """An incoming customer email and its processing lifecycle."""
    __tablename__ = "emails"

    id = Column(String(64), primary_key=True)
    from_name = Column(String(256), default="")
    from_email = Column(String(256), nullable=False)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Classification
    status = Column(String(32), default="unprocessed")  # unprocessed, draft_ready, approved, sent, rejected, escalated
    category = Column(String(64), default="unclassified")  # technical_support, billing, general_inquiry, escalation, spam
    priority = Column(String(16), default="P2")  # P1, P2, P3
    urgency = Column(String(16), default="medium")  # low, medium, high, critical
    sentiment = Column(String(32), default="neutral")  # positive, neutral, negative, angry
    is_spam = Column(Boolean, default=False)

    # Draft & RAG Grounding
    confidence_score = Column(Float, default=0.0)
    draft_response = Column(Text, default="")
    edited_response = Column(Text, default="")
    retrieved_sources = Column(JSON, default=list)
    escalation_reason = Column(Text, default="")
    escalation_id = Column(String(64), default="")

    # Processing metadata
    processed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(128), default="")
    was_auto_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_emails_status", "status"),
        Index("ix_emails_category", "category"),
    )


class CategoryAutonomy(Base):
    """Tracks consecutive human approvals to trigger autonomy transition rule."""
    __tablename__ = "category_autonomy"

    category = Column(String(64), primary_key=True)
    consecutive_approvals = Column(Integer, default=0)
    is_autonomous = Column(Boolean, default=False)
    suggestion_ready = Column(Boolean, default=False)
    suggested_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    total_approved = Column(Integer, default=0)
    total_rejected = Column(Integer, default=0)
    total_edited = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class DraftFeedback(Base):
    """Human edit feedback used as few-shot in-context learning for drafter."""
    __tablename__ = "draft_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(64), nullable=False)
    category = Column(String(64), nullable=False)
    customer_query = Column(Text, default="")
    original_draft = Column(Text, nullable=False)
    edited_draft = Column(Text, nullable=False)
    diff_summary = Column(Text, default="")
    editor_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (Index("ix_feedback_cat", "category"),)


engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if "aiosqlite" not in settings.database_url
    else settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize tables and default category autonomy records."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial categories
    categories = ["technical_support", "billing", "general_inquiry", "escalation", "spam"]
    async with async_session() as session:
        for cat in categories:
            existing = await session.get(CategoryAutonomy, cat)
            if not existing:
                session.add(CategoryAutonomy(category=cat, consecutive_approvals=0, is_autonomous=False))
        await session.commit()
