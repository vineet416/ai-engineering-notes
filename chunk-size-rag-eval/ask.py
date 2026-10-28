"""Real answers from GPT-5.4 mini, using the chunks each chunk size retrieves.

One question, side by side:   python ask.py --question 9
All 46 questions per size:   python ask.py --all
  (counts how often the model had to say "Not in the docs" because the
   right chunk never reached it)
"""
import argparse

from rag_eval.api_models import ApiEmbeddingRetriever, answer, make_client
from rag_eval.chunking import chunk_corpus
from rag_eval.data import load_docs, load_questions
from rag_eval.metrics import first_hit_rank
from rag_eval.tokenizer import load_tokenizer
from run_eval import fill_budget


def build_context(chunks, ids):
    return "\n\n---\n\n".join(chunks[i].text for i in ids)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=int, default=9)
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 256, 512])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    tok = load_tokenizer()
    docs = load_docs()
    questions = load_questions()
    client = make_client()
    retriever = ApiEmbeddingRetriever(client=client)
    if not args.all:
        questions = [q for q in questions if q["id"] == args.question]
        print(f"Q{args.question}: {questions[0]['question']}\n")

    for size in args.sizes:
        chunks = chunk_corpus(tok, docs, size)
        texts = [c.text for c in chunks]
        retriever.index(texts)
        not_found = 0
        for q in questions:
            ids = fill_budget(chunks, retriever.search(q["question"], 50))
            reply = answer(client, q["question"], build_context(chunks, ids))
            not_found += "not in the docs" in reply.lower()
            if not args.all:
                has_answer = first_hit_rank(texts, ids, q["evidence"]) is not None
                print(f"=== {size}-token chunks (answer chunk sent: {'yes' if has_answer else 'no'}) ===")
                print(reply, "\n")
        if args.all:
            print(f"{size:>4}-token chunks: 'Not in the docs' for {not_found}/{len(questions)} questions")


if __name__ == "__main__":
    main()
