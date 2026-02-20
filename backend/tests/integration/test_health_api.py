from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_success() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["components"]["db"] == "healthy"
    assert payload["components"]["redis"] == "healthy"
    assert payload["components"]["rdkit"] == "healthy"
