from pathlib import Path
import importlib
import sys
import time
from collections.abc import Generator
from typing import Optional
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.exc import IntegrityError
from app.dependencies import get_db
from app.main import app
from app.services.compound_service import reset_compound_cache


def _create_test_client():
    module = importlib.import_module("fastapi.testclient")
    test_client_cls = getattr(module, "TestClient")
    return test_client_cls(app)


client = _create_test_client()


class _QueryStub:
    def __init__(self, session: "_DbSessionStub") -> None:
        self._session: _DbSessionStub = session
        self._calc_id: Optional[UUID] = None

    def filter(self, *_args: object, **_kwargs: object) -> "_QueryStub":
        if _args:
            criterion = _args[0]
            right = getattr(criterion, "right", None)
            value = getattr(right, "value", None)
            if isinstance(value, UUID):
                self._calc_id = value
        return self

    def first(self) -> Optional[object]:
        if self._calc_id is None:
            return None
        return object() if self._calc_id in self._session.persisted_calc_ids else None


class _DbSessionStub:
    def __init__(self, fail_next_commit: bool = False) -> None:
        self.persisted_calc_ids: set[UUID] = set()
        self.pending_calc_id: Optional[UUID] = None
        self.fail_next_commit: bool = fail_next_commit
        self.commit_count: int = 0
        self.rollback_count: int = 0

    def query(self, *_args: object, **_kwargs: object) -> _QueryStub:
        return _QueryStub(self)

    def add(self, _obj: object) -> None:
        calc_id = getattr(_obj, "calc_id", None)
        if isinstance(calc_id, UUID):
            self.pending_calc_id = calc_id

    def commit(self) -> None:
        if self.fail_next_commit:
            self.fail_next_commit = False
            raise IntegrityError("insert", None, Exception("duplicate calc_id"))
        if self.pending_calc_id is not None:
            self.persisted_calc_ids.add(self.pending_calc_id)
            self.pending_calc_id = None
        self.commit_count += 1

    def rollback(self) -> None:
        self.pending_calc_id = None
        self.rollback_count += 1


def setup_function() -> None:
    reset_compound_cache()
    app.dependency_overrides.clear()


def test_compounds_analyze_success() -> None:
    response = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is not None
    assert payload["error"] is None
    assert payload["data"]["canonical_smiles"] == "CCO"
    assert len(payload["data"]["top_similarities"]) <= 3


def test_compounds_analyze_invalid_smiles() -> None:
    response = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "   ",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] is not None
    assert payload["error"]["code"] == "INVALID_SMILES"


def test_compounds_analyze_cached_response_stability() -> None:
    first = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )
    second = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["success"] is True
    assert first_payload["data"] is not None
    assert first_payload["data"]["cached"] is False
    assert second_payload["success"] is True
    assert second_payload["data"] is not None
    assert second_payload["data"]["cached"] is True
    assert second_payload["data"]["calc_id"] == first_payload["data"]["calc_id"]


def test_compounds_analyze_cache_key_isolated_by_options() -> None:
    first = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3, "radius": 2, "n_bits": 2048},
        },
    )
    second = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3, "radius": 2, "n_bits": 2048},
        },
    )
    third = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3, "radius": 3, "n_bits": 2048},
        },
    )

    first_payload = first.json()
    second_payload = second.json()
    third_payload = third.json()
    assert first_payload["success"] is True
    assert second_payload["success"] is True
    assert third_payload["success"] is True
    assert first_payload["data"]["cached"] is False
    assert second_payload["data"]["cached"] is True
    assert third_payload["data"]["cached"] is False
    assert first_payload["data"]["calc_id"] == second_payload["data"]["calc_id"]
    assert third_payload["data"]["calc_id"] != first_payload["data"]["calc_id"]


def test_compounds_analyze_single_request_within_slo() -> None:
    started_at = time.perf_counter()
    response = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )
    elapsed_seconds = time.perf_counter() - started_at

    assert response.status_code == 200
    assert elapsed_seconds < 3.0


def test_compounds_analyze_cached_result_persists_when_db_attached_later() -> None:
    db = _DbSessionStub()

    warmup = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    def _override_db() -> Generator[_DbSessionStub, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    cached = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    warmup_payload = warmup.json()
    cached_payload = cached.json()
    assert warmup_payload["success"] is True
    assert warmup_payload["data"] is not None
    assert warmup_payload["data"]["cached"] is False
    assert cached_payload["success"] is True
    assert cached_payload["data"] is not None
    assert cached_payload["data"]["cached"] is True
    assert cached_payload["data"]["calc_id"] == warmup_payload["data"]["calc_id"]
    assert UUID(cached_payload["data"]["calc_id"]) in db.persisted_calc_ids
    assert db.commit_count == 1


def test_compounds_analyze_cached_result_does_not_duplicate_persistence() -> None:
    db = _DbSessionStub()

    def _override_db() -> Generator[_DbSessionStub, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    first = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )
    second = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["success"] is True
    assert second_payload["success"] is True
    assert second_payload["data"] is not None
    assert second_payload["data"]["cached"] is True
    assert len(db.persisted_calc_ids) == 1
    assert db.commit_count == 1


def test_compounds_analyze_recovers_from_duplicate_commit_conflict() -> None:
    db = _DbSessionStub(fail_next_commit=True)

    def _override_db() -> Generator[_DbSessionStub, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    first = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )
    second = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["success"] is True
    assert first_payload["data"] is not None
    assert first_payload["data"]["cached"] is False
    assert second_payload["success"] is True
    assert second_payload["data"] is not None
    assert second_payload["data"]["cached"] is True
    assert first_payload["data"]["calc_id"] == second_payload["data"]["calc_id"]
    assert db.rollback_count == 1
    assert db.commit_count == 1
    assert len(db.persisted_calc_ids) == 1
