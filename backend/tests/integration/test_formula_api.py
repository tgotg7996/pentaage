from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_formulas_analyze_success() -> None:
    response = client.post(
        "/api/v1/formulas/analyze",
        json={
            "formula_name": "demo",
            "ingredients": [{"name": "Resveratrol"}, {"name": "Quercetin"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["data"] is not None
    assert payload["data"]["component_scores"][0]["ingredient_name"] == "Resveratrol"
    assert payload["data"]["component_scores"][1]["ingredient_name"] == "Quercetin"
    assert payload["data"]["component_scores"][0]["total_score"] == 60
    assert payload["data"]["component_scores"][1]["total_score"] == 60
    assert payload["data"]["synergy_bonus"] == 5
    assert payload["data"]["total_score"] == 125


def test_formulas_analyze_unresolved_ingredient() -> None:
    response = client.post(
        "/api/v1/formulas/analyze",
        json={
            "formula_name": "demo",
            "ingredients": [{"name": " "}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is not None
    assert payload["data"]["component_scores"][0]["resolved"] is False
    assert payload["data"]["component_scores"][0]["total_score"] == 0
    assert len(payload["data"]["unresolved_ingredients"]) == 1
    assert payload["data"]["total_score"] == 0
