"""Tests for hybrid search combining semantic and keyword matching."""
import pytest
from retrieval.vector_store import add_chunks
from retrieval.search import hybrid_search, keyword_score


def test_keyword_score():
    score_full = keyword_score("stripe api key", "Enter your stripe api key in the settings.")
    score_partial = keyword_score("stripe api key", "Enter your stripe account details.")
    score_none = keyword_score("stripe api key", "Here is information on uploading videos.")

    assert score_full == 1.0
    assert 0.0 < score_partial < 1.0
    assert score_none == 0.0


def test_hybrid_search():
    add_chunks(
        ["hybrid_1", "hybrid_2"],
        [
            "Refund policy: users can request a refund within 14 days of purchase.",
            "Setting up member categories and directory taxonomy hierarchy.",
        ],
        [
            {"article_id": "art_refund", "article_title": "Refund Policy", "article_url": "https://example.com/refund"},
            {"article_id": "art_tax", "article_title": "Taxonomy", "article_url": "https://example.com/taxonomy"},
        ],
    )

    results = hybrid_search("how to request refund", n_results=2)
    assert len(results) >= 1
    top = results[0]
    assert "Refund" in top["metadata"]["article_title"] or "refund" in top["document"].lower()
    assert "combined_score" in top
    assert top["combined_score"] > 0
