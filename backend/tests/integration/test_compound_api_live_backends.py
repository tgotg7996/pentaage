from __future__ import annotations

from pathlib import Path
import importlib
import os
import socket
import sys
from unittest import SkipTest
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.main import app
from app.models.compound import CompoundResult
from app.services import compound_service


def _create_test_client():
    module = importlib.import_module("fastapi.testclient")
    test_client_cls = getattr(module, "TestClient")
    return test_client_cls(app)


client = _create_test_client()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SkipTest(f"{name} is required for live backend integration test")
    return value


def _require_service_reachable(url: str, default_port: int, service_name: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or default_port

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(1.5)
    try:
        if probe.connect_ex((host, port)) != 0:
            raise SkipTest(f"{service_name} is not reachable at {host}:{port}")
    finally:
        probe.close()


def _reset_db_factory() -> None:
    from app import dependencies

    dependencies._engine = None
    dependencies._session_factory = None


def _ensure_compound_result_table(database_url: str) -> None:
    if not database_url:
        return
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
    except ModuleNotFoundError as exc:
        raise SkipTest(f"DB driver module missing for DATABASE_URL: {exc}") from exc
    try:
        from app.models.base import Base

        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()


def _make_session_factory(database_url: str) -> sessionmaker[Session]:
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
    except ModuleNotFoundError as exc:
        raise SkipTest(f"DB driver module missing for DATABASE_URL: {exc}") from exc
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _clear_compound_results(database_url: str) -> None:
    if not database_url:
        return
    session_factory = _make_session_factory(database_url)
    db = session_factory()
    try:
        db.execute(text("DELETE FROM compound_results"))
        db.commit()
    finally:
        db.close()


def _clear_redis_prefix(redis_url: str, prefix: str = "compound-cache:") -> None:
    redis_module = importlib.import_module("redis")
    client = redis_module.from_url(redis_url, decode_responses=True)
    keys = client.keys(f"{prefix}*")
    if keys:
        client.delete(*keys)


def _setup_live_backends() -> tuple[str, str]:
    database_url = _require_env("DATABASE_URL")
    redis_url = _require_env("REDIS_URL")
    _require_service_reachable(database_url, default_port=5432, service_name="PostgreSQL")
    _require_service_reachable(redis_url, default_port=6379, service_name="Redis")
    _ensure_compound_result_table(database_url)
    _clear_compound_results(database_url)
    _clear_redis_prefix(redis_url)
    _reset_db_factory()
    app.dependency_overrides.clear()
    return database_url, redis_url


def _teardown_live_backends(database_url: str, redis_url: str) -> None:
    _clear_compound_results(database_url)
    _clear_redis_prefix(redis_url)
    _reset_db_factory()


def test_compounds_analyze_persists_to_real_db() -> None:
    database_url = _require_env("DATABASE_URL")
    _require_service_reachable(database_url, default_port=5432, service_name="PostgreSQL")
    _ensure_compound_result_table(database_url)
    _clear_compound_results(database_url)
    _reset_db_factory()
    app.dependency_overrides.clear()

    response = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"] is not None
    assert payload["data"]["cached"] is False
    calc_id = UUID(payload["data"]["calc_id"])

    session_factory = _make_session_factory(database_url)
    db = session_factory()
    try:
        row = db.query(CompoundResult).filter(CompoundResult.calc_id == calc_id).first()
        assert row is not None
        assert row.canonical_smiles == "CCO"
    finally:
        db.close()


def test_compounds_analyze_uses_live_redis_cache_and_keeps_single_persisted_row() -> None:
    database_url, redis_url = _setup_live_backends()

    previous_backend = os.getenv("COMPOUND_CACHE_BACKEND")
    previous_redis_url = os.getenv("REDIS_URL")
    os.environ["COMPOUND_CACHE_BACKEND"] = "redis"
    os.environ["REDIS_URL"] = redis_url
    compound_service.compound_cache = compound_service._create_compound_cache()

    try:
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
        assert first_payload["data"] is not None
        assert second_payload["data"] is not None
        assert first_payload["data"]["cached"] is False
        assert second_payload["data"]["cached"] is True
        assert first_payload["data"]["calc_id"] == second_payload["data"]["calc_id"]

        session_factory = _make_session_factory(database_url)
        db = session_factory()
        try:
            calc_id = UUID(first_payload["data"]["calc_id"])
            persisted = db.query(CompoundResult).filter(CompoundResult.calc_id == calc_id).all()
            assert len(persisted) == 1
        finally:
            db.close()

        redis_module = importlib.import_module("redis")
        redis_client = redis_module.from_url(redis_url, decode_responses=True)
        keys = redis_client.keys("compound-cache:fp:CCO:2:2048:0:3")
        assert len(keys) == 1
    finally:
        if previous_backend is None:
            os.environ.pop("COMPOUND_CACHE_BACKEND", None)
        else:
            os.environ["COMPOUND_CACHE_BACKEND"] = previous_backend
        if previous_redis_url is None:
            os.environ.pop("REDIS_URL", None)
        else:
            os.environ["REDIS_URL"] = previous_redis_url

    compound_service.compound_cache = compound_service._create_compound_cache()
    _teardown_live_backends(database_url, redis_url)
