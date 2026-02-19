import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ReferenceCompound(Base, TimestampMixin):
    __tablename__ = "reference_compounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_cn: Mapped[str] = mapped_column(String(128), nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    cas: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    smiles: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint_version: Mapped[str] = mapped_column(String(64), nullable=False)


class CompoundResult(Base, TimestampMixin):
    __tablename__ = "compound_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )
    input_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    total_score: Mapped[int] = mapped_column(nullable=False)
    base_score: Mapped[float] = mapped_column(Float, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    fingerprint_params: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    cached: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
