"""Async crawler with rate limiting, retries, and checkpoint support."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import settings

logger = logging.getLogger(__name__)


class CrawlResult:
    """Result of crawling a single page."""

    def __init__(
        self,
        url: str,
        html: str = "",
        status_code: int = 0,
        success: bool = False,
        error: str = "",
        content_hash: str = "",
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.success = success
        self.error = error
        self.content_hash = content_hash


class PoliteAsyncCrawler:
    """Crawls pages with configurable concurrency, rate limits, and retries."""

    def __init__(
        self,
        concurrency: int | None = None,
        delay_seconds: float | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
    ):
        self.concurrency = concurrency or settings.crawl_concurrency
        self.delay_seconds = delay_seconds or settings.crawl_delay_seconds
        self.timeout_seconds = timeout_seconds or settings.crawl_timeout_seconds
        self.max_retries = max_retries or settings.crawl_max_retries
        self._semaphore = asyncio.Semaphore(self.concurrency)
        self._last_request_time: float = 0
        self._lock = asyncio.Lock()

    async def _rate_limit(self) -> None:
        """Enforce minimum delay between requests."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.delay_seconds:
                await asyncio.sleep(self.delay_seconds - elapsed)
            self._last_request_time = time.monotonic()

    async def fetch_page(self, url: str) -> CrawlResult:
        """Fetch a single page with rate limiting and retries."""
        async with self._semaphore:
            await self._rate_limit()
            return await self._fetch_with_retry(url)

    async def _fetch_with_retry(self, url: str) -> CrawlResult:
        """Fetch with exponential backoff retry."""
        last_error = ""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(
                        url,
                        headers={
                            "User-Agent": "KnowledgeBrain/1.0 (educational project)",
                            "Accept": "text/html",
                        },
                    )

                    if resp.status_code == 429:
                        # Rate limited — wait longer
                        wait_time = min(2 ** (attempt + 2), 60)
                        logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if resp.status_code >= 500:
                        # Server error — retry
                        wait_time = min(2 ** (attempt + 1), 30)
                        logger.warning(f"Server error {resp.status_code} on {url}, retry in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if resp.status_code == 404:
                        return CrawlResult(url=url, status_code=404, error="Page not found")

                    resp.raise_for_status()
                    html = resp.text
                    content_hash = hashlib.sha256(html.encode()).hexdigest()[:16]

                    return CrawlResult(
                        url=url,
                        html=html,
                        status_code=resp.status_code,
                        success=True,
                        content_hash=content_hash,
                    )

            except httpx.TimeoutException:
                last_error = f"Timeout after {self.timeout_seconds}s"
                logger.warning(f"Timeout on {url} (attempt {attempt + 1})")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                logger.warning(f"HTTP error on {url}: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error fetching {url}: {last_error}")

            if attempt < self.max_retries:
                wait_time = min(2 ** (attempt + 1), 30)
                await asyncio.sleep(wait_time)

        return CrawlResult(url=url, error=f"Failed after {self.max_retries + 1} attempts: {last_error}")

    async def crawl_batch(
        self,
        urls: list[str],
        on_result: Any = None,
    ) -> list[CrawlResult]:
        """Crawl a batch of URLs concurrently with rate limiting."""
        results: list[CrawlResult] = []

        async def _process(url: str) -> None:
            result = await self.fetch_page(url)
            results.append(result)
            if on_result:
                await on_result(result)

        tasks = [_process(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)
        return results
