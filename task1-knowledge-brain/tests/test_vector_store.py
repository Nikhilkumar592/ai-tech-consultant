"""Tests for ChromaDB vector store operations."""
import pytest
from retrieval.vector_store import (
    add_chunks,
    search,
    delete_chunks,
    delete_by_article,
    get_stats,
)


def test_add_and_search_chunks():
    chunk_ids = ["test_chk_1", "test_chk_2"]
    texts = [
        "To configure SMTP email settings, enter your host, port, and password.",
        "To connect your custom domain name, update the A records in your DNS manager.",
    ]
    metadatas = [
        {"article_id": "art_smtp", "article_title": "Email Settings"},
        {"article_id": "art_dns", "article_title": "Domain Setup"},
    ]

    added = add_chunks(chunk_ids, texts, metadatas)
    assert added == 2

    # Search for email configuration
    results = search("SMTP email settings", n_results=2)
    assert len(results) > 0
    top_doc = results[0]["document"]
    assert "SMTP" in top_doc or "email" in top_doc.lower()


def test_delete_by_article():
    add_chunks(
        ["del_chk_1", "del_chk_2"],
        ["Content for deletion test A", "Content for deletion test B"],
        [{"article_id": "art_to_delete"}, {"article_id": "art_to_delete"}],
    )

    deleted_count = delete_by_article("art_to_delete")
    assert deleted_count >= 1

    # Ensure search does not return deleted article
    results = search("Content for deletion test", n_results=5)
    for r in results:
        assert r["metadata"].get("article_id") != "art_to_delete"


def test_get_stats():
    stats = get_stats()
    assert "total_chunks" in stats
    assert "collection_name" in stats
