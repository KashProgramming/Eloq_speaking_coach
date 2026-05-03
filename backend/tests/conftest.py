import os
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_DB_PATH = Path("./test_backend.db").resolve()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["CLOUDINARY_CLOUD_NAME"] = "test-cloud"
os.environ["CLOUDINARY_API_KEY"] = "test-cloud-key"
os.environ["CLOUDINARY_API_SECRET"] = "test-cloud-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from app.api.deps import get_db  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402


_original_httpx_client_init = httpx.Client.__init__


def _compat_httpx_client_init(self, *args, **kwargs):
    """
    Starlette's older TestClient passes an `app=` kwarg into httpx.Client.
    Newer httpx versions removed that constructor parameter, so tests fail
    before any application code runs. We ignore that kwarg here because
    TestClient already provides the ASGI transport explicitly.
    """
    kwargs.pop("app", None)
    return _original_httpx_client_init(self, *args, **kwargs)


if getattr(httpx.Client.__init__, "__name__", "") != "_compat_httpx_client_init":
    httpx.Client.__init__ = _compat_httpx_client_init


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    get_settings.cache_clear()
    _reset_db()
    yield


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    app = create_app()
    app.state.limiter.enabled = False

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
