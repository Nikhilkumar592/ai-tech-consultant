"""Ingestion pipeline: orchestrates sitemap → crawl → parse → chunk → embed → store."""
from __future__ import annotations

import asyncio
import datetime
import hashlib
import logging
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import (
    Article, Chunk, ArticleImage, IngestionJob,
    async_session,
)
from ingestion.sitemap import (
    fetch_sitemap, parse_sitemap, classify_changes, SitemapEntry,
)
from ingestion.crawler import PoliteAsyncCrawler, CrawlResult
from ingestion.parser import parse_article, ParsedArticle
from ingestion.chunker import chunk_article, TextChunk
from ingestion.images import download_image, analyze_image_with_vision
from retrieval.vector_store import add_chunks, delete_by_article

logger = logging.getLogger(__name__)


async def run_ingestion(
    job_type: str = "incremental",
    batch_size: int | None = None,
    max_pages: int | None = None,
) -> dict[str, Any]:
    """Run a full or incremental ingestion job.

    Returns summary dict with counts.
    """
    batch_size = batch_size or settings.crawl_batch_size
    job_id = str(uuid.uuid4())[:12]

    async with async_session() as session:
        # Create job record
        job = IngestionJob(
            id=job_id,
            job_type=job_type,
            status="running",
            started_at=datetime.datetime.utcnow(),
        )
        session.add(job)
        await session.commit()

        try:
            # 1. Fetch and parse sitemap
            logger.info(f"[Job {job_id}] Fetching sitemap...")
            xml = await fetch_sitemap()
            entries = parse_sitemap(xml)
            job.total_urls = len(entries)

            if max_pages:
                entries = entries[:max_pages]
                job.total_urls = len(entries)

            # 2. Get existing articles for change detection
            existing = await _get_existing_articles(session)

            # 3. Classify changes
            changes = classify_changes(entries, existing)
            logger.info(
                f"[Job {job_id}] Changes: "
                f"added={len(changes['added'])}, changed={len(changes['changed'])}, "
                f"unchanged={len(changes['unchanged'])}, removed={len(changes['removed'])}"
            )

            # 4. Determine what to process
            if job_type == "full":
                to_process = entries
            else:
                to_process = changes["added"] + changes["changed"]

            # 5. Handle removed articles
            for entry in changes["removed"]:
                await _deactivate_article(session, entry.article_id)
                job.removed += 1
            
            job.unchanged = len(changes["unchanged"])

            # 6. Crawl and process in batches
            crawler = PoliteAsyncCrawler()

            for i in range(0, len(to_process), batch_size):
                batch = to_process[i : i + batch_size]
                urls = [e.url for e in batch]
                logger.info(f"[Job {job_id}] Processing batch {i // batch_size + 1}: {len(urls)} URLs")

                results = await crawler.crawl_batch(urls)

                for result, entry in zip(results, batch):
                    if result.success:
                        was_new = await _process_page(session, entry, result)
                        if was_new:
                            job.added += 1
                        else:
                            job.updated += 1
                    else:
                        await _mark_failed(session, entry, result.error)
                        job.failed += 1

                    job.processed += 1

                await session.commit()

            # 7. Complete the job
            job.status = "completed"
            job.completed_at = datetime.datetime.utcnow()
            await session.commit()

            summary = {
                "job_id": job_id,
                "status": "completed",
                "total_urls": job.total_urls,
                "processed": job.processed,
                "added": job.added,
                "updated": job.updated,
                "removed": job.removed,
                "unchanged": job.unchanged,
                "failed": job.failed,
            }
            logger.info(f"[Job {job_id}] Ingestion complete: {summary}")
            return summary

        except Exception as e:
            logger.error(f"[Job {job_id}] Ingestion failed: {e}")
            job.status = "failed"
            job.error_message = str(e)[:1000]
            job.completed_at = datetime.datetime.utcnow()
            await session.commit()
            raise


async def _get_existing_articles(session: AsyncSession) -> dict[str, dict]:
    """Get all existing articles as a lookup dict."""
    result = await session.execute(
        select(Article.id, Article.url, Article.content_hash, Article.last_modified)
        .where(Article.is_active == True)
    )
    return {
        row.id: {
            "url": row.url,
            "content_hash": row.content_hash,
            "last_modified": row.last_modified,
        }
        for row in result
    }


