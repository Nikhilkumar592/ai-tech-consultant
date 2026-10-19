"""Tests for draft generator."""
import pytest
import pytest_asyncio
from app.database import init_db
from app.drafter import generate_draft_response


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_draft_spam_produces_empty_response():
    res = await generate_draft_response(
        from_name="Scammer",
        subject="Claim your BTC",
        body="Send banking details",
        category="spam",
    )
    assert res["draft"] == ""
    assert res["confidence"] >= 0.95


@pytest.mark.asyncio
async def test_draft_escalation_produces_legal_routing():
    res = await generate_draft_response(
        from_name="Attorney Vance",
        subject="DMCA Takedown Notice",
        body="Preserve server logs immediately",
        category="escalation",
    )
    assert "escalated" in res["draft"].lower()
    assert res["needs_escalation"] is True


@pytest.mark.asyncio
async def test_draft_support_response():
    res = await generate_draft_response(
        from_name="Sarah Jenkins",
        subject="How to configure payment gateway?",
        body="I need help setting up Stripe",
        category="technical_support",
    )
    assert "Sarah" in res["draft"]
    assert "Brilliant Directories" in res["draft"]
    assert res["confidence"] > 0
