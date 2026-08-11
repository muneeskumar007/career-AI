"""
The main suite runs with generous rate limits (see conftest.py) so unrelated
tests sharing one client IP don't trip each other's limits. That means
production's real limits (RATE_LIMIT_REGISTER=3/minute etc.) are never
exercised by tests/test_auth.py. This file proves the *mechanism* works —
a fresh, isolated Limiter + route, independent of the app's shared settings
so it can use a strict limit without disturbing every other test.
"""

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


async def test_rate_limit_blocks_after_threshold():
    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.post("/ping")
    @limiter.limit("2/minute")
    async def ping(request: Request):
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.post("/ping")
        second = await ac.post("/ping")
        third = await ac.post("/ping")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
