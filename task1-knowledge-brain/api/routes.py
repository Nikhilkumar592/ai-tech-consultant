"""FastAPI route handlers for Knowledge Brain."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, select

from app.config import settings
from app.database import Article, Chunk, Escalation, IngestionJob, async_session
from app.models import (
    ErrorResponse,
    EscalationCreateRequest,
    EscalationResolveRequest,
    EscalationResponse,
    HealthResponse,
    IngestionRunRequest,
    IngestionStatusResponse,
    QueryRequest,
    QueryResponse,
)
from api.escalation import (
    create_escalation,
    get_escalation,
    list_escalations,
    resolve_escalation,
)
from ingestion.pipeline import run_ingestion
from retrieval.rag import answer_question
from retrieval.vector_store import get_stats as get_vector_stats

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health & Stats ──

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint verifying database and vector store connectivity."""
    db_status = "connected"
    articles_count = 0
    chunks_count = 0

    try:
        async with async_session() as session:
            art_res = await session.execute(
                select(func.count()).select_from(Article).where(Article.is_active == True)
            )
            articles_count = art_res.scalar() or 0

            chk_res = await session.execute(
                select(func.count()).select_from(Chunk).where(Chunk.is_active == True)
            )
            chunks_count = chk_res.scalar() or 0
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"unhealthy: {e}"

    vector_status = "connected"
    try:
        v_stats = get_vector_stats()
        vector_chunks = v_stats.get("total_chunks", 0)
    except Exception as e:
        logger.warning(f"Vector store health check issue: {e}")
        vector_status = f"degraded: {e}"
        vector_chunks = 0

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="knowledge-brain",
        version="1.0.0",
        database=db_status,
        vector_store=vector_status,
        articles_count=articles_count,
        chunks_count=chunks_count or vector_chunks,
        mock_mode=settings.mock_mode or not settings.has_anthropic_key,
    )


@router.get("/stats")
async def get_system_stats():
    """Detailed system statistics for monitoring."""
    async with async_session() as session:
        total_articles = (await session.execute(select(func.count(Article.id)))).scalar() or 0
        active_articles = (await session.execute(
            select(func.count(Article.id)).where(Article.is_active == True)
        )).scalar() or 0
        total_chunks = (await session.execute(select(func.count(Chunk.id)))).scalar() or 0
        open_escalations = (await session.execute(
            select(func.count(Escalation.id)).where(Escalation.status == "open")
        )).scalar() or 0
        resolved_escalations = (await session.execute(
            select(func.count(Escalation.id)).where(Escalation.status == "resolved")
        )).scalar() or 0

        latest_job = (await session.execute(
            select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(1)
        )).scalar_one_or_none()

    v_stats = get_vector_stats()

    return {
        "articles": {
            "total": total_articles,
            "active": active_articles,
        },
        "chunks": {
            "database_count": total_chunks,
            "vector_store_count": v_stats.get("total_chunks", 0),
        },
        "escalations": {
            "open": open_escalations,
            "resolved": resolved_escalations,
        },
        "latest_ingestion": {
            "id": latest_job.id if latest_job else None,
            "status": latest_job.status if latest_job else None,
            "completed_at": latest_job.completed_at if latest_job else None,
            "added": latest_job.added if latest_job else 0,
            "updated": latest_job.updated if latest_job else 0,
        } if latest_job else None,
    }


# ── Query (RAG) ──

@router.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """Answer a user question grounded in knowledge base articles."""
    try:
        response = await answer_question(
            question=request.question,
            max_results=request.max_results,
            include_images=request.include_images,
        )

        # If answer needs human or confidence is low, record escalation
        if response.needs_human:
            esc_id = await create_escalation(
                question=request.question,
                context=response.answer,
                reason="Automatic escalation due to low confidence or human-verification trigger",
                retrieved_evidence=[s.model_dump() for s in response.sources],
            )
            response.escalation_id = esc_id

        return response
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


# ── Ingestion ──

@router.post("/ingestion/run", response_model=IngestionStatusResponse)
async def trigger_ingestion(
    request: IngestionRunRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger a crawl and ingestion run."""
    # Check if a job is already running
    async with async_session() as session:
        running_job = (await session.execute(
            select(IngestionJob).where(IngestionJob.status == "running").limit(1)
        )).scalar_one_or_none()

        if running_job:
            return IngestionStatusResponse(
                job_id=running_job.id,
                status=running_job.status,
                job_type=running_job.job_type,
                total_urls=running_job.total_urls,
                processed=running_job.processed,
                added=running_job.added,
                updated=running_job.updated,
                removed=running_job.removed,
                unchanged=running_job.unchanged,
                failed=running_job.failed,
                error_message="A job is already currently running",
                started_at=running_job.started_at,
            )

    # Spawn background task
    async def _run():
        try:
            await run_ingestion(
                job_type=request.job_type,
                batch_size=request.batch_size,
                max_pages=request.max_pages,
            )
        except Exception as e:
            logger.error(f"Background ingestion failed: {e}", exc_info=True)

    background_tasks.add_task(_run)

    return IngestionStatusResponse(
        job_id="pending",
        status="starting",
        job_type=request.job_type,
        error_message="",
    )


@router.get("/ingestion/status", response_model=IngestionStatusResponse)
async def get_ingestion_status():
    """Get the status of the most recent ingestion job."""
    async with async_session() as session:
        job = (await session.execute(
            select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        if not job:
            return IngestionStatusResponse(
                job_id="none",
                status="idle",
                job_type="none",
                error_message="No ingestion jobs have been run yet",
            )

        return IngestionStatusResponse(
            job_id=job.id,
            status=job.status,
            job_type=job.job_type,
            total_urls=job.total_urls,
            processed=job.processed,
            added=job.added,
            updated=job.updated,
            removed=job.removed,
            unchanged=job.unchanged,
            failed=job.failed,
            error_message=job.error_message or "",
            started_at=job.started_at,
            completed_at=job.completed_at,
        )


# ── Escalations ──

@router.post("/escalations", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_escalation(request: EscalationCreateRequest):
    """Manually escalate a question to human experts."""
    esc_id = await create_escalation(
        question=request.question,
        context=request.context,
        reason=request.reason,
    )
    esc = await get_escalation(esc_id)
    if not esc:
        raise HTTPException(status_code=500, detail="Failed to retrieve created escalation")
    return esc


@router.get("/escalations", response_model=list[EscalationResponse])
async def get_escalations(
    status_filter: str | None = Query(None, alias="status", pattern="^(open|resolved|dismissed)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List escalations with optional status filter."""
    return await list_escalations(status=status_filter, limit=limit, offset=offset)


@router.get("/escalations/{escalation_id}", response_model=EscalationResponse)
async def get_single_escalation(escalation_id: str):
    """Get a single escalation by ID."""
    esc = await get_escalation(escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return esc


@router.post("/escalations/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_single_escalation(
    escalation_id: str,
    resolve_data: EscalationResolveRequest,
):
    """Resolve an escalation with an authoritative expert answer and re-index it."""
    esc = await resolve_escalation(escalation_id, resolve_data)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return esc
