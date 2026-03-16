from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models.formula import FormulaComponent, FormulaResult
from ..schemas.formula import (
    FormulaAnalyzeRequest,
    FormulaAnalyzeResponse,
    FormulaComponentScore,
)


def _persist_formula_result(
    db: Session,
    request: FormulaAnalyzeRequest,
    component_scores: list[FormulaComponentScore],
    total_score: int,
) -> None:
    calc_id = uuid.uuid4()
    result = FormulaResult(
        calc_id=calc_id,
        formula_name=request.formula_name,
        total_score=total_score,
    )
    db.add(result)

    for ingredient, score in zip(request.ingredients, component_scores):
        raw_name = ingredient.name.strip()
        component = FormulaComponent(
            calc_id=calc_id,
            ingredient_name=raw_name,
            resolved_compound_name=score.ingredient_name if score.resolved else None,
            resolved_smiles=None,
            weight=ingredient.weight if ingredient.weight is not None else 1.0,
            resolved_source="db" if score.resolved else "unresolved",
        )
        db.add(component)

    try:
        db.commit()
    except Exception:
        db.rollback()


def analyze_formula(
    request: FormulaAnalyzeRequest,
    db: Session | None = None,
) -> FormulaAnalyzeResponse:
    if not request.ingredients:
        raise ValueError("EMPTY_INGREDIENTS")
    if len(request.ingredients) > 50:
        raise ValueError("TOO_MANY_INGREDIENTS")

    component_scores: list[FormulaComponentScore] = []
    unresolved_ingredients: list[str] = []

    for ingredient in request.ingredients:
        name = ingredient.name.strip()
        resolved = len(name) > 0
        total_score = 60 if resolved else 0
        component_scores.append(
            FormulaComponentScore(
                ingredient_name=name,
                total_score=total_score,
                resolved=resolved,
            )
        )
        if not resolved:
            unresolved_ingredients.append(name)

    synergy_bonus = min(2 * len(component_scores), 10)
    total_score = sum(item.total_score for item in component_scores) + synergy_bonus

    if component_scores and len(unresolved_ingredients) == len(component_scores):
        raise ValueError("ALL_UNRESOLVED")

    if db is not None:
        _persist_formula_result(
            db=db,
            request=request,
            component_scores=component_scores,
            total_score=total_score,
        )

    return FormulaAnalyzeResponse(
        total_score=total_score,
        component_scores=component_scores,
        synergy_bonus=synergy_bonus,
        unresolved_ingredients=unresolved_ingredients,
    )
