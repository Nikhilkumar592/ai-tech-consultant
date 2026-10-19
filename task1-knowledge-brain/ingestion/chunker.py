"""Text chunking with metadata for embedding and retrieval."""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800  # characters
DEFAULT_CHUNK_OVERLAP = 100


@dataclass
class TextChunk:
    """A chunk of text ready for embedding."""
    chunk_id: str
    article_id: str
    chunk_index: int
    content: str
    content_hash: str
    heading: str = ""
    article_title: str = ""
    article_url: str = ""
    category: str = ""
    image_refs: list[str] = field(default_factory=list)


def chunk_article(
    article_id: str,
    title: str,
    url: str,
    content: str,
    category: str = "",
    headings: list[dict[str, str]] | None = None,
    image_urls: list[str] | None = None,
    tables: list[str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Split article content into meaningful chunks with metadata.

    Strategy:
    1. First try to split by headings/sections
    2. Then split long sections by paragraph
    3. Then split long paragraphs by sentence with overlap
    """
    if not content.strip():
        return []

    sections = _split_by_headings(content, headings or [])
    chunks: list[TextChunk] = []
    chunk_index = 0

    # Add table content as separate chunks
    for i, table_text in enumerate(tables or []):
        if table_text.strip():
            chunk_id = _make_chunk_id(article_id, chunk_index)
            chunks.append(TextChunk(
                chunk_id=chunk_id,
                article_id=article_id,
                chunk_index=chunk_index,
                content=f"[Table from {title}]\n{table_text}",
                content_hash=hashlib.sha256(table_text.encode()).hexdigest()[:16],
                heading="Table",
                article_title=title,
                article_url=url,
                category=category,
            ))
            chunk_index += 1

    for section_heading, section_text in sections:
        if not section_text.strip():
            continue

        if len(section_text) <= chunk_size:
            # Section fits in one chunk
            chunk_id = _make_chunk_id(article_id, chunk_index)
            chunk_content = section_text
            if section_heading:
                chunk_content = f"{section_heading}\n{chunk_content}"

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                article_id=article_id,
                chunk_index=chunk_index,
                content=chunk_content,
                content_hash=hashlib.sha256(chunk_content.encode()).hexdigest()[:16],
                heading=section_heading,
                article_title=title,
                article_url=url,
                category=category,
                image_refs=image_urls or [],
            ))
            chunk_index += 1
        else:
            # Section too long — split by paragraphs then sentences
            sub_chunks = _split_text(section_text, chunk_size, chunk_overlap)
            for sub in sub_chunks:
                chunk_id = _make_chunk_id(article_id, chunk_index)
                chunk_content = sub
                if section_heading:
                    chunk_content = f"{section_heading}\n{chunk_content}"

                chunks.append(TextChunk(
                    chunk_id=chunk_id,
                    article_id=article_id,
                    chunk_index=chunk_index,
                    content=chunk_content,
                    content_hash=hashlib.sha256(chunk_content.encode()).hexdigest()[:16],
                    heading=section_heading,
                    article_title=title,
                    article_url=url,
                    category=category,
                    image_refs=image_urls or [],
                ))
                chunk_index += 1

    # If no chunks were created, create a single chunk from the full content
    if not chunks and content.strip():
        chunk_id = _make_chunk_id(article_id, 0)
        chunk_content = f"{title}\n{content}" if title else content
        chunks.append(TextChunk(
            chunk_id=chunk_id,
            article_id=article_id,
            chunk_index=0,
            content=chunk_content[:chunk_size * 2],  # Allow larger for single-chunk articles
            content_hash=hashlib.sha256(chunk_content.encode()).hexdigest()[:16],
            article_title=title,
            article_url=url,
            category=category,
        ))

    return chunks


def _split_by_headings(
    content: str,
    headings: list[dict[str, str]],
) -> list[tuple[str, str]]:
    """Split content at heading boundaries."""
    if not headings:
        return [("", content)]

    sections: list[tuple[str, str]] = []
    heading_texts = [h["text"] for h in headings if h.get("text")]

    # Try to split content at heading lines
    lines = content.split("\n")
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped in heading_texts:
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines)))
            current_heading = stripped
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines)))

    return sections if sections else [("", content)]


def _split_text(text: str, max_size: int, overlap: int) -> list[str]:
    """Split text by paragraphs, then sentences, with overlap."""
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 2 <= max_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current.strip())
            if len(para) <= max_size:
                current = para
            else:
                # Split long paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_size:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current.strip())
                        current = sent

    if current:
        chunks.append(current.strip())

    # Add overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1][-overlap:]
            overlapped.append(f"{prev_end}... {chunks[i]}")
        chunks = overlapped

    return chunks


def _make_chunk_id(article_id: str, index: int) -> str:
    """Generate a stable chunk ID."""
    raw = f"{article_id}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
