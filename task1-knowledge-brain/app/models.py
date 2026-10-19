"""Pydantic schemas for API request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Query ──

class QueryRequest(BaseModel):
    """Request to query the knowledge brain."""
    question: str = Field(..., min_length=3, max_length=2000, description="The question to ask")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of sources to return")
    include_images: bool = Field(default=True, description="Include image references in results")


class SourceReference(BaseModel):
    """A reference to a source article."""
    title: str
    url: str
    relevance_score: float = 0.0
    excerpt: str = ""


class ImageReference(BaseModel):
    """A reference to an image from a source article."""
    image_url: str
    article_title: str
    article_url: str
    description: str = ""
    alt_text: str = ""


class QueryResponse(BaseModel):
    """Response from the knowledge query endpoint."""
    answer: str
    status: str  # answered, insufficient_evidence, escalated, error
    sources: list[SourceReference] = []
    images: list[ImageReference] = []
    confidence: float = 0.0
    needs_human: bool = False
    escalation_id: str | None = None
    request_id: str = ""


# ── Ingestion ──

class IngestionRunRequest(BaseModel):
    """Request to start an ingestion run."""
    job_type: str = Field(default="incremental", pattern="^(full|incremental)$")
    batch_size: int | None = None
    max_pages: int | None = None


class IngestionStatusResponse(BaseModel):
    """Status of the current/last ingestion job."""
    job_id: str
    status: str
    job_type: str
    total_urls: int = 0
    processed: int = 0
    added: int = 0
    updated: int = 0
    removed: int = 0
    unchanged: int = 0
    failed: int = 0
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ── Escalation ──

class EscalationCreateRequest(BaseModel):
    """Request to create a human escalation."""
    question: str = Field(..., min_length=3)
    context: str = ""
    reason: str = ""


class EscalationResolveRequest(BaseModel):
    """Request to resolve an escalation with expert answer."""
    expert_answer: str = Field(..., min_length=1)
    expert_name: str = ""
    expert_sources: list[str] = []
    resolution_notes: str = ""


class EscalationResponse(BaseModel):
    """Response for an escalation."""
    id: str
    question: str
    context: str = ""
    reason: str = ""
    status: str
    expert_answer: str = ""
    expert_name: str = ""
    created_at: datetime
    resolved_at: datetime | None = None


# ── Health ──

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "knowledge-brain"
    version: str = "1.0.0"
    database: str = "connected"
    vector_store: str = "connected"
    articles_count: int = 0
    chunks_count: int = 0
    mock_mode: bool = False


# ── Error ──

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str = ""
    request_id: str = ""
