# The actual rules of the shortener. No HTTP code in here,
# so the tests (or a script) can call these directly.
from collections import Counter
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cache import link_cache
from app.core.config import ID_OFFSET, RESERVED_ALIASES
from app.models.link import Click, Link
from app.services import codes


class AliasTaken(Exception):
    pass


def create_link(db: Session, long_url: str, alias: Optional[str] = None) -> Link:
    if alias is not None:
        if alias.lower() in RESERVED_ALIASES:
            raise AliasTaken(f"'{alias}' is reserved")
        link = Link(code=alias, long_url=long_url)
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            # the unique index on code is the real guard, even if two
            # requests ask for the same alias at the same moment
            db.rollback()
            raise AliasTaken(f"'{alias}' is already taken")
        db.refresh(link)
        return link

    # 1. insert the row first so the database gives us the next id
    link = Link(long_url=long_url)
    db.add(link)
    db.flush()
    # 2. turn that id into the code
    link.code = codes.encode(link.id + ID_OFFSET)
    db.commit()
    db.refresh(link)
    return link


def resolve(db: Session, code: str) -> Optional[Link]:
    """Find a link by code, checking the cache before the database."""
    cached = link_cache.get(code)
    if cached is not None:
        link_id, long_url = cached
        return Link(id=link_id, code=code, long_url=long_url)  # no database hit

    link = db.scalar(select(Link).where(Link.code == code))
    if link is not None:
        link_cache.set(code, (link.id, link.long_url))
    return link


def record_click(session_factory, link_id: int, referrer: Optional[str], user_agent: Optional[str]) -> None:
    """Runs after the redirect has already been sent to the user."""
    db = session_factory()
    try:
        db.add(Click(link_id=link_id, referrer=referrer, user_agent=user_agent))
        db.commit()
    finally:
        db.close()


def get_stats(db: Session, link: Link) -> dict:
    total = db.scalar(select(func.count()).select_from(Click).where(Click.link_id == link.id)) or 0

    by_day_rows = db.execute(
        select(func.date(Click.clicked_at), func.count())
        .where(Click.link_id == link.id)
        .group_by(func.date(Click.clicked_at))
        .order_by(func.date(Click.clicked_at))
    ).all()

    referrers = Counter(
        ref or "direct"
        for ref in db.scalars(select(Click.referrer).where(Click.link_id == link.id))
    )

    return {
        "code": link.code,
        "long_url": link.long_url,
        "total_clicks": total,
        "clicks_by_day": {str(day): count for day, count in by_day_rows},
        "top_referrers": [{"referrer": r, "clicks": c} for r, c in referrers.most_common(5)],
    }
