def formula_score(component_scores: list[int]) -> int:
    return int(sum(component_scores) / len(component_scores)) if component_scores else 0
