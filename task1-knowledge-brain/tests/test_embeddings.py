"""Tests for embeddings generation."""
import pytest
from retrieval.embeddings import generate_embedding, generate_embeddings, EMBEDDING_DIM


def test_generate_single_embedding():
    text = "How do I setup Stripe payments?"
    emb = generate_embedding(text)

    assert isinstance(emb, list)
    assert len(emb) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in emb)
    # Check normalization: sum of squares should be approximately 1.0
    norm_sq = sum(x * x for x in emb)
    assert abs(norm_sq - 1.0) < 0.05


def test_generate_multiple_embeddings():
    texts = ["Stripe setup", "PayPal configuration", "Email notifications"]
    embs = generate_embeddings(texts)

    assert len(embs) == 3
    assert len(embs[0]) == EMBEDDING_DIM
    assert len(embs[1]) == EMBEDDING_DIM


def test_empty_text_embedding():
    emb = generate_embedding("")
    assert len(emb) == EMBEDDING_DIM
    embs_empty = generate_embeddings([])
    assert embs_empty == []


def test_semantic_similarity_overlap():
    emb1 = generate_embedding("configure stripe payments")
    emb2 = generate_embedding("stripe payment gateway setup")
    emb_unrelated = generate_embedding("quantum thermodynamics astrophysics")

    dot_related = sum(a * b for a, b in zip(emb1, emb2))
    dot_unrelated = sum(a * b for a, b in zip(emb1, emb_unrelated))

    assert dot_related > dot_unrelated
