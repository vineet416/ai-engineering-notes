# How links and clicks are stored.
# Two tables: one row per short link, one row per click.
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)  # auto-increment, this is the counter
    # unique + index: every redirect looks a link up by its code
    code: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True)
    long_url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id"), index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    referrer: Mapped[Optional[str]] = mapped_column(String(2048))
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
