import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from app.db.base import SessionLocal, init_db


@pytest.fixture(scope="session", autouse=True)
def _db_ready():
    init_db()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()
