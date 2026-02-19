from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any


def _legacy_fingerprint(smiles: str, radius: int, n_bits: int) -> list[int]:
    window = max(radius + 1, 1)
    bits: set[int] = set()

    if len(smiles) < window:
        bits.add(sum(ord(char) for char in smiles) % n_bits)
    else:
        for index in range(len(smiles) - window + 1):
            segment = smiles[index : index + window]
            bits.add(sum(ord(char) * (position + 1) for position, char in enumerate(segment)) % n_bits)

    return sorted(bits)


@lru_cache(maxsize=1)
def _load_rdkit_modules() -> tuple[Any | None, Any | None]:
    try:
        chem = importlib.import_module("rdkit.Chem")
        generator_module = importlib.import_module("rdkit.Chem.rdFingerprintGenerator")
        return chem, generator_module
    except ModuleNotFoundError:
        return None, None


@lru_cache(maxsize=8)
def _get_morgan_generator(radius: int, n_bits: int) -> Any | None:
    _, generator_module = _load_rdkit_modules()
    if generator_module is None:
        return None
    return generator_module.GetMorganGenerator(radius=radius, fpSize=n_bits)


def morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> list[int]:
    if not smiles or n_bits <= 0:
        return []

    normalized = smiles.strip()
    if not normalized:
        return []

    chem, _ = _load_rdkit_modules()
    if chem is None:
        return _legacy_fingerprint(normalized, radius=radius, n_bits=n_bits)

    mol = chem.MolFromSmiles(normalized)
    if mol is None:
        return []

    generator = _get_morgan_generator(radius=radius, n_bits=n_bits)
    if generator is None:
        return _legacy_fingerprint(normalized, radius=radius, n_bits=n_bits)

    fingerprint = generator.GetFingerprint(mol)
    return sorted(int(bit) for bit in fingerprint.GetOnBits())
