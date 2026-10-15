# Database connection + dependencies.
# Routes never build a session themselves. They ask FastAPI for one,
# which is what lets the tests hand them an in-memory database instead.
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory():
    # The click logger runs AFTER the redirect is sent, when the request's
    # session may already be closed. So it opens its own session from this.
    return SessionLocal
