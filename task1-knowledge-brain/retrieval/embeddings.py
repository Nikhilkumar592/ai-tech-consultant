"""Embedding generation with sentence-transformers and deterministic fallback."""
from __future__ import annotations

import hashlib
import logging
import math
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

_model = None
EMBEDDING_DIM = 384


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load or return cached embedding model, with fallback."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.info(f"SentenceTransformer not available ({e}). Using deterministic 384-dim fallback.")
            _model = "fallback"
    return _model


def _deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a deterministic normalized vector based on n-grams and tokens.

    Ensures semantic overlap has positive cosine similarity, perfectly
    compatible with ChromaDB vector search in offline/test environments.
    """
    if not text.strip():
        return [0.0] * dim

    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())

    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign * 1.5

        # Also add character trigrams for subword matching
        if len(word) >= 3:
            for i in range(len(word) - 2):
                tri = word[i:i+3]
                th = int(hashlib.md5(tri.encode()).hexdigest(), 16)
                tidx = th % dim
                vec[tidx] += 0.5

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    else:
        vec[0] = 1.0

    return vec


def generate_embeddings(
    texts: list[str],
    model_name: str = "all-MiniLM-L6-v2",
) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    if not texts:
        return []

    model = get_embedding_model(model_name)
    if model != "fallback":
        try:
            embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            logger.warning(f"SentenceTransformer encode failed: {e}. Using deterministic fallback.")

    return [_deterministic_embedding(t) for t in texts]


def generate_embedding(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
) -> list[float]:
    """Generate embedding for a single text."""
    result = generate_embeddings([text], model_name)
    return result[0] if result else [0.0] * EMBEDDING_DIM
