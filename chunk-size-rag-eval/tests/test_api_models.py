"""Checks the API retriever with a fake client, so tests never call the real API."""
from types import SimpleNamespace

import numpy as np

from rag_eval import api_models
from rag_eval.api_models import ApiEmbeddingRetriever, answer


class FakeEmbeddings:
    def __init__(self):
        self.calls = 0

    def create(self, model, input):
        self.calls += 1
        def vec(text):  # tiny fake "meaning": does the text talk about memory or CORS?
            t = text.lower()
            return [1.0 if ("memory" in t or "ram" in t) else 0.0, 1.0 if "cors" in t else 0.0, 0.1]
        data = [SimpleNamespace(index=i, embedding=vec(t)) for i, t in enumerate(input)]
        return SimpleNamespace(data=list(reversed(data)))  # out of order on purpose


class FakeChat:
    def create(self, model, messages):
        msg = SimpleNamespace(content=" Not in the docs. ")
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def fake_client():
    return SimpleNamespace(embeddings=FakeEmbeddings(),
                           chat=SimpleNamespace(completions=FakeChat()))


def test_search_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(api_models, "CACHE_DIR", tmp_path)
    client = fake_client()
    r = ApiEmbeddingRetriever(client=client, model="fake")
    r.index(["bytes stay in memory", "CORS allows origins", "background tasks"])
    assert r.search("will it use my RAM?", k=1) == [0]
    calls = client.embeddings.calls
    r2 = ApiEmbeddingRetriever(client=client, model="fake")  # loads the disk cache
    r2.index(["bytes stay in memory", "CORS allows origins", "background tasks"])
    assert client.embeddings.calls == calls
    assert np.allclose(np.linalg.norm(r2.vectors, axis=1), 1.0)


def test_answer_strips_text():
    assert answer(fake_client(), "q", "ctx", model="fake") == "Not in the docs."
