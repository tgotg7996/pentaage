from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.scoring import total_score


def test_total_score_uses_60_40_weight_formula() -> None:
    assert total_score(max_similarity=0.8, top3_avg_similarity=0.5) == 68


def test_total_score_clamps_to_100() -> None:
    assert total_score(max_similarity=1.0, top3_avg_similarity=1.0) == 100


def test_total_score_allows_zero_floor() -> None:
    assert total_score(max_similarity=0.0, top3_avg_similarity=0.0) == 0
