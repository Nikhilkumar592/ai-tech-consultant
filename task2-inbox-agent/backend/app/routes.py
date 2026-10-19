"""FastAPI router for Intelligent Inbox Agent."""
from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, update

from app.autonomy import (
    get_all_autonomy_statuses,
    record_approval,
    record_edit,
    record_rejection,
    toggle_autonomy,
)
from app.classifier import classify_email
from app.config import settings
from app.database import Email, async_session
from app.drafter import generate_draft_response
from app.feedback import save_draft_feedback
from app.models import (
    AutonomyCategoryStatus,
    AutonomyToggleRequest,
    EmailApproveRequest,
    EmailDetail,
    EmailEditRequest,
    EmailSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Emails List & Detail ──

@router.get("/emails", response_model=list[EmailSummary])
async def list_emails(
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    urgency: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List inbox emails with optional filters."""
    async with async_session() as session:
        query = select(Email)
        if category:
            query = query.where(Email.category == category)
        if status_filter:
            query = query.where(Email.status == status_filter)
        if urgency:
            query = query.where(Email.urgency == urgency)

        query = query.order_by(Email.received_at.desc()).offset(offset).limit(limit)
        result = await session.execute(query)
        emails = result.scalars().all()

        return [
            EmailSummary(
                id=e.id,
                from_name=e.from_name,
                from_email=e.from_email,
                subject=e.subject,
                received_at=e.received_at,
                status=e.status,
                category=e.category,
                priority=e.priority,
                urgency=e.urgency,
                sentiment=e.sentiment,
                confidence_score=e.confidence_score,
                is_spam=e.is_spam,
                escalation_reason=e.escalation_reason or "",
            )
            for e in emails
        ]


@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """Get full details of an email including body and draft response."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        return EmailDetail(
            id=email.id,
            from_name=email.from_name,
            from_email=email.from_email,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
            status=email.status,
            category=email.category,
            priority=email.priority,
            urgency=email.urgency,
            sentiment=email.sentiment,
            confidence_score=email.confidence_score,
            is_spam=email.is_spam,
            draft_response=email.draft_response or "",
            edited_response=email.edited_response or "",
            retrieved_sources=email.retrieved_sources or [],
            escalation_reason=email.escalation_reason or "",
            escalation_id=email.escalation_id or "",
            processed_at=email.processed_at,
            resolved_at=email.resolved_at,
            reviewed_by=email.reviewed_by or "",
            was_auto_sent=email.was_auto_sent,
        )


# ── AI Processing ──

@router.post("/emails/{email_id}/process", response_model=EmailDetail)
async def process_email(email_id: str):
    """Run classification, knowledge retrieval, and grounded draft generation."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        # 1. Classify
        classification = classify_email(email.subject, email.body)
        email.category = classification["category"]
        email.priority = classification["priority"]
        email.urgency = classification["urgency"]
        email.sentiment = classification["sentiment"]
        email.is_spam = classification["is_spam"]

        # 2. Draft response with grounding
        draft_result = await generate_draft_response(
            from_name=email.from_name,
            subject=email.subject,
            body=email.body,
            category=email.category,
        )

        email.draft_response = draft_result["draft"]
        email.confidence_score = draft_result["confidence"]
        email.retrieved_sources = draft_result["sources"]
        email.processed_at = datetime.datetime.utcnow()

        if draft_result["needs_escalation"]:
            email.status = "escalated"
            email.escalation_reason = draft_result["escalation_reason"]
        elif email.is_spam:
            email.status = "rejected"
        else:
            email.status = "draft_ready"

        await session.commit()
        await session.refresh(email)

        return await get_email(email_id)


@router.post("/emails/process-all")
async def process_all_emails():
    """Batch process all unprocessed emails."""
    count = 0
    async with async_session() as session:
        result = await session.execute(
            select(Email.id).where(Email.status == "unprocessed")
        )
        email_ids = [row[0] for row in result.all()]

    for eid in email_ids:
        try:
            await process_email(eid)
            count += 1
        except Exception as e:
            logger.error(f"Error processing email {eid}: {e}")

    return {"message": f"Successfully processed {count} emails", "total_processed": count}


# ── Human Review Actions ──

@router.post("/emails/{email_id}/approve", response_model=EmailDetail)
async def approve_draft(email_id: str, request: EmailApproveRequest | None = None):
    """Approve draft for sending, incrementing category streak."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.status = "approved"
        email.reviewed_by = request.reviewer_name if request else "Support Specialist"
        email.resolved_at = datetime.datetime.utcnow()
        await session.commit()

        # Update category autonomy counter
        await record_approval(email.category)

    return await get_email(email_id)


@router.post("/emails/{email_id}/edit", response_model=EmailDetail)
async def edit_draft(email_id: str, request: EmailEditRequest):
    """Human edits AI draft. Captures diff as few-shot learning example."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        original = email.draft_response
        email.edited_response = request.edited_draft
        email.reviewed_by = request.editor_name
        email.status = "approved"
        email.resolved_at = datetime.datetime.utcnow()
        await session.commit()

        # Save feedback for future in-context few-shot learning
        await save_draft_feedback(
            email_id=email.id,
            category=email.category,
            customer_query=f"{email.subject}\n{email.body}",
            original_draft=original,
            edited_draft=request.edited_draft,
            editor_notes=request.editor_notes,
        )
        await record_edit(email.category)

    return await get_email(email_id)


@router.post("/emails/{email_id}/reject", response_model=EmailDetail)
async def reject_draft(email_id: str):
    """Reject AI draft. Resets category streak to 0."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.status = "rejected"
        email.resolved_at = datetime.datetime.utcnow()
        await session.commit()

        # Reset consecutive approval streak
        await record_rejection(email.category)

    return await get_email(email_id)


@router.post("/emails/{email_id}/escalate", response_model=EmailDetail)
async def escalate_email(email_id: str, reason: str = Query("Manual agent escalation")):
    """Escalate email to human expert queue."""
    async with async_session() as session:
        email = await session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.status = "escalated"
        email.escalation_reason = reason
        email.resolved_at = datetime.datetime.utcnow()
        await session.commit()

    return await get_email(email_id)


# ── Autonomy Controls ──

@router.get("/autonomy/status", response_model=list[AutonomyCategoryStatus])
async def get_autonomy_status():
    """Get current approval streaks and autonomy transition state."""
    statuses = await get_all_autonomy_statuses()
    return [AutonomyCategoryStatus(**s) for s in statuses]


@router.post("/autonomy/toggle")
async def toggle_category_autonomy(request: AutonomyToggleRequest):
    """Enable or disable autonomous mode for a category upon human confirmation."""
    result = await toggle_autonomy(
        category=request.category,
        enable=request.enable_autonomous,
        confirmed_by=request.confirmed_by,
    )
    return result


# ── Seed Data ──

@router.post("/inbox/seed")
async def seed_sample_emails():
    """Load the 50 sample customer emails from sample-data."""
    # Look in common parent directory locations
    candidates = [
        settings.base_dir.parent.parent / "sample-data" / "sample_emails" / "emails.json",
        settings.base_dir.parent / "sample-data" / "sample_emails" / "emails.json",
        Path("sample-data/sample_emails/emails.json"),
        Path("../sample-data/sample_emails/emails.json"),
        Path("../../sample-data/sample_emails/emails.json"),
    ]
    sample_file = next((p for p in candidates if p.exists()), None)
    if not sample_file:
        raise HTTPException(status_code=404, detail="Sample file not found in candidates")

    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    count_added = 0
    async with async_session() as session:
        for item in data:
            existing = await session.get(Email, item["id"])
            if not existing:
                received = datetime.datetime.fromisoformat(item["received_at"].replace("Z", "+00:00"))
                email = Email(
                    id=item["id"],
                    from_name=item["from_name"],
                    from_email=item["from_email"],
                    subject=item["subject"],
                    body=item["body"],
                    received_at=received,
                    status="unprocessed",
                )
                session.add(email)
                count_added += 1

        await session.commit()

    return {"message": f"Successfully seeded {count_added} emails", "count": count_added}
