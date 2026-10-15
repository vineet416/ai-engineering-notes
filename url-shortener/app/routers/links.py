# Routes only: read the request, call the service, send the response.
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import BASE_URL
from app.core.database import get_db, get_session_factory
from app.schemas.link import LinkOut, ShortenRequest, StatsOut
from app.services import link_service

router = APIRouter()


@router.post("/shorten", response_model=LinkOut, status_code=201)
def shorten(body: ShortenRequest, db: Session = Depends(get_db)):
    try:
        link = link_service.create_link(db, str(body.url), body.alias)
    except link_service.AliasTaken as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return LinkOut(code=link.code, short_url=f"{BASE_URL}/{link.code}", long_url=link.long_url)


@router.get("/stats/{code}", response_model=StatsOut)
def stats(code: str, db: Session = Depends(get_db)):
    link = link_service.resolve(db, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    return link_service.get_stats(db, link)


@router.get("/{code}")
def redirect(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    session_factory=Depends(get_session_factory),
):
    link = link_service.resolve(db, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Log the click AFTER the response goes out, so the user isn't kept waiting.
    background_tasks.add_task(
        link_service.record_click,
        session_factory,
        link.id,
        request.headers.get("referer"),
        request.headers.get("user-agent"),
    )
    # 302, not 301. A 301 gets cached by the browser, so the second click
    # never reaches this server and never gets counted.
    return RedirectResponse(link.long_url, status_code=302)
