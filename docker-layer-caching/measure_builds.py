"""Time two Dockerfiles: a full build, then a rebuild after a one-line code change.

Run from this folder with Docker running:
    python measure_builds.py

For each Dockerfile it:
  1. builds the image from scratch (--no-cache), like a first build
  2. edits one line in app/main.py (STARTUP_MESSAGE)
  3. rebuilds and times it, which is what you wait for after every code change
  4. puts app/main.py back the way it was

Results are printed as a table and saved to results.txt.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
MAIN_PY = HERE / "app" / "main.py"
BASE_IMAGE = "python:3.12-slim"
VARIANTS = [("before", "Dockerfile.before"), ("after", "Dockerfile.after")]


def run(cmd, show_output, must_pass=True):
    """Run a command and return how long it took in seconds (None if it failed)."""
    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=HERE,
        stdout=None if show_output else subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    seconds = time.perf_counter() - start
    if result.returncode != 0:
        if not must_pass:
            return None
        if result.stdout:
            print(result.stdout)
        sys.exit(f"Command failed: {' '.join(cmd)}")
    return seconds


def build(name, dockerfile, no_cache, show_output):
    cmd = ["docker", "build", "--progress=plain", "-f", dockerfile, "-t", f"layer-demo:{name}"]
    if no_cache:
        cmd.append("--no-cache")
    cmd.append(".")
    return run(cmd, show_output)


def change_one_line(original):
    """Simulate a tiny code change: a new startup log message."""
    stamp = datetime.now().strftime("%H:%M:%S")
    changed = original.replace(
        'STARTUP_MESSAGE = "Iris model is ready"',
        f'STARTUP_MESSAGE = "Iris model is ready (edited at {stamp})"',
    )
    if changed == original:
        sys.exit("Could not find the STARTUP_MESSAGE line in app/main.py")
    MAIN_PY.write_text(changed, encoding="utf-8")


def fmt(seconds):
    if seconds >= 60:
        return f"{int(seconds // 60)}m {seconds % 60:04.1f}s"
    return f"{seconds:.1f}s"


def main():
    print(f"Pulling {BASE_IMAGE} first, so download time of the base image is not counted...")
    if run(["docker", "pull", BASE_IMAGE], show_output=False, must_pass=False) is None:
        # Pull can fail (no internet, Docker Hub rate limit). Fine if we already have it.
        run(["docker", "image", "inspect", BASE_IMAGE], show_output=False)
        print("Pull failed, using the copy of the base image already on this machine.")

    original = MAIN_PY.read_text(encoding="utf-8")
    results = {}
    try:
        for name, dockerfile in VARIANTS:
            print(f"\n=== {dockerfile}: full build from scratch (this is the slow one) ===")
            full = build(name, dockerfile, no_cache=True, show_output=False)
            print(f"Done in {fmt(full)}")

            change_one_line(original)
            print(f"\n=== {dockerfile}: rebuild after changing ONE line in app/main.py ===")
            rebuild = build(name, dockerfile, no_cache=False, show_output=True)
            MAIN_PY.write_text(original, encoding="utf-8")
            print(f"Rebuild done in {fmt(rebuild)}")

            results[dockerfile] = (full, rebuild)
    finally:
        # Always put main.py back, even if a build fails or you press Ctrl+C.
        MAIN_PY.write_text(original, encoding="utf-8")

    lines = [
        "",
        "Docker build times",
        f"{'Dockerfile':<20}{'Full build':>14}{'1-line change':>17}",
        "-" * 51,
    ]
    for dockerfile, (full, rebuild) in results.items():
        lines.append(f"{dockerfile:<20}{fmt(full):>14}{fmt(rebuild):>17}")
    before = results["Dockerfile.before"][1]
    after = results["Dockerfile.after"][1]
    lines.append("-" * 51)
    lines.append(f"Rebuild after a code change: {fmt(before)} -> {fmt(after)} ({before / after:.0f}x faster)")

    report = "\n".join(lines)
    print(report)
    (HERE / "results.txt").write_text(report.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
