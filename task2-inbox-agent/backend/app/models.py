"""Pydantic schemas for Inbox Agent."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class EmailSummary(BaseModel):
    id: str
    from_name: str
    from_email: str
    subject: str
    received_at: datetime
    status: str
    category: str
    priority: str
    urgency: str
    sentiment: str
    confidence_score: float
    is_spam: bool
    escalation_reason: str = ""


class EmailDetail(EmailSummary):
    body: str
    draft_response: str = ""
    edited_response: str = ""
    retrieved_sources: list[dict[str, Any]] = []
    escalation_id: str = ""
    processed_at: datetime | None = None
    resolved_at: datetime | None = None
    reviewed_by: str = ""
    was_auto_sent: bool = False


class EmailEditRequest(BaseModel):
    edited_draft: str = Field(..., min_length=1)
    editor_name: str = "Support Specialist"
    editor_notes: str = ""


class EmailApproveRequest(BaseModel):
    reviewer_name: str = "Support Specialist"


class AutonomyCategoryStatus(BaseModel):
    category: str
    consecutive_approvals: int
    is_autonomous: bool
    suggestion_ready: bool
    suggested_at: datetime | None = None
    confirmed_at: datetime | None = None
    total_approved: int
    total_rejected: int
    total_edited: int
    target_threshold: int = 20


class AutonomyToggleRequest(BaseModel):
    category: str
    enable_autonomous: bool
    confirmed_by: str = "Support Lead"
