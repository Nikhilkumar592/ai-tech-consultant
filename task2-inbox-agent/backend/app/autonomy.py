"""Autonomy management: 20-consecutive-approval transition rule."""
from __future__ import annotations

import datetime
import logging
from typing import Any
from sqlalchemy import select

from app.config import settings
from app.database import CategoryAutonomy, async_session

logger = logging.getLogger(__name__)


async def record_approval(category: str) -> dict[str, Any]:
    """Record a human approval for an email draft in a category."""
    async with async_session() as session:
        record = await session.get(CategoryAutonomy, category)
        if not record:
            record = CategoryAutonomy(category=category, consecutive_approvals=0, is_autonomous=False)
            session.add(record)

        record.consecutive_approvals += 1
        record.total_approved += 1
        record.updated_at = datetime.datetime.utcnow()

        # Check 20-consecutive-approval threshold
        if (
            record.consecutive_approvals >= settings.autonomy_approval_threshold
            and not record.is_autonomous
        ):
            record.suggestion_ready = True
            record.suggested_at = datetime.datetime.utcnow()
            logger.info(
                f"AUTONOMY TRIGGER: Category '{category}' reached {record.consecutive_approvals} "
                f"consecutive approvals! Suggesting autonomous mode."
            )

        await session.commit()
        await session.refresh(record)

        return {
            "category": record.category,
            "consecutive_approvals": record.consecutive_approvals,
            "is_autonomous": record.is_autonomous,
            "suggestion_ready": record.suggestion_ready,
        }


async def record_rejection(category: str) -> dict[str, Any]:
    """Record a draft rejection, resetting consecutive approval streak to zero."""
    async with async_session() as session:
        record = await session.get(CategoryAutonomy, category)
        if not record:
            record = CategoryAutonomy(category=category, consecutive_approvals=0, is_autonomous=False)
            session.add(record)

        # Reset streak on rejection
        old_streak = record.consecutive_approvals
        record.consecutive_approvals = 0
        record.suggestion_ready = False
        record.total_rejected += 1
        record.updated_at = datetime.datetime.utcnow()

        logger.info(f"Rejection in '{category}': Reset streak from {old_streak} to 0.")
        await session.commit()
        await session.refresh(record)

        return {
            "category": record.category,
            "consecutive_approvals": record.consecutive_approvals,
            "is_autonomous": record.is_autonomous,
        }


async def record_edit(category: str) -> None:
    """Record a human edit to an AI draft."""
    async with async_session() as session:
        record = await session.get(CategoryAutonomy, category)
        if record:
            record.total_edited += 1
            record.updated_at = datetime.datetime.utcnow()
            await session.commit()


async def toggle_autonomy(category: str, enable: bool, confirmed_by: str = "Lead") -> dict[str, Any]:
    """Human confirmation to enable or disable autonomous sending for a category."""
    async with async_session() as session:
        record = await session.get(CategoryAutonomy, category)
        if not record:
            record = CategoryAutonomy(category=category)
            session.add(record)

        record.is_autonomous = enable
        record.suggestion_ready = False
        if enable:
            record.confirmed_at = datetime.datetime.utcnow()
        record.updated_at = datetime.datetime.utcnow()

        logger.info(f"Autonomy for category '{category}' set to {enable} by {confirmed_by}")
        await session.commit()
        await session.refresh(record)

        return {
            "category": record.category,
            "is_autonomous": record.is_autonomous,
            "confirmed_at": record.confirmed_at,
        }


async def get_all_autonomy_statuses() -> list[dict[str, Any]]:
    """Retrieve current autonomy status and approval streaks for all categories."""
    async with async_session() as session:
        result = await session.execute(select(CategoryAutonomy).order_by(CategoryAutonomy.category))
        records = result.scalars().all()

        return [
            {
                "category": r.category,
                "consecutive_approvals": r.consecutive_approvals,
                "is_autonomous": r.is_autonomous,
                "suggestion_ready": r.suggestion_ready,
                "suggested_at": r.suggested_at,
                "confirmed_at": r.confirmed_at,
                "total_approved": r.total_approved,
                "total_rejected": r.total_rejected,
                "total_edited": r.total_edited,
                "target_threshold": settings.autonomy_approval_threshold,
            }
            for r in records
        ]
