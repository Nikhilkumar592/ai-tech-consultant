"""Tests for Task 3 FastAPI pipeline runner endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_run_pipeline_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/pipeline/run")
        assert resp.status_code == 200
        data = resp.json()

        assert "client_name" in data
        assert "analysis" in data
        assert "feasibility" in data
        assert "estimation" in data
        assert "proposal_markdown" in data
        assert "comparison_results" in data
        assert "comparison_markdown" in data

        assert data["comparison_results"]["requirement_coverage_rate"] >= 80.0
        assert data["estimation"]["hours"]["expected"] > 80.0


@pytest.mark.asyncio
async def test_get_proposal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/proposal")
        assert resp.status_code == 200
        data = resp.json()
        assert "proposal_markdown" in data
        assert "Statement of Work" in data["proposal_markdown"]
