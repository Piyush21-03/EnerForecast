import logging

from fastapi.testclient import TestClient

from app.core.logging import setup_logging
from app.main import create_app


def test_app_creates_and_serves_openapi():
    client = TestClient(create_app())
    assert client.get("/openapi.json").status_code == 200


def test_cors_allows_configured_origin():
    client = TestClient(create_app())
    r = client.options(
        "/openapi.json",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_setup_logging_is_idempotent():
    setup_logging("WARNING")
    setup_logging("INFO")
    assert logging.getLogger().level == logging.INFO
    assert len(logging.getLogger().handlers) == 1
