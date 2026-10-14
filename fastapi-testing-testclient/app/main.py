from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import APP_NAME
from app.core.database import Base, engine
from app.models import task  # noqa: F401  registers the Task table
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # makes tasks.db on first run
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.include_router(tasks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
