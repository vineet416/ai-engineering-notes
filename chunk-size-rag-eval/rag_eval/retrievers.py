"""Local retrievers. The main one, Gemini Embedding 2, is in api_models.py.

- BM25: keyword search, no model involved.
- Dense (optional): all-MiniLM-L6-v2 running locally. Needs `pip install onnxruntime`
  and downloads the model (about 80 MB) the first time.
"""
import re

import numpy as np
from rank_bm25 import BM25Okapi
from tokenizers import Tokenizer

from .tokenizer import model_dir

MAX_LEN = 512  # the model's position limit, so the model reads (almost) every token of a 512 chunk


class DenseRetriever:
    def __init__(self):
        import onnxruntime as ort  # only needed for this optional retriever

        path = model_dir()
        self.tok = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tok.enable_truncation(max_length=MAX_LEN)
        self.tok.enable_padding(pad_id=0, pad_token="[PAD]")
        self.session = ort.InferenceSession(str(path / "model.onnx"),
                                            providers=["CPUExecutionProvider"])
        self.vectors = None

    def embed(self, texts: list[str], batch: int = 32) -> np.ndarray:
        out = []
        for i in range(0, len(texts), batch):
            enc = self.tok.encode_batch(texts[i:i + batch])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            hidden = self.session.run(None, {
                "input_ids": ids,
                "attention_mask": mask,
                "token_type_ids": np.zeros_like(ids),
            })[0]
            # mean pooling over real tokens, then L2-normalise (what sentence-transformers does)
            m = mask[..., None].astype(np.float32)
            pooled = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)
            out.append(pooled / np.linalg.norm(pooled, axis=1, keepdims=True))
        return np.vstack(out)

    def index(self, chunk_texts: list[str]) -> None:
        self.vectors = self.embed(chunk_texts)

    def search(self, query: str, k: int) -> list[int]:
        q = self.embed([query])[0]
        scores = self.vectors @ q  # cosine similarity, vectors are normalised
        return list(np.argsort(-scores)[:k])


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


class BM25Retriever:
    def index(self, chunk_texts: list[str]) -> None:
        self.bm25 = BM25Okapi([_words(t) for t in chunk_texts])

    def search(self, query: str, k: int) -> list[int]:
        scores = self.bm25.get_scores(_words(query))
        return list(np.argsort(-scores, kind="stable")[:k])
