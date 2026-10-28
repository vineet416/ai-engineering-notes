"""Show what the LLM would actually receive for one question, at each chunk size.

Same 1,000-token context budget for every size, Gemini Embedding 2 search.
Run:  python show_example.py --question 9
"""
import argparse
import textwrap

from rag_eval.chunking import chunk_corpus
from rag_eval.data import load_docs, load_questions
from rag_eval.metrics import is_hit
from rag_eval.api_models import ApiEmbeddingRetriever
from rag_eval.tokenizer import load_tokenizer
from run_eval import fill_budget


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=int, default=9)
    parser.add_argument("--sizes", type=int, nargs="+", default=[256, 512])
    args = parser.parse_args()

    tok = load_tokenizer()
    docs = load_docs()
    q = next(x for x in load_questions() if x["id"] == args.question)
    retriever = ApiEmbeddingRetriever()
    print(f"Q{q['id']}: {q['question']}")
    print(f"Answer sentence: {q['evidence']}\n")

    for size in args.sizes:
        chunks = chunk_corpus(tok, docs, size)
        retriever.index([c.text for c in chunks])
        context = fill_budget(chunks, retriever.search(q["question"], 50))
        used = sum(chunks[i].tokens for i in context)
        print(f"=== {size}-token chunks: {len(context)} chunks ({used} tokens) sent to the LLM ===")
        for rank, idx in enumerate(context, start=1):
            c = chunks[idx]
            mark = "ANSWER HERE" if is_hit(c.text, q["evidence"]) else "-"
            preview = textwrap.shorten(c.text.replace("\n", " "), 90)
            print(f"  #{rank} [{c.doc}] {mark}\n      {preview}")
        print()


if __name__ == "__main__":
    main()
