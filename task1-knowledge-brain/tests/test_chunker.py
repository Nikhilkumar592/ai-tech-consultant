"""Tests for article chunking module."""
import pytest
from ingestion.chunker import chunk_article, TextChunk


def test_chunk_small_article():
    chunks = chunk_article(
        article_id="art_1",
        title="Quick Start",
        url="https://example.com/quick-start",
        content="This is a short article about getting started with the platform.",
        category="Getting Started",
    )

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.article_id == "art_1"
    assert chunk.chunk_index == 0
    assert "Quick Start" in chunk.content or "getting started" in chunk.content
    assert chunk.category == "Getting Started"
    assert chunk.content_hash != ""


def test_chunk_with_headings():
    headings = [
        {"level": "h2", "text": "Section 1: Setup"},
        {"level": "h2", "text": "Section 2: Verification"},
    ]
    content = "Section 1: Setup\nFollow these setup instructions.\nSection 2: Verification\nVerify the setup worked."

    chunks = chunk_article(
        article_id="art_2",
        title="Detailed Guide",
        url="https://example.com/guide",
        content=content,
        headings=headings,
    )

    assert len(chunks) >= 2
    headings_in_chunks = [c.heading for c in chunks]
    assert any("Section 1: Setup" in h for h in headings_in_chunks)
    assert any("Section 2: Verification" in h for h in headings_in_chunks)


def test_chunk_with_tables():
    tables = ["| Feature | Supported |\n| --- | --- |\n| SSO | Yes |"]
    chunks = chunk_article(
        article_id="art_3",
        title="Features",
        url="https://example.com/features",
        content="Here are the features supported by our platform.",
        tables=tables,
    )

    assert len(chunks) >= 2
    table_chunk = next((c for c in chunks if c.heading == "Table"), None)
    assert table_chunk is not None
    assert "SSO" in table_chunk.content


def test_chunk_empty_content():
    chunks = chunk_article(
        article_id="art_empty",
        title="Empty",
        url="https://example.com/empty",
        content="",
    )
    assert len(chunks) == 0
