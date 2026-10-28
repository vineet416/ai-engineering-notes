"""Same documents, same questions, same retriever. Only the chunk size changes.
Retrievers: Gemini Embedding 2 (API) and BM25 (keyword).
Optional: --retrievers minilm runs all-MiniLM-L6-v2 locally (needs onnxruntime).

For each chunk size we measure:
  hit@1  - the very first chunk returned contains the answer
  hit@5  - one of the top 5 chunks contains the answer
  hit@1k tokens  - the answer is inside the context the LLM would get if we
                   fill a 1,000-token budget with the top chunks, in rank order
                   (more small chunks fit, fewer big ones). This is the fair one.

Run:  python run_eval.py
"""
import argparse
import time

from rag_eval.chunking import chunk_corpus
from rag_eval.data import load_docs, load_questions
from rag_eval.metrics import first_hit_rank
from rag_eval.retrievers import BM25Retriever, DenseRetriever

RETRIEVERS = {
    "gemini": "Gemini Emb 2",
    "minilm": "MiniLM (vector)",
    "bm25": "BM25 (keyword)",
}


def build_retriever(name):
    if name == "gemini":
        from rag_eval.api_models import ApiEmbeddingRetriever
        return ApiEmbeddingRetriever()
    if name == "minilm":
        return DenseRetriever()
    return BM25Retriever()
from rag_eval.tokenizer import load_tokenizer

CONTEXT_BUDGET = 1000  # tokens of context we can afford to send the LLM


def fill_budget(chunks, ranked_ids, budget=CONTEXT_BUDGET):
    """Take chunks in rank order until the next one would go over the token budget."""
    picked, used = [], 0
    for idx in ranked_ids:
        if picked and used + chunks[idx].tokens > budget:
            break
        picked.append(idx)
        used += chunks[idx].tokens
    return picked


def evaluate(retriever, chunks, questions):
    texts = [c.text for c in chunks]
    retriever.index(texts)
    hits1 = hits5 = hits_budget = 0
    sent = []
    misses = []
    for q in questions:
        ranked = retriever.search(q["question"], k=50)
        rank = first_hit_rank(texts, ranked, q["evidence"])
        context = fill_budget(chunks, ranked)
        sent.append(len(context))
        hits1 += rank == 1
        hits5 += rank is not None and rank <= 5
        hits_budget += first_hit_rank(texts, context, q["evidence"]) is not None
        if rank != 1:
            misses.append(q["id"])
    return hits1, hits5, hits_budget, sum(sent) / len(sent), misses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 128, 256, 512])
    parser.add_argument("--retrievers", nargs="+", choices=list(RETRIEVERS),
                        default=["gemini", "bm25"])
    parser.add_argument("--show-misses", action="store_true")
    args = parser.parse_args()

    tok = load_tokenizer()
    docs = load_docs()
    questions = load_questions()
    n = len(questions)
    total_tokens = sum(len(tok.encode(t, add_special_tokens=False).ids) for t in docs.values())
    print(f"{len(docs)} docs, {total_tokens:,} tokens, {n} questions\n")

    retrievers = {RETRIEVERS[r]: build_retriever(r) for r in args.retrievers}
    header = f"{'retriever':<17}{'chunk':>6}{'chunks':>8}{'hit@1':>8}{'hit@5':>8}{'chunks sent':>13}{'hit@1k tok':>12}"
    print(header)
    print("-" * len(header))
    all_misses = {}
    for name, retriever in retrievers.items():
        for size in args.sizes:
            start = time.perf_counter()
            chunks = chunk_corpus(tok, docs, size)
            h1, h5, hb, avg_sent, misses = evaluate(retriever, chunks, questions)
            all_misses[(name, size)] = misses
            pct = lambda x: f"{x}/{n}"
            print(f"{name:<17}{size:>6}{len(chunks):>8}{pct(h1):>8}{pct(h5):>8}{avg_sent:>13.1f}{pct(hb):>12}"
                  f"   ({time.perf_counter() - start:.1f}s)")
        print()

    if args.show_misses:
        for (name, size), ids in all_misses.items():
            print(f"{name} @ {size}: not ranked #1 -> questions {ids}")


if __name__ == "__main__":
    main()
