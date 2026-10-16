# Database connection + the get_db() dependency.
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import DB_PATH


def make_engine(db_path: str) -> Engine:
    # mode=rw: open the file only if it already exists.
    # By default SQLite quietly creates a brand new EMPTY database when the
    # file is missing, so the app would look "up" with all its data gone.
    def connect():
        return sqlite3.connect(f"file:{db_path}?mode=rw", uri=True, check_same_thread=False)

    # NullPool: open a fresh connection every time instead of keeping one open,
    # so each health check really talks to the database.
    return create_engine("sqlite://", creator=connect, poolclass=NullPool)


def create_db_file(db_path: str) -> None:
    # Only used once at startup to create app.db on the very first run.
    sqlite3.connect(db_path).close()


engine = make_engine(DB_PATH)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
