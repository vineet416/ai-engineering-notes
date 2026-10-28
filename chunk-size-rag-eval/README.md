# Chunk size vs retrieval quality (RAG)

Same documents, same questions, same embedding model. Only the chunk size changes.
This measures how often the chunk that actually contains the answer reaches the LLM.

## What's inside

- `data/docs/`: 22 pages of the FastAPI tutorial (about 40k tokens), cleaned to plain text. Source: [fastapi/fastapi](https://github.com/fastapi/fastapi) docs, MIT licensed. `scripts/fetch_docs.py` shows how they were downloaded.
- `data/questions.json`: 46 questions written the way a developer would ask them. Each one stores the exact sentence from the docs that answers it (`evidence`). A chunk counts as a hit only if it contains that whole sentence.
- `rag_eval/chunking.py`: keeps paragraphs together and packs them into chunks of at most N tokens (counted with `data/tokenizer.json`). No overlap.
- `rag_eval/retrievers.py`: BM25 keyword search, plus an optional local `all-MiniLM-L6-v2` retriever.
- `data/tokenizer.json`: the BERT WordPiece tokenizer used to count chunk sizes in tokens (from all-MiniLM-L6-v2, Apache 2.0). It ships with the repo, so no model download.
- `rag_eval/api_models.py`: `gemini-embedding-2` embeddings and `gpt-5.4-mini` answers through an OpenAI-compatible endpoint (Euri). Embeddings are cached in `.cache/`.
- `ask.py`: real LLM answers from the chunks each size retrieves.
- `run_eval.py`: the comparison table.
- `show_example.py`: shows exactly which chunks the LLM would receive for one question at different chunk sizes.

## The metrics

- `hit@1`: the first chunk returned contains the answer.
- `hit@5`: one of the top 5 chunks contains the answer. Careful: 5 big chunks are far more text than 5 small ones, so this favours big chunks.
- `hit@1k tok`: top chunks are added in rank order until a 1,000-token context budget is full. This is the fair comparison across sizes.

## Run it (Windows, PowerShell)

```powershell
cd D:\AI\builds\chunk-size-rag-eval
```

```powershell
python -m venv venv
```

```powershell
venv\Scripts\activate
```

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and put your key in it (never commit `.env`):

```powershell
copy .env.example .env
```

```powershell
python run_eval.py
```

No API key? Run keyword search plus a small local model instead (downloads about 80 MB once):

```powershell
python -m pip install onnxruntime
```

```powershell
python run_eval.py --retrievers minilm bm25
```

```powershell
python show_example.py --question 9
```

```powershell
python ask.py --question 9
```

```powershell
python ask.py --all
```

```powershell
python -m pytest -q
```

The tests use a fake API client, so they never spend API credits.

The first run embeds every chunk of every size with Gemini Embedding 2 (about 160k tokens). They're cached in `.cache/`, so later runs only embed the questions.

Try your own sizes: `python run_eval.py --sizes 100 200 300 400`. Add `--show-misses` to see which questions each setup got wrong.
