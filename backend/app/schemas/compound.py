from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class AnalyzeOptions:
    radius: int = 2
    n_bits: int = 2048
    use_features: bool = False
    top_n: int = 5


@dataclass
class CompoundAnalyzeRequest:
    input_type: Literal["smiles", "name", "cas", "mol"]
    input_value: str
    options: Optional[AnalyzeOptions] = None


@dataclass
class SimilarityResult:
    reference_name: str
    reference_cas: str
    similarity: float
    rank: int


@dataclass
class CompoundAnalyzeResponse:
    compound_name: Optional[str]
    canonical_smiles: str
    total_score: int
    base_score: float
    composite_score: float
    top_similarities: list[SimilarityResult] = field(default_factory=list)
    algorithm_version: str = ""
    fingerprint_params: dict[str, object] = field(default_factory=dict)
    cached: bool = False
    calc_id: str = ""
