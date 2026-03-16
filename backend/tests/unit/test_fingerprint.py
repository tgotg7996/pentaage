import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.fingerprint import morgan_fingerprint


def test_morgan_fingerprint_empty_input_returns_empty_list() -> None:
    assert morgan_fingerprint("") == []


def test_morgan_fingerprint_whitespace_input_returns_empty_list() -> None:
    assert morgan_fingerprint("   ") == []


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


def test_morgan_fingerprint_uses_rdkit_generator_when_available() -> None:
    class _FakeFingerprint:
        def GetOnBits(self) -> list[int]:
            return [9, 2, 5]

    class _FakeGenerator:
        def GetFingerprint(self, _mol: object) -> _FakeFingerprint:
            return _FakeFingerprint()

    fake_chem = SimpleNamespace(MolFromSmiles=lambda _smiles: object())
    with patch("app.core.fingerprint._load_rdkit_modules", return_value=(fake_chem, object())), patch(
        "app.core.fingerprint._get_morgan_generator", return_value=_FakeGenerator()
    ):
        bits = morgan_fingerprint("CCO", radius=2, n_bits=128)

    assert bits == [2, 5, 9]


def test_morgan_fingerprint_falls_back_when_generator_unavailable() -> None:
    fake_chem = SimpleNamespace(MolFromSmiles=lambda _smiles: object())
    with patch("app.core.fingerprint._load_rdkit_modules", return_value=(fake_chem, object())), patch(
        "app.core.fingerprint._get_morgan_generator", return_value=None
    ):
        bits = morgan_fingerprint("CCO", radius=2, n_bits=64)

    assert bits
    assert all(0 <= bit < 64 for bit in bits)


def test_morgan_fingerprint_falls_back_when_rdkit_unavailable() -> None:
    with patch("app.core.fingerprint._load_rdkit_modules", return_value=(None, None)):
        bits = morgan_fingerprint("C", radius=2, n_bits=64)

    assert len(bits) == 1


def test_get_morgan_generator_returns_none_without_generator_module() -> None:
    with patch("app.core.fingerprint._load_rdkit_modules", return_value=(object(), None)):
        from app.core.fingerprint import _get_morgan_generator

        _get_morgan_generator.cache_clear()
        generator = _get_morgan_generator(radius=2, n_bits=128)

    assert generator is None


def test_load_rdkit_modules_returns_none_tuple_on_missing_module() -> None:
    from app.core.fingerprint import _load_rdkit_modules

    _load_rdkit_modules.cache_clear()
    with patch("app.core.fingerprint.importlib.import_module", side_effect=ModuleNotFoundError):
        chem, generator_module = _load_rdkit_modules()

    assert chem is None
    assert generator_module is None
