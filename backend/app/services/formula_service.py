from __future__ import annotations

from ..schemas.formula import (
    FormulaAnalyzeRequest,
    FormulaAnalyzeResponse,
    FormulaComponentScore,
)


def analyze_formula(request: FormulaAnalyzeRequest) -> FormulaAnalyzeResponse:
    if not request.ingredients:
        raise ValueError("EMPTY_INGREDIENTS")

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

    synergy_bonus = max(len(component_scores) - 1, 0) * 5
    total_score = sum(item.total_score for item in component_scores) + synergy_bonus

    if component_scores and len(unresolved_ingredients) == len(component_scores):
        raise ValueError("ALL_UNRESOLVED")

    return FormulaAnalyzeResponse(
        total_score=total_score,
        component_scores=component_scores,
        synergy_bonus=synergy_bonus,
        unresolved_ingredients=unresolved_ingredients,
    )
