import uuid
from typing import Optional

from sqlalchemy import BigInteger, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class FormulaResult(Base, TimestampMixin):
    __tablename__ = "formula_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )
    formula_name: Mapped[str] = mapped_column(String(128), nullable=False)
    total_score: Mapped[int] = mapped_column(nullable=False)


class FormulaComponent(Base, TimestampMixin):
    __tablename__ = "formula_components"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    calc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("formula_results.calc_id", ondelete="CASCADE"), nullable=False
    )
    ingredient_name: Mapped[str] = mapped_column(String(128), nullable=False)
    resolved_compound_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resolved_smiles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    resolved_source: Mapped[str] = mapped_column(String(16), nullable=False, default="db")
