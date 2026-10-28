import pytest

from rag_eval.chunking import chunk_corpus, chunk_document
from rag_eval.data import load_docs
from rag_eval.tokenizer import count_tokens, load_tokenizer


@pytest.fixture(scope="module")
def tok():
    return load_tokenizer()


@pytest.mark.parametrize("size", [64, 128, 256, 512])
def test_no_chunk_goes_over_the_limit(tok, size):
    chunks = chunk_corpus(tok, load_docs(), size)
    assert max(c.tokens for c in chunks) <= size


@pytest.mark.parametrize("size", [64, 512])
def test_chunking_keeps_every_word(tok, size):
    docs = load_docs()
    for name, text in docs.items():
        chunks = chunk_document(tok, name, text, size)
        assert " ".join(c.text for c in chunks).split() == text.split()


def test_smaller_size_means_more_chunks(tok):
    docs = load_docs()
    counts = [len(chunk_corpus(tok, docs, s)) for s in (64, 128, 256, 512)]
    assert counts == sorted(counts, reverse=True)


def test_long_paragraph_is_cut_into_windows(tok):
    text = " ".join(["word"] * 300)
    chunks = chunk_document(tok, "x", text, 50)
    assert len(chunks) > 1
    assert all(count_tokens(tok, c.text) <= 50 for c in chunks)
