"""HTML parser to extract article content, structure, and images."""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass
class ParsedImage:
    """An image found in an article."""
    url: str
    alt_text: str = ""
    surrounding_text: str = ""


@dataclass
class ParsedArticle:
    """Structured extraction from a help center article."""
    url: str
    title: str = ""
    content_text: str = ""
    content_html: str = ""
    content_hash: str = ""
    category: str = ""
    folder: str = ""
    headings: list[dict[str, str]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[ParsedImage] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    lists: list[str] = field(default_factory=list)


def parse_article(html: str, url: str) -> ParsedArticle:
    """Parse a help center article page and extract structured content."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    article = ParsedArticle(url=url)

    # Extract title
    title_tag = (
        soup.find("h1", class_=re.compile(r"article", re.I))
        or soup.find("h1")
        or soup.find("title")
    )
    if title_tag:
        article.title = title_tag.get_text(strip=True)

    # Try to find the main article content area
    main_content = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"article[-_]?(body|content)", re.I))
        or soup.find("div", class_=re.compile(r"(content|main)[-_]?(body|area|text)", re.I))
        or soup.find("div", id=re.compile(r"article|content|main", re.I))
        or soup.find("main")
    )

    if not main_content:
        # Fallback: use body but strip nav, footer, sidebar
        main_content = soup.find("body") or soup
        for tag_name in ["nav", "footer", "header", "aside"]:
            for tag in main_content.find_all(tag_name):
                tag.decompose()
        for cls in ["sidebar", "navigation", "footer", "header", "breadcrumb", "menu"]:
            for tag in main_content.find_all(class_=re.compile(cls, re.I)):
                tag.decompose()

    # Extract breadcrumb/category info
    breadcrumb = soup.find(class_=re.compile(r"breadcrumb", re.I))
    if breadcrumb:
        crumbs = [a.get_text(strip=True) for a in breadcrumb.find_all("a")]
        if len(crumbs) >= 2:
            article.category = crumbs[1] if len(crumbs) > 1 else ""
            article.folder = crumbs[2] if len(crumbs) > 2 else ""

    # Extract headings
    for h in main_content.find_all(re.compile(r"^h[1-6]$")):
        article.headings.append({
            "level": h.name,
            "text": h.get_text(strip=True),
        })

    # Extract images with surrounding context
    for img in main_content.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue

        full_url = urljoin(url, src)
        alt = img.get("alt", "")

        # Get surrounding text for context
        surrounding = ""
        parent = img.parent
        if parent:
            prev_sib = img.find_previous_sibling(string=True)
            next_sib = img.find_next_sibling(string=True)
            if parent.name in ("p", "div", "figure"):
                surrounding = parent.get_text(strip=True)[:300]
            elif prev_sib:
                surrounding = str(prev_sib).strip()[:200]

            # Also check for figure caption
            caption = parent.find("figcaption") if parent else None
            if caption:
                surrounding = caption.get_text(strip=True)

        article.images.append(ParsedImage(
            url=full_url,
            alt_text=alt,
            surrounding_text=surrounding,
        ))

    # Extract tables as text
    for table in main_content.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            rows.append(" | ".join(cells))
        if rows:
            article.tables.append("\n".join(rows))

    # Extract lists
    for ul in main_content.find_all(["ul", "ol"]):
        items = []
        for li in ul.find_all("li", recursive=False):
            items.append(f"• {li.get_text(strip=True)}")
        if items:
            article.lists.append("\n".join(items))

    # Extract links
    for a in main_content.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href and text and not href.startswith("#"):
            article.links.append({
                "text": text,
                "url": urljoin(url, href),
            })

    # Extract clean text content
    article.content_html = str(main_content)
    article.content_text = _clean_text(main_content.get_text(separator="\n"))

    # Content hash for change detection
    article.content_hash = hashlib.sha256(
        article.content_text.encode()
    ).hexdigest()[:16]

    return article


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove excessive blank lines."""
    lines = text.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        line = line.strip()
        if not line:
            if not prev_empty:
                cleaned.append("")
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    return "\n".join(cleaned).strip()
