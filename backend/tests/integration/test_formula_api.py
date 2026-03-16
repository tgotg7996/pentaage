from pathlib import Path
import importlib
import sys
from collections.abc import Generator
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dependencies import get_db
from app.main import app


def _create_test_client():
    module = importlib.import_module("fastapi.testclient")
    test_client_cls = getattr(module, "TestClient")
    return test_client_cls(app)


client = _create_test_client()


class _DbSessionStub:
    def __init__(self) -> None:
        self.formula_results: list[object] = []
        self.formula_components: list[object] = []
        self.commit_count: int = 0
        self.rollback_count: int = 0

    def add(self, obj: object) -> None:
        name = obj.__class__.__name__
        if name == "FormulaResult":
            self.formula_results.append(obj)
        elif name == "FormulaComponent":
            self.formula_components.append(obj)

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def setup_function() -> None:
    app.dependency_overrides.clear()


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
    assert payload["data"]["synergy_bonus"] == 4
    assert payload["data"]["total_score"] == 124


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
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] is not None
    assert payload["error"]["code"] == "ALL_UNRESOLVED"


def test_formulas_analyze_empty_ingredients() -> None:
    response = client.post(
        "/api/v1/formulas/analyze",
        json={
            "formula_name": "demo",
            "ingredients": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] is not None
    assert payload["error"]["code"] == "EMPTY_INGREDIENTS"


def test_formulas_analyze_too_many_ingredients() -> None:
    ingredients = [{"name": f"ingredient-{idx}"} for idx in range(51)]
    response = client.post(
        "/api/v1/formulas/analyze",
        json={
            "formula_name": "demo",
            "ingredients": ingredients,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] is not None
    assert payload["error"]["code"] == "TOO_MANY_INGREDIENTS"


def test_formulas_analyze_persists_formula_result_and_components() -> None:
    db = _DbSessionStub()

    def _override_db() -> Generator[Optional[_DbSessionStub], None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    response = client.post(
        "/api/v1/formulas/analyze",
        json={
            "formula_name": "demo",
            "ingredients": [{"name": "Resveratrol", "weight": 1.2}, {"name": "Quercetin"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(db.formula_results) == 1
    assert len(db.formula_components) == 2
    assert db.commit_count == 1
    assert db.rollback_count == 0

    first_component = db.formula_components[0]
    assert getattr(first_component, "ingredient_name", "") == "Resveratrol"
    assert getattr(first_component, "weight", 0.0) == 1.2
