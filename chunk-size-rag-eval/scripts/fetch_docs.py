"""Download the FastAPI tutorial pages used as the test documents and clean them.

You don't need to run this: the cleaned files are already in data/docs/.
It's here so anyone can see exactly where the documents came from.
FastAPI docs are MIT licensed: https://github.com/fastapi/fastapi
"""
import re
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial"
PAGES = [
    "query-params", "path-params", "body", "request-forms", "request-files",
    "handling-errors", "dependencies/index", "security/first-steps", "cors",
    "middleware", "background-tasks", "response-status-code", "response-model",
    "bigger-applications", "sql-databases", "cookie-params", "header-params",
    "path-params-numeric-validations", "query-params-str-validations",
    "static-files", "testing", "debugging",
]
OUT = Path(__file__).resolve().parent.parent / "data" / "docs"


def clean(markdown: str) -> str:
    text = re.sub(r"\{\*.*?\*\}", "", markdown)          # code-include placeholders
    text = re.sub(r"\s*\{ #[^}]+\}", "", text)            # heading anchors
    text = re.sub(r"^/// ?.*$", "", text, flags=re.M)     # admonition markers
    return re.sub(r"\n{3,}", "\n\n", text)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        with urllib.request.urlopen(f"{BASE}/{page}.md") as resp:
            md = resp.read().decode("utf-8")
        name = page.replace("/", "_") + ".txt"
        (OUT / name).write_text(clean(md), encoding="utf-8")
        print("saved", name)
