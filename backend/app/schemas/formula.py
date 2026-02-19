from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormulaIngredient:
    name: str
    weight: Optional[float] = None


@dataclass
class FormulaAnalyzeOptions:
    top_n: int = 5


@dataclass
class FormulaAnalyzeRequest:
    formula_name: str
    ingredients: list[FormulaIngredient] = field(default_factory=list)
    options: Optional[FormulaAnalyzeOptions] = None


@dataclass
class FormulaComponentScore:
    ingredient_name: str
    total_score: int
    resolved: bool


@dataclass
class FormulaAnalyzeResponse:
    total_score: int
    component_scores: list[FormulaComponentScore] = field(default_factory=list)
    synergy_bonus: int = 0
    unresolved_ingredients: list[str] = field(default_factory=list)
