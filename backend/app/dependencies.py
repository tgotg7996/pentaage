from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _get_session_factory() -> sessionmaker[Session] | None:
    global _engine, _session_factory
    if _session_factory is not None:
        return _session_factory

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None

    _engine = create_engine(database_url, pool_pre_ping=True)
    _session_factory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _session_factory


def get_db() -> Generator[Session | None, None, None]:
    session_factory = _get_session_factory()
    if session_factory is None:
        yield None
        return

    db = session_factory()
    try:
        yield db
    finally:
        db.close()
