"""Sitemap parser and manifest manager for the Knowledge Brain."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

SITEMAP_URL = "https://support.brilliantdirectories.com/support/sitemap.xml"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class SitemapEntry:
    """A single URL entry from the sitemap."""
    url: str
    lastmod: str = ""
    changefreq: str = ""
    priority: str = ""

    @property
    def article_id(self) -> str:
        """Stable ID derived from URL."""
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]


async def fetch_sitemap(
    url: str = SITEMAP_URL,
    timeout: int = 30,
) -> str:
    """Download the sitemap XML."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "KnowledgeBrain/1.0 (educational project)"})
        resp.raise_for_status()
        return resp.text


def parse_sitemap(xml_content: str) -> list[SitemapEntry]:
    """Parse sitemap XML into entries, filtering for article URLs."""
    root = ElementTree.fromstring(xml_content)
    entries: list[SitemapEntry] = []

    for url_elem in root.findall("sm:url", SITEMAP_NS):
        loc = url_elem.findtext("sm:loc", default="", namespaces=SITEMAP_NS).strip()
        if not loc:
            continue

        lastmod = url_elem.findtext("sm:lastmod", default="", namespaces=SITEMAP_NS).strip()
        changefreq = url_elem.findtext("sm:changefreq", default="", namespaces=SITEMAP_NS).strip()
        priority = url_elem.findtext("sm:priority", default="", namespaces=SITEMAP_NS).strip()

        entries.append(SitemapEntry(
            url=loc,
            lastmod=lastmod,
            changefreq=changefreq,
            priority=priority,
        ))

    logger.info(f"Parsed {len(entries)} URLs from sitemap")
    return entries


def classify_changes(
    sitemap_entries: list[SitemapEntry],
    existing_articles: dict[str, dict],  # id -> {url, content_hash, last_modified}
) -> dict[str, list[SitemapEntry]]:
    """Compare sitemap entries against existing articles to find changes.

    Returns dict with keys: added, changed, unchanged, removed.
    """
    sitemap_ids = {e.article_id: e for e in sitemap_entries}
    existing_ids = set(existing_articles.keys())
    new_ids = set(sitemap_ids.keys())

    added = [sitemap_ids[aid] for aid in new_ids - existing_ids]
    removed_ids = existing_ids - new_ids

    changed = []
    unchanged = []
    for aid in new_ids & existing_ids:
        entry = sitemap_ids[aid]
        existing = existing_articles[aid]
        # If lastmod changed, mark as potentially changed
        if entry.lastmod and entry.lastmod != existing.get("last_modified", ""):
            changed.append(entry)
        else:
            unchanged.append(entry)

    # Create pseudo-entries for removed articles
    removed = []
    for aid in removed_ids:
        ex = existing_articles[aid]
        removed.append(SitemapEntry(url=ex["url"]))

    logger.info(
        f"Changes: added={len(added)}, changed={len(changed)}, "
        f"unchanged={len(unchanged)}, removed={len(removed)}"
    )

    return {
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
        "removed": removed,
    }
