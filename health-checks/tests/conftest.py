# Every test gets its own throwaway app.db in a temp folder.
# Nothing here touches the real app.db or the internet.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, create_db_file, get_db, get_engine, make_engine
from app.main import app


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    create_db_file(str(path))
    Base.metadata.create_all(bind=make_engine(str(path)))
    return path


@pytest.fixture
def client(db_path):
    engine = make_engine(str(db_path))
    Session = sessionmaker(bind=engine, autoflush=False)

    def test_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_db] = test_db
    yield TestClient(app)
    app.dependency_overrides.clear()
