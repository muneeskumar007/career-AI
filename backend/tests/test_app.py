async def test_health_check(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_openapi_schema_generates(client):
    # Catches schema-generation regressions (e.g. from Generic response models)
    # that only surface when FastAPI builds the OpenAPI document.
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "/api/auth/login" in schema["paths"]
    assert "/api/users" in schema["paths"]
