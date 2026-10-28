import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load_docs() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((DATA / "docs").glob("*.txt"))}


def load_questions() -> list[dict]:
    return json.loads((DATA / "questions.json").read_text(encoding="utf-8"))