async def _process_page(
    session: AsyncSession,
    entry: SitemapEntry,
    result: CrawlResult,
) -> bool:
    """Process a successfully crawled page. Returns True if new article."""
    # Parse HTML
    parsed = parse_article(result.html, entry.url)

    # Check if article exists
    existing = await session.get(Article, entry.article_id)
    is_new = existing is None

    if existing and existing.content_hash == parsed.content_hash:
        # Content unchanged despite lastmod change
        existing.last_ingested_at = datetime.datetime.utcnow()
        existing.ingestion_status = "completed"
        return False

    # Create or update article
    if is_new:
        article = Article(
            id=entry.article_id,
            url=entry.url,
            title=parsed.title,
            content_raw=parsed.content_html[:50000],  # Limit storage
            content_text=parsed.content_text,
            content_hash=parsed.content_hash,
            category=parsed.category,
            folder=parsed.folder,
            headings=[h for h in parsed.headings],
            links=parsed.links[:50],  # Limit stored links
            image_urls=[img.url for img in parsed.images],
            last_modified=entry.lastmod,
            ingestion_status="completed",
            last_ingested_at=datetime.datetime.utcnow(),
        )
        session.add(article)
    else:
        existing.title = parsed.title
        existing.content_raw = parsed.content_html[:50000]
        existing.content_text = parsed.content_text
        existing.content_hash = parsed.content_hash
        existing.category = parsed.category
        existing.folder = parsed.folder
        existing.headings = [h for h in parsed.headings]
        existing.links = parsed.links[:50]
        existing.image_urls = [img.url for img in parsed.images]
        existing.last_modified = entry.lastmod
        existing.version = (existing.version or 1) + 1
        existing.ingestion_status = "completed"
        existing.last_ingested_at = datetime.datetime.utcnow()
        article = existing

        # Delete old chunks from vector store before re-adding
        delete_by_article(entry.article_id)

        # Delete old chunks from DB
        old_chunks = await session.execute(
            select(Chunk).where(Chunk.article_id == entry.article_id)
        )
        for old_chunk in old_chunks.scalars():
            await session.delete(old_chunk)

    await session.flush()

    # Create chunks
    image_urls_str = [img.url for img in parsed.images[:5]]
    chunks = chunk_article(
        article_id=entry.article_id,
        title=parsed.title,
        url=entry.url,
        content=parsed.content_text,
        category=parsed.category,
        headings=parsed.headings,
        image_urls=image_urls_str,
        tables=parsed.tables,
    )

    # Save chunks to DB and vector store
    chunk_ids = []
    chunk_texts = []
    chunk_metadatas = []

    for tc in chunks:
        db_chunk = Chunk(
            id=tc.chunk_id,
            article_id=tc.article_id,
            chunk_index=tc.chunk_index,
            content=tc.content,
            content_hash=tc.content_hash,
            heading=tc.heading,
            metadata_extra={
                "article_title": tc.article_title,
                "article_url": tc.article_url,
                "category": tc.category,
            },
        )
        session.add(db_chunk)

        chunk_ids.append(tc.chunk_id)
        chunk_texts.append(tc.content)
        chunk_metadatas.append({
            "article_id": tc.article_id,
            "article_title": tc.article_title,
            "article_url": tc.article_url,
            "category": tc.category,
            "heading": tc.heading,
            "image_refs": ",".join(tc.image_refs[:3]),
        })

    # Add to vector store
    if chunk_ids:
        add_chunks(chunk_ids, chunk_texts, chunk_metadatas)

    # Process images (limited to save time and API costs)
    for img in parsed.images[:5]:
        img_id = hashlib.sha256(img.url.encode()).hexdigest()[:16]
        db_image = ArticleImage(
            id=img_id,
            article_id=entry.article_id,
            image_url=img.url,
            alt_text=img.alt_text,
            surrounding_text=img.surrounding_text[:500],
        )
        session.add(db_image)

    logger.info(
        f"Processed article '{parsed.title}' "
        f"({len(chunks)} chunks, {len(parsed.images)} images)"
    )
    return is_new


async def _deactivate_article(session: AsyncSession, article_id: str) -> None:
    """Deactivate an article and remove its chunks from search."""
    await session.execute(
        update(Article)
        .where(Article.id == article_id)
        .values(is_active=False, ingestion_status="removed")
    )
    await session.execute(
        update(Chunk)
        .where(Chunk.article_id == article_id)
        .values(is_active=False)
    )
    delete_by_article(article_id)
    logger.info(f"Deactivated article {article_id}")


async def _mark_failed(
    session: AsyncSession,
    entry: SitemapEntry,
    error: str,
) -> None:
    """Mark an article as failed."""
    existing = await session.get(Article, entry.article_id)
    if existing:
        existing.ingestion_status = "failed"
        existing.error_message = error[:1000]
        existing.retry_count = (existing.retry_count or 0) + 1
    else:
        article = Article(
            id=entry.article_id,
            url=entry.url,
            ingestion_status="failed",
            error_message=error[:1000],
        )
        session.add(article)
