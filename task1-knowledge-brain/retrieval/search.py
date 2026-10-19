"""Hybrid search combining semantic and keyword retrieval."""
from __future__ import annotations

import logging
import re
from typing import Any

from retrieval.vector_store import search as vector_search

logger = logging.getLogger(__name__)


def keyword_score(query: str, document: str) -> float:
    """Simple keyword matching score."""
    query_terms = set(re.findall(r"\w+", query.lower()))
    doc_terms = set(re.findall(r"\w+", document.lower()))

    if not query_terms:
        return 0.0

    matches = query_terms & doc_terms
    return len(matches) / len(query_terms)


def hybrid_search(
    query: str,
    n_results: int = 5,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> list[dict[str, Any]]:
    """Combine semantic vector search with keyword matching.

    Returns results sorted by combined score (higher is better).
    """
    # Get more results from vector search to allow for re-ranking
    semantic_results = vector_search(query, n_results=n_results * 2)

    if not semantic_results:
        return []

    # Calculate hybrid scores
    for result in semantic_results:
        # Convert distance to similarity (ChromaDB returns cosine distance)
        semantic_sim = max(0.0, 1.0 - result.get("distance", 1.0))
        kw_score = keyword_score(query, result.get("document", ""))

        result["semantic_score"] = semantic_sim
        result["keyword_score"] = kw_score
        result["combined_score"] = (
            semantic_weight * semantic_sim + keyword_weight * kw_score
        )

    # Sort by combined score, highest first
    semantic_results.sort(key=lambda x: x["combined_score"], reverse=True)

    # Return top N
    return semantic_results[:n_results]
