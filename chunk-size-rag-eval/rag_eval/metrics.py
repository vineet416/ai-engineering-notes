"""A retrieved chunk is a hit if it contains the full answer sentence.

Each question in data/questions.json has an `evidence` string copied word for
word from the docs. If a chunk split cuts that sentence in half, it's a miss,
which is exactly what happens in a real RAG app.
"""
import re


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def is_hit(chunk_text: str, evidence: str) -> bool:
    return normalise(evidence) in normalise(chunk_text)


def first_hit_rank(chunk_texts: list[str], ranked_ids: list[int], evidence: str):
    """1-based rank of the first chunk containing the evidence, or None."""
    for rank, idx in enumerate(ranked_ids, start=1):
        if is_hit(chunk_texts[idx], evidence):
            return rank
    return None
