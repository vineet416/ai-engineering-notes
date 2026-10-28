import pytest

from rag_eval.retrievers import BM25Retriever, DenseRetriever

TEXTS = [
    "Uploaded files read as bytes are kept fully in memory.",
    "CORS lets a browser frontend call a backend on another origin.",
    "Background tasks run after the response is sent.",
]


def test_bm25_finds_keyword_match():
    r = BM25Retriever()
    r.index(TEXTS)
    assert r.search("which origin can call my backend? CORS", k=1) == [1]


def test_vector_search_finds_meaning_match():
    pytest.importorskip("onnxruntime")  # optional local model
    r = DenseRetriever()
    r.index(TEXTS)
    assert r.search("does a big upload eat my RAM?", k=1) == [0]
