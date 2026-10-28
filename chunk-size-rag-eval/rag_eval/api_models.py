"""Gemini Embedding 2 and GPT-5.4 mini through an OpenAI-compatible endpoint (Euri).

Embeddings are cached on disk, so re-running the eval doesn't pay for the
same chunk twice. Each chunk size creates new chunks, so the first full run
embeds the whole corpus 4 times (about 160k tokens).
"""
import hashlib
import pickle
import time

import numpy as np
from openai import OpenAI

from .config import ROOT, settings

CACHE_DIR = ROOT / ".cache"


def make_client() -> OpenAI:
    if not settings.euri_api_key:
        raise RuntimeError("EURI_API_KEY is missing. Copy .env.example to .env and add your key.")
    return OpenAI(api_key=settings.euri_api_key, base_url=settings.euri_base_url)


def _with_retry(fn, tries: int = 5):
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:  # rate limits, timeouts
            if attempt == tries - 1:
                raise
            wait = 2 ** attempt
            print(f"  API error ({type(exc).__name__}), retrying in {wait}s...")
            time.sleep(wait)


class ApiEmbeddingRetriever:
    def __init__(self, client=None, model: str | None = None, batch: int = 32):
        self.client = client or make_client()
        self.model = model or settings.embedding_model
        self.batch = batch
        self.cache_file = CACHE_DIR / f"emb-{self.model}.pkl"
        self.cache = pickle.loads(self.cache_file.read_bytes()) if self.cache_file.exists() else {}
        self.vectors = None

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def embed(self, texts: list[str]) -> np.ndarray:
        missing = list({self._key(t): t for t in texts if self._key(t) not in self.cache}.items())
        for i in range(0, len(missing), self.batch):
            part = missing[i:i + self.batch]
            resp = _with_retry(lambda: self.client.embeddings.create(
                model=self.model, input=[t for _, t in part]))
            for (key, _), item in zip(part, sorted(resp.data, key=lambda d: d.index)):
                self.cache[key] = np.asarray(item.embedding, dtype=np.float32)
        if missing:
            CACHE_DIR.mkdir(exist_ok=True)
            self.cache_file.write_bytes(pickle.dumps(self.cache))
        vecs = np.vstack([self.cache[self._key(t)] for t in texts])
        return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    def index(self, chunk_texts: list[str]) -> None:
        self.vectors = self.embed(chunk_texts)

    def search(self, query: str, k: int) -> list[int]:
        scores = self.vectors @ self.embed([query])[0]
        return list(np.argsort(-scores)[:k])


SYSTEM_PROMPT = (
    "Answer the question using only the context. "
    "If the context does not contain the answer, reply exactly: Not in the docs."
)


def answer(client, question: str, context: str, model: str | None = None) -> str:
    resp = _with_retry(lambda: client.chat.completions.create(
        model=model or settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    ))
    return resp.choices[0].message.content.strip()
