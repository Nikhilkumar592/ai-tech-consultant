"""Feedback learning mechanism: captures human edits to improve future drafts."""
from __future__ import annotations

import datetime
import difflib
import logging
from sqlalchemy import select

from app.database import DraftFeedback, async_session

logger = logging.getLogger(__name__)


async def save_draft_feedback(
    email_id: str,
    category: str,
    customer_query: str,
    original_draft: str,
    edited_draft: str,
    editor_notes: str = "",
) -> int:
    """Save human edit diff as in-context few-shot learning example."""
    # Compute diff summary
    matcher = difflib.SequenceMatcher(None, original_draft, edited_draft)
    ratio = matcher.ratio()

    diff_lines = list(difflib.unified_diff(
        original_draft.splitlines(),
        edited_draft.splitlines(),
        fromfile="original_draft",
        tofile="edited_draft",
        lineterm=""
    ))
    diff_summary = f"Similarity: {ratio:.1%}. Modified {len(diff_lines)} lines.\n" + "\n".join(diff_lines[:15])

    async with async_session() as session:
        feedback = DraftFeedback(
            email_id=email_id,
            category=category,
            customer_query=customer_query[:1000],
            original_draft=original_draft,
            edited_draft=edited_draft,
            diff_summary=diff_summary,
            editor_notes=editor_notes,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

    logger.info(f"Recorded draft feedback for email {email_id} (category: {category})")
    return feedback.id


async def get_recent_feedback(category: str, limit: int = 5) -> list[dict]:
    """Retrieve recent feedback examples for prompt injection or review."""
    async with async_session() as session:
        result = await session.execute(
            select(DraftFeedback)
            .where(DraftFeedback.category == category)
            .order_by(DraftFeedback.created_at.desc())
            .limit(limit)
        )
        items = result.scalars().all()
        return [
            {
                "id": f.id,
                "email_id": f.email_id,
                "category": f.category,
                "customer_query": f.customer_query,
                "diff_summary": f.diff_summary,
                "editor_notes": f.editor_notes,
                "created_at": f.created_at,
            }
            for f in items
        ]
