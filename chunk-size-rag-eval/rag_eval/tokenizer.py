"""Token counting for chunk sizes, plus the optional local MiniLM model download.

Chunk sizes are counted with a standard BERT WordPiece tokenizer
(data/tokenizer.json, from all-MiniLM-L6-v2, Apache 2.0). It ships with the
repo, so nothing is downloaded unless you ask for the local MiniLM retriever.
"""
import tarfile
import urllib.request
from pathlib import Path

from tokenizers import Tokenizer

# Same ONNX export of sentence-transformers/all-MiniLM-L6-v2 that Chroma uses by default.
MODEL_URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / ".model_cache" / "onnx"
TOKENIZER_FILE = ROOT / "data" / "tokenizer.json"


def model_dir() -> Path:
    """Only used by the optional local MiniLM retriever."""
    if not (MODEL_DIR / "model.onnx").exists():
        MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
        archive = MODEL_DIR.parent / "onnx.tar.gz"
        print("Downloading all-MiniLM-L6-v2 (about 80 MB, only once)...")
        urllib.request.urlretrieve(MODEL_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(MODEL_DIR.parent)
        archive.unlink()
    return MODEL_DIR


def load_tokenizer() -> Tokenizer:
    tok = Tokenizer.from_file(str(TOKENIZER_FILE))
    tok.no_truncation()
    tok.no_padding()
    return tok


def count_tokens(tok: Tokenizer, text: str) -> int:
    return len(tok.encode(text, add_special_tokens=False).ids)
