"""
Live smoke test — boots a real uvicorn server on a real TCP socket and drives
it with real HTTP requests (real Set-Cookie parsing, a real CORS preflight,
real header casing over the wire). This is a different, complementary check
from tests/test_auth.py, which runs in-process against the ASGI app directly
and never touches a socket. Uses mongomock-motor so no real MongoDB is needed.

Run from backend/: python3 scripts/smoke_test_live.py
"""

import os
import sys
import threading
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "smoke-test-secret-do-not-use-in-prod")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "careerai_smoke")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import httpx
import uvicorn
from mongomock_motor import AsyncMongoMockClient

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

HOST, PORT = "127.0.0.1", 8321
BASE_URL = f"http://{HOST}:{PORT}"
FRONTEND_ORIGIN = "http://localhost:5173"

PASS, FAIL = "\033[92mPASS\033[0m", "\033[91mFAIL\033[0m"
results = []


def check(label, condition, detail=""):
    results.append(condition)
    print(f"  [{PASS if condition else FAIL}] {label}" + (f" — {detail}" if detail and not condition else ""))


def main():
    from app.api.deps import get_db
    from app.main import app

    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["careerai_smoke"]
    app.dependency_overrides[get_db] = lambda: mock_db

    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning", lifespan="off")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    else:
        print("Server did not start in time")
        sys.exit(1)

    try:
        client = httpx.Client(base_url=BASE_URL, timeout=5.0)

        print("\n1. Health check")
        r = client.get("/api/health")
        check("GET /api/health -> 200", r.status_code == 200, r.text)

        print("\n2. CORS preflight (simulating the real frontend origin)")
        r = client.options(
            "/api/auth/login",
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        allow_origin = r.headers.get("access-control-allow-origin")
        allow_creds = r.headers.get("access-control-allow-credentials")
        check("OPTIONS preflight -> 200", r.status_code == 200, f"got {r.status_code}")
        check("Access-Control-Allow-Origin echoes frontend origin", allow_origin == FRONTEND_ORIGIN, f"got {allow_origin!r}")
        check("Access-Control-Allow-Credentials: true", allow_creds == "true", f"got {allow_creds!r}")

        print("\n3. Register over real HTTP")
        r = client.post(
            "/api/auth/register",
            json={"name": "Smoke Test", "email": "smoke@example.com", "password": "StrongPass1!"},
            headers={"Origin": FRONTEND_ORIGIN},
        )
        check("POST /api/auth/register -> 201", r.status_code == 201, r.text)

        print("\n4. Login — verify the real Set-Cookie header, not just the JSON body")
        r = client.post(
            "/api/auth/login",
            json={"email": "smoke@example.com", "password": "StrongPass1!"},
            headers={"Origin": FRONTEND_ORIGIN},
        )
        check("POST /api/auth/login -> 200", r.status_code == 200, r.text)
        set_cookie = r.headers.get("set-cookie", "")
        check("Set-Cookie present", "careerai_refresh_token=" in set_cookie)
        check("Cookie is HttpOnly", "httponly" in set_cookie.lower(), set_cookie)
        check("Cookie is SameSite=Lax", "samesite=lax" in set_cookie.lower(), set_cookie)
        check("Cookie NOT Secure (dev mode, plain HTTP)", "secure" not in set_cookie.lower().replace("httponly", ""), set_cookie)
        access_token = r.json()["data"]["access_token"]

        print("\n5. Authenticated request with the real Authorization header")
        r = client.get("/api/profile/me", headers={"Authorization": f"Bearer {access_token}"})
        check("GET /api/profile/me -> 200", r.status_code == 200, r.text)
        check("Returned email matches", r.json()["data"]["email"] == "smoke@example.com")

        print("\n6. Refresh using the real cookie jar (httpx tracks Set-Cookie automatically)")
        r = client.post("/api/auth/refresh")
        check("POST /api/auth/refresh -> 200 using cookie jar", r.status_code == 200, r.text)

        print("\n7. Unauthenticated request correctly rejected")
        r = client.get("/api/profile/me")
        check("GET /api/profile/me without token -> 401", r.status_code == 401, r.text)

    finally:
        server.should_exit = True
        thread.join(timeout=5)

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
