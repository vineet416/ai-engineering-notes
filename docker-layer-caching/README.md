# Docker layer caching: why one line of code reinstalled every package

Two Dockerfiles for the same small FastAPI app. The only difference is the order of three lines.

**Dockerfile.before**

```dockerfile
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

**Dockerfile.after**

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

## Why the order matters

Docker builds an image one step at a time and caches each step.
A step is reused only if it, and every step before it, is unchanged.
For `COPY`, unchanged means every copied file has the same content.

- In **before**, `COPY . .` copies all the code. Edit one line in `app/main.py` and that step changes, so `pip install` below it runs again from scratch.
- In **after**, `pip install` only depends on `requirements.txt`. A code change only re-runs the last `COPY . .`, and the install comes from the cache.

The app (`app/main.py`) is a tiny iris prediction API with scikit-learn and pandas. It is only there so `pip install` has real, heavy packages to download.

## Measure it yourself

You need Docker Desktop running. From this folder:

```
python measure_builds.py
```

For each Dockerfile the script does a full build with `--no-cache`, changes one line in `app/main.py`, rebuilds and times it, then puts the file back. It prints a table and saves it to `results.txt`.

Example run (numbers depend on your internet speed and machine):

```
Dockerfile              Full build    1-line change
---------------------------------------------------
Dockerfile.before            43.2s            43.6s
Dockerfile.after             42.1s             0.8s
```

In the rebuild output for `Dockerfile.after`, look for `RUN pip install ... CACHED`.

## Run the app

```
docker build -f Dockerfile.after -t layer-demo:after .
docker run --rm -p 8000:8000 layer-demo:after
```

Then open http://localhost:8000/docs and try `POST /predict`.

## Other things the team learned

- **Pin versions.** Docker caches a `RUN` step by its command text, not by what pip would download today. A cached install never picks up new package versions, so `requirements.txt` pins exact versions.
- **CI starts with no cache.** A fresh CI machine has an empty cache, so the reorder only helps there if the build reuses a saved cache, e.g. in GitHub Actions with `docker/build-push-action` and `cache-from: type=gha`, `cache-to: type=gha,mode=max`.
- **.dockerignore.** Without it, `COPY . .` also copies `.git`, `.venv` and `.env` into the image. See `.dockerignore` in this folder.
