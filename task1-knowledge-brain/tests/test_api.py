"""Tests for FastAPI endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from retrieval.vector_store import add_chunks


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "knowledge-brain"
        assert "database" in data
        assert "vector_store" in data


@pytest.mark.asyncio
async def test_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "chunks" in data
        assert "escalations" in data


@pytest.mark.asyncio
async def test_query_endpoint():
    # Insert knowledge
    add_chunks(
        ["api_chk_1"],
        ["Member search results can be filtered by city, state, postal code, and radius."],
        [{"article_id": "art_search", "article_title": "Member Search", "article_url": "https://example.com/search"}],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "question": "Can members search by postal code radius?",
            "max_results": 3,
            "include_images": False,
        }
        response = await client.post("/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["status"] in ["answered", "escalated"]
        assert len(data["sources"]) >= 1


@pytest.mark.asyncio
async def test_escalation_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create escalation
        create_payload = {
            "question": "How to implement custom webhook callback signatures?",
            "context": "Customer has enterprise security policy requirement",
            "reason": "Requires engineering expertise",
        }
        res_create = await client.post("/escalations", json=create_payload)
        assert res_create.status_code == 201
        esc = res_create.json()
        esc_id = esc["id"]
        assert esc["status"] == "open"

        # 2. List escalations
        res_list = await client.get("/escalations?status=open")
        assert res_list.status_code == 200
        open_list = res_list.json()
        assert any(item["id"] == esc_id for item in open_list)

        # 3. Resolve escalation
        resolve_payload = {
            "expert_answer": "Use HMAC-SHA256 signature verification in your endpoint using your webhook secret.",
            "expert_name": "Senior Security Architect",
            "expert_sources": ["https://support.example.com/webhooks-security"],
            "resolution_notes": "Verified against v2 webhook specs",
        }
        res_resolve = await client.post(f"/escalations/{esc_id}/resolve", json=resolve_payload)
        assert res_resolve.status_code == 200
        resolved_esc = res_resolve.json()
        assert resolved_esc["status"] == "resolved"
        assert "HMAC-SHA256" in resolved_esc["expert_answer"]

        # 4. Verify Q&A query returns re-indexed resolution
        res_query = await client.post("/query", json={"question": "custom webhook callback signatures"})
        assert res_query.status_code == 200
        q_data = res_query.json()
        assert any("Verified Q&A" in s["title"] or "webhook" in s["title"].lower() for s in q_data["sources"])
