# main.py: the front door. It only creates the app and plugs in the routers.
# It stays small no matter how big the project gets.

from fastapi import FastAPI

from app.core.config import APP_NAME, APP_VERSION
from app.routers import tasks

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.include_router(tasks.router)


@app.get("/")
def health_check():
    return {"status": "ok", "app": APP_NAME}
