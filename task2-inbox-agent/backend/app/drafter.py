"""Grounded draft generator integrated with Knowledge Brain and few-shot feedback."""
from __future__ import annotations

import logging
from typing import Any
import httpx
from sqlalchemy import select

from app.config import settings
from app.database import DraftFeedback, async_session

logger = logging.getLogger(__name__)


async def generate_draft_response(
    from_name: str,
    subject: str,
    body: str,
    category: str,
) -> dict[str, Any]:
    """Generate grounded draft response using Knowledge Brain RAG + feedback examples."""
    first_name = from_name.split()[0] if from_name else "there"

    # Handle spam
    if category == "spam":
        return {
            "draft": "",
            "confidence": 0.99,
            "sources": [],
            "needs_escalation": False,
            "escalation_reason": "Identified as spam/phishing - no response needed.",
        }

    # Handle critical escalation
    if category == "escalation":
        draft = (
            f"Dear {first_name},\n\n"
            f"Thank you for contacting us regarding: \"{subject}\".\n\n"
            f"Your request has been prioritized and immediately escalated to our Senior Technical "
            f"Operations and Legal Compliance teams for specialized review. A senior specialist "
            f"will review the details and respond to you directly.\n\n"
            f"Reference Ticket ID: Priority Escalation Queue\n\n"
            f"Best regards,\nBrilliant Directories Executive Support"
        )
        return {
            "draft": draft,
            "confidence": 0.95,
            "sources": [],
            "needs_escalation": True,
            "escalation_reason": "High-urgency escalation or compliance matter requiring executive review.",
        }

    # Query Knowledge Brain API
    kb_query = f"{subject} {body[:250]}"
    retrieved_sources = []
    rag_answer = ""
    kb_confidence = 0.5
    needs_human = False

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{settings.kb_api_url}/query",
                json={"question": kb_query, "max_results": 3, "include_images": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                rag_answer = data.get("answer", "")
                retrieved_sources = data.get("sources", [])
                kb_confidence = data.get("confidence", 0.7)
                needs_human = data.get("needs_human", False)
    except Exception as e:
        logger.warning(f"Could not reach Knowledge Brain at {settings.kb_api_url}: {e}. Using fallback drafting.")

    # Retrieve few-shot human feedback examples for this category
    few_shot_examples = []
    try:
        async with async_session() as session:
            stmt = select(DraftFeedback).where(DraftFeedback.category == category).order_by(DraftFeedback.created_at.desc()).limit(2)
            res = await session.execute(stmt)
            few_shot_examples = res.scalars().all()
    except Exception as e:
        logger.warning(f"Could not load feedback examples: {e}")

    # Build response draft
    if rag_answer and not rag_answer.startswith("I don't have any information"):
        content_body = rag_answer.replace("[Mock Answer] ", "")
    else:
        # Fallback category-specific helpful response
        if category == "billing":
            content_body = (
                "Regarding your billing request, our accounting team processes invoices, updates, "
                "and refunds within 1-2 business days. If you are updating a payment method, you can also "
                "manage your active cards securely in your Admin Panel under Settings > Account Billing."
            )
        elif category == "technical_support":
            content_body = (
                "Regarding your technical question, please check the corresponding section in your "
                "Admin Panel (Settings > General Settings or Settings > Payment Gateways). Ensure all API credentials "
                "and DNS records match the configuration guides."
            )
        else:
            content_body = (
                "Thank you for reaching out with your question. We are happy to help guide you on how to best "
                "configure and make the most of your directory website."
            )

    sources_citation = ""
    if retrieved_sources:
        sources_citation = "\n\nHelpful Reference Articles:\n" + "\n".join(
            f"- {s.get('title')}: {s.get('url')}" for s in retrieved_sources[:2]
        )

    draft = (
        f"Hi {first_name},\n\n"
        f"Thank you for contacting Brilliant Directories Support.\n\n"
        f"{content_body}"
        f"{sources_citation}\n\n"
        f"Please let us know if you need any further assistance!\n\n"
        f"Best regards,\nCustomer Success Team\nBrilliant Directories"
    )

    return {
        "draft": draft,
        "confidence": kb_confidence if not needs_human else 0.35,
        "sources": retrieved_sources,
        "needs_escalation": needs_human,
        "escalation_reason": "Low retrieval confidence or complex edge case requiring specialist verification" if needs_human else "",
    }
