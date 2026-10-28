"""Split documents into chunks of at most `size` tokens.

Simple and common approach: keep paragraphs together and pack them into a chunk
until the next one would go over the limit. A paragraph that is bigger than the
limit on its own is cut into word windows. No overlap, so the only thing that
changes between runs is the chunk size.
"""
from dataclasses import dataclass

from tokenizers import Tokenizer

from .tokenizer import count_tokens


@dataclass
class Chunk:
    doc: str
    text: str
    tokens: int


def _split_long_paragraph(tok: Tokenizer, para: str, size: int) -> list[str]:
    pieces, current = [], []
    for word in para.split():
        candidate = " ".join(current + [word])
        if current and count_tokens(tok, candidate) > size:
            pieces.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_document(tok: Tokenizer, doc: str, text: str, size: int) -> list[Chunk]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units = []
    for para in paragraphs:
        if count_tokens(tok, para) > size:
            units.extend(_split_long_paragraph(tok, para, size))
        else:
            units.append(para)

    chunks, current = [], []
    for unit in units:
        candidate = "\n\n".join(current + [unit])
        if current and count_tokens(tok, candidate) > size:
            body = "\n\n".join(current)
            chunks.append(Chunk(doc, body, count_tokens(tok, body)))
            current = [unit]
        else:
            current.append(unit)
    if current:
        body = "\n\n".join(current)
        chunks.append(Chunk(doc, body, count_tokens(tok, body)))
    return chunks


def chunk_corpus(tok: Tokenizer, docs: dict[str, str], size: int) -> list[Chunk]:
    out = []
    for name, text in docs.items():
        out.extend(chunk_document(tok, name, text, size))
    return out
