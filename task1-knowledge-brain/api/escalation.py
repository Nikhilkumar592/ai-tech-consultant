"""Escalation management for human-in-the-loop QA."""
from __future__ import annotations

import datetime
import hashlib
import logging
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Escalation, async_session
from app.models import (
    EscalationCreateRequest,
    EscalationResolveRequest,
    EscalationResponse,
)
from retrieval.vector_store import add_chunks

logger = logging.getLogger(__name__)


async def create_escalation(
    question: str,
    context: str = "",
    reason: str = "",
    retrieved_evidence: list[dict[str, Any]] | None = None,
) -> str:
    """Create a new human escalation record."""
    escalation_id = str(uuid.uuid4())[:12]

    async with async_session() as session:
        esc = Escalation(
            id=escalation_id,
            question=question,
            context=context,
            reason=reason or "Low confidence or requires human verification",
            retrieved_evidence=retrieved_evidence or [],
            status="open",
            created_at=datetime.datetime.utcnow(),
        )
        session.add(esc)
        await session.commit()

    logger.info(f"Created escalation {escalation_id} for question: {question[:80]}")
    return escalation_id


async def get_escalation(escalation_id: str) -> EscalationResponse | None:
    """Get an escalation by ID."""
    async with async_session() as session:
        result = await session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        )
        esc = result.scalar_one_or_none()
        if not esc:
            return None

        return EscalationResponse(
            id=esc.id,
            question=esc.question,
            context=esc.context or "",
            reason=esc.reason or "",
            status=esc.status,
            expert_answer=esc.expert_answer or "",
            expert_name=esc.expert_name or "",
            created_at=esc.created_at,
            resolved_at=esc.resolved_at,
        )


async def list_escalations(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[EscalationResponse]:
    """List escalations with optional status filter."""
    async with async_session() as session:
        query = select(Escalation)
        if status:
            query = query.where(Escalation.status == status)
        query = query.order_by(Escalation.created_at.desc()).offset(offset).limit(limit)

        result = await session.execute(query)
        items = result.scalars().all()

        return [
            EscalationResponse(
                id=item.id,
                question=item.question,
                context=item.context or "",
                reason=item.reason or "",
                status=item.status,
                expert_answer=item.expert_answer or "",
                expert_name=item.expert_name or "",
                created_at=item.created_at,
                resolved_at=item.resolved_at,
            )
            for item in items
        ]


async def resolve_escalation(
    escalation_id: str,
    resolve_data: EscalationResolveRequest,
) -> EscalationResponse | None:
    """Resolve an escalation with expert answer and re-index into vector store."""
    async with async_session() as session:
        result = await session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        )
        esc = result.scalar_one_or_none()
        if not esc:
            return None

        now = datetime.datetime.utcnow()
        esc.status = "resolved"
        esc.expert_answer = resolve_data.expert_answer
        esc.expert_name = resolve_data.expert_name or "Domain Expert"
        esc.expert_sources = resolve_data.expert_sources
        esc.resolution_notes = resolve_data.resolution_notes
        esc.resolved_at = now

        await session.commit()
        await session.refresh(esc)

        # Index verified Q&A into vector store for future queries
        try:
            chunk_content = (
                f"Question: {esc.question}\n"
                f"Expert Answer: {resolve_data.expert_answer}\n"
                f"Verified by: {esc.expert_name}"
            )
            chunk_id = f"esc_{escalation_id}"
            add_chunks(
                chunk_ids=[chunk_id],
                texts=[chunk_content],
                metadatas=[{
                    "article_id": f"escalation_{escalation_id}",
                    "article_title": f"Verified Q&A: {esc.question[:60]}",
                    "article_url": f"/escalations/{escalation_id}",
                    "category": "Expert Verified Q&A",
                    "source_type": "escalation",
                }],
            )
            logger.info(f"Re-indexed resolved escalation {escalation_id} into vector store")
        except Exception as e:
            logger.warning(f"Could not index resolved escalation into vector store: {e}")

        return EscalationResponse(
            id=esc.id,
            question=esc.question,
            context=esc.context or "",
            reason=esc.reason or "",
            status=esc.status,
            expert_answer=esc.expert_answer or "",
            expert_name=esc.expert_name or "",
            created_at=esc.created_at,
            resolved_at=esc.resolved_at,
        )
