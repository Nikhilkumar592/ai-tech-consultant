"""ChromaDB vector store for persistent semantic search."""
from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from retrieval.embeddings import generate_embeddings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "knowledge_chunks"


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info(f"ChromaDB client initialized at {settings.chroma_path}")
    return _client


def get_collection() -> chromadb.Collection:
    """Get or create the knowledge chunks collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready, count={_collection.count()}")
    return _collection


def add_chunks(
    chunk_ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
) -> int:
    """Add or update chunks in the vector store."""
    if not chunk_ids:
        return 0

    collection = get_collection()
    embeddings = generate_embeddings(texts)

    # ChromaDB upsert handles both add and update
    collection.upsert(
        ids=chunk_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(f"Upserted {len(chunk_ids)} chunks into vector store")
    return len(chunk_ids)


def search(
    query: str,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Search for similar chunks.

    Returns list of dicts with: id, document, metadata, distance.
    """
    collection = get_collection()
    query_embedding = generate_embeddings([query])

    if not query_embedding:
        return []

    kwargs: dict[str, Any] = {
        "query_embeddings": query_embedding,
        "n_results": min(n_results, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    try:
        results = collection.query(**kwargs)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []

    items = []
    if results and results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 1.0,
            })

    return items


def delete_chunks(chunk_ids: list[str]) -> int:
    """Delete chunks by ID."""
    if not chunk_ids:
        return 0

    collection = get_collection()
    collection.delete(ids=chunk_ids)
    logger.info(f"Deleted {len(chunk_ids)} chunks from vector store")
    return len(chunk_ids)


def delete_by_article(article_id: str) -> int:
    """Delete all chunks belonging to an article."""
    collection = get_collection()
    try:
        # Get chunks for this article
        results = collection.get(
            where={"article_id": article_id},
            include=[],
        )
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for article {article_id}")
            return len(results["ids"])
    except Exception as e:
        logger.warning(f"Failed to delete chunks for article {article_id}: {e}")
    return 0


def get_stats() -> dict[str, Any]:
    """Get vector store statistics."""
    try:
        collection = get_collection()
        return {
            "total_chunks": collection.count(),
            "collection_name": COLLECTION_NAME,
        }
    except Exception:
        return {"total_chunks": 0, "collection_name": COLLECTION_NAME}
