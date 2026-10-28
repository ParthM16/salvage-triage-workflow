import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_audit.db"
os.environ["USE_STUBS"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.api.main import app  # noqa: E402
from src.db.repository import init_db  # noqa: E402
from src.ml.llm import set_force_wrong_memo  # noqa: E402


@pytest.fixture(autouse=True)
def _setup():
    init_db()
    set_force_wrong_memo(False)
    yield
    set_force_wrong_memo(False)


@pytest.fixture
def client():
    return TestClient(app)
