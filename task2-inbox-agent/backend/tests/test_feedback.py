"""Tests for human edit feedback capture."""
import pytest
import pytest_asyncio
from app.database import init_db
from app.feedback import save_draft_feedback, get_recent_feedback


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_save_and_retrieve_feedback():
    orig = "Hello Sarah,\nPlease refer to the guide.\nBest, Support"
    edited = "Hi Sarah,\nHere is the exact Stripe setup documentation link: https://support.example.com/stripe\nBest, Sarah's Dedicated Support"

    fid = await save_draft_feedback(
        email_id="email_01",
        category="technical_support",
        customer_query="Stripe webhook 400 error",
        original_draft=orig,
        edited_draft=edited,
        editor_notes="Included exact documentation link directly",
    )
    assert fid > 0

    recent = await get_recent_feedback("technical_support", limit=3)
    assert len(recent) >= 1
    item = recent[0]
    assert item["email_id"] == "email_01"
    assert "Similarity" in item["diff_summary"]
