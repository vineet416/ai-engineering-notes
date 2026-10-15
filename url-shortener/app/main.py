from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import link_cache
from app.core.database import Base, engine
from app.models import link  # noqa: F401  (registers the tables)
from app.routers import links


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates links.db on first run
    yield


app = FastAPI(title="URL Shortener", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "cache_size": len(link_cache), "cache_hits": link_cache.hits, "cache_misses": link_cache.misses}


# included last, so /{code} doesn't swallow /health or /docs
app.include_router(links.router)
