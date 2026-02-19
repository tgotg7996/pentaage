import importlib.util
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.fingerprint import morgan_fingerprint


def test_morgan_fingerprint_empty_input_returns_empty_list() -> None:
    assert morgan_fingerprint("") == []


def test_morgan_fingerprint_non_positive_nbits_returns_empty_list() -> None:
    assert morgan_fingerprint("CCO", n_bits=0) == []


def test_morgan_fingerprint_is_deterministic() -> None:
    first = morgan_fingerprint("CCO", radius=2, n_bits=128)
    second = morgan_fingerprint("CCO", radius=2, n_bits=128)
    assert first == second


def test_morgan_fingerprint_values_within_nbits_range() -> None:
    bits = morgan_fingerprint("C1=CC=CC=C1", radius=2, n_bits=256)
    assert bits
    assert all(0 <= bit < 256 for bit in bits)


def test_morgan_fingerprint_short_smiles_still_returns_single_bit() -> None:
    bits = morgan_fingerprint("C", radius=2, n_bits=64)
    assert len(bits) == 1


def test_morgan_fingerprint_invalid_smiles_returns_empty_when_rdkit_available() -> None:
    try:
        has_rdkit = importlib.util.find_spec("rdkit.Chem") is not None
    except ModuleNotFoundError:
        has_rdkit = False
    if not has_rdkit:
        return
    assert morgan_fingerprint("C1CC", radius=2, n_bits=128) == []
