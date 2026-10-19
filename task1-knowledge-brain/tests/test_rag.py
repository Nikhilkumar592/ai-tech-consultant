"""Tests for RAG pipeline and escalation detection."""
import pytest
from app.config import settings
from retrieval.vector_store import add_chunks
from retrieval.rag import answer_question, _check_needs_human


@pytest.mark.asyncio
async def test_answer_question_with_evidence():
    # Insert knowledge chunk
    add_chunks(
        ["rag_test_1"],
        ["To change your directory logo, navigate to Settings > General Settings > Brand Info and upload your logo image."],
        [{
            "article_id": "art_logo",
            "article_title": "Updating Directory Logo",
            "article_url": "https://support.example.com/logo",
            "image_refs": "https://support.example.com/images/logo.png",
        }],
    )

    # Force mock mode for deterministic test
    settings.mock_mode = True

    response = await answer_question("how do I change my directory logo?", max_results=3)

    assert response.status in ["answered", "escalated"]
    assert len(response.sources) >= 1
    assert response.sources[0].title == "Updating Directory Logo"
    assert response.request_id != ""


@pytest.mark.asyncio
async def test_answer_insufficient_evidence():
    settings.mock_mode = True

    # Ask something completely absent from knowledge base
    response = await answer_question(
        "What is the relativistic quantum electrodynamic constant of hyperdrive spacetime?",
        confidence_threshold=0.99,
    )

    assert response.status == "insufficient_evidence"
    assert response.needs_human is True


def test_escalation_detection():
    assert _check_needs_human("I cannot find this information in the documentation", "how to cancel?") is True
    assert _check_needs_human("Here are the steps to upload a logo.", "how to upload a logo?") is False
    assert _check_needs_human("Please contact support for refund authorization.", "Can I get a refund?") is True
