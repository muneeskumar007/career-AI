import os
import shutil
import tempfile

# SECRET_KEY etc. must exist before app.config.settings is imported anywhere.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-prod")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "careerai_test")
# The limiter's in-memory storage lives for the whole pytest process, and many
# unrelated tests share one client IP ("127.0.0.1"), so production-strict
# limits would trip well before a real abuser ever would. Rate-limiting
# itself is exercised separately in test_rate_limiting.py with its own tiny limit.
os.environ.setdefault("RATE_LIMIT_LOGIN", "1000/minute")
os.environ.setdefault("RATE_LIMIT_REGISTER", "1000/minute")
os.environ.setdefault("RATE_LIMIT_DEFAULT", "10000/minute")
# Uploaded-file tests must never write into the real backend/uploads/ folder
# that ships with the repo — isolate to a throwaway temp dir instead.
_TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="careerai_test_uploads_")
os.environ.setdefault("UPLOAD_DIR", _TEST_UPLOAD_DIR)

import atexit

atexit.register(lambda: shutil.rmtree(_TEST_UPLOAD_DIR, ignore_errors=True))

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.api.deps import get_db
from app.main import app


@pytest_asyncio.fixture
async def test_db():
    """An in-memory Mongo-compatible database — no real MongoDB required."""
    client = AsyncMongoMockClient()
    db = client["careerai_test"]
    await db.users.create_index("email", unique=True)
    yield db


@pytest_asyncio.fixture
async def client(test_db):
    """An HTTP client wired to the FastAPI app with the real DB dependency
    swapped for the in-memory one. The app's lifespan (real Mongo connect)
    deliberately never runs in tests — nothing here depends on it."""
    app.dependency_overrides[get_db] = lambda: test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client):
    """Registers and logs in a candidate, returning (email, password, access_token)."""
    payload = {"name": "Test Candidate", "email": "candidate@example.com", "password": "StrongPass1!"}
    await client.post("/api/auth/register", json=payload)
    login = await client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login.json()["data"]["access_token"]
    return payload["email"], payload["password"], token
