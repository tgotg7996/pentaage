from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.similarity import tanimoto


def test_tanimoto_empty_sets_is_one() -> None:
    assert tanimoto([], []) == 1.0


def test_tanimoto_identical_sets_is_one() -> None:
    assert tanimoto([1, 2, 3], [1, 2, 3]) == 1.0


def test_tanimoto_disjoint_sets_is_zero() -> None:
    assert tanimoto([1, 2], [3, 4]) == 0.0


def test_tanimoto_partial_overlap() -> None:
    score = tanimoto([1, 2, 3], [2, 3, 4, 5])
    assert score == 2 / 5
