from pathlib import Path
import importlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.main import app


def _create_test_client():
    module = importlib.import_module("fastapi.testclient")
    test_client_cls = getattr(module, "TestClient")
    return test_client_cls(app)


client = _create_test_client()


def test_health_success() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["components"]["db"] == "healthy"
    assert payload["components"]["redis"] == "healthy"
    assert payload["components"]["rdkit"] == "healthy"
