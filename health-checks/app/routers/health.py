# Two health endpoints that answer two different questions.
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine

from app.core.config import CHECK_TIMEOUT_SECONDS, EXTERNAL_API_URL
from app.core.database import get_engine
from app.health.checks import Check, database_check, http_check, run_checks

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live():
    # "Is the process alive and able to answer?" Nothing else.
    # No database, no outside calls. If this fails, restarting the app helps.
    # If the DB is down, restarting the app does NOT help, so the DB stays out of here.
    return {"status": "alive"}


def get_checks(engine: Engine = Depends(get_engine)) -> List[Check]:
    # Tests swap this out with dependency_overrides.
    return [
        Check("database", database_check(engine), critical=True),
        Check("external_api", http_check(EXTERNAL_API_URL, CHECK_TIMEOUT_SECONDS), critical=False),
    ]


@router.get("/ready")
async def ready(checks: List[Check] = Depends(get_checks)):
    # "Can this instance do real work right now?" Checks every dependency.
    report = await run_checks(checks, CHECK_TIMEOUT_SECONDS)
    # Load balancers and Kubernetes only read the status code, not the JSON.
    # So "database: down" inside a 200 response still counts as healthy.
    code = 503 if report["status"] == "not_ready" else 200
    return JSONResponse(status_code=code, content=report)
