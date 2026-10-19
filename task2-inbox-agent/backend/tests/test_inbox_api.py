"""Tests for Inbox Agent FastAPI endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_seed_and_list_emails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Seed
        seed_resp = await client.post("/inbox/seed")
        assert seed_resp.status_code == 200
        assert seed_resp.json()["count"] >= 0

        # List
        list_resp = await client.get("/emails?limit=10")
        assert list_resp.status_code == 200
        emails = list_resp.json()
        assert len(emails) >= 1
        first_email = emails[0]
        assert "from_email" in first_email
        assert "subject" in first_email


@pytest.mark.asyncio
async def test_email_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Seed to make sure emails exist
        await client.post("/inbox/seed")

        # 1. Process email_01
        proc_resp = await client.post("/emails/email_01/process")
        assert proc_resp.status_code == 200
        data = proc_resp.json()
        assert data["category"] in ["technical_support", "billing", "general_inquiry"]
        assert data["draft_response"] != ""

        # 2. Edit draft
        edit_payload = {
            "edited_draft": "Hi Sarah, custom human edited response with direct guide instructions.",
            "editor_name": "Senior Support Engineer",
            "editor_notes": "Added direct instructions",
        }
        edit_resp = await client.post("/emails/email_01/edit", json=edit_payload)
        assert edit_resp.status_code == 200
        assert edit_resp.json()["edited_response"] == edit_payload["edited_draft"]

        # 3. Autonomy status
        auto_resp = await client.get("/autonomy/status")
        assert auto_resp.status_code == 200
        statuses = auto_resp.json()
        assert any(s["category"] == "technical_support" for s in statuses)
