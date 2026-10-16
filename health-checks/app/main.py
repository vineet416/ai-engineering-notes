import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import DB_PATH
from app.core.database import Base, create_db_file, engine
from app.models import task  # noqa: F401  (registers the tasks table)
from app.routers import health, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create app.db on the very first run, then make sure the tables exist.
    if not os.path.exists(DB_PATH):
        create_db_file(DB_PATH)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Health Checks Demo", lifespan=lifespan)
app.include_router(health.router)
app.include_router(tasks.router)
