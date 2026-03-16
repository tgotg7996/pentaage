from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.schemas.formula import FormulaAnalyzeRequest, FormulaIngredient
from app.services.formula_service import analyze_formula


def test_formula_synergy_uses_two_per_component_capped_at_ten() -> None:
    request = FormulaAnalyzeRequest(
        formula_name="demo",
        ingredients=[FormulaIngredient(name=f"ing-{idx}") for idx in range(6)],
    )

    response = analyze_formula(request)
    assert response.synergy_bonus == 10
    assert response.total_score == 370


def test_formula_raises_when_too_many_ingredients() -> None:
    request = FormulaAnalyzeRequest(
        formula_name="demo",
        ingredients=[FormulaIngredient(name=f"ing-{idx}") for idx in range(51)],
    )

    try:
        analyze_formula(request)
    except ValueError as exc:
        assert str(exc) == "TOO_MANY_INGREDIENTS"
        return

    raise AssertionError("expected TOO_MANY_INGREDIENTS error")


def test_formula_raises_all_unresolved_when_every_name_blank() -> None:
    request = FormulaAnalyzeRequest(
        formula_name="demo",
        ingredients=[FormulaIngredient(name="  "), FormulaIngredient(name=" ")],
    )

    try:
        analyze_formula(request)
    except ValueError as exc:
        assert str(exc) == "ALL_UNRESOLVED"
        return

    raise AssertionError("expected ALL_UNRESOLVED error")
