import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    import alembic

    op = getattr(alembic, "op")

    op.create_table(
        "reference_compounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name_cn", sa.String(length=128), nullable=False),
        sa.Column("name_en", sa.String(length=128), nullable=False),
        sa.Column("cas", sa.String(length=64), nullable=False),
        sa.Column("smiles", sa.Text(), nullable=False),
        sa.Column("canonical_smiles", sa.Text(), nullable=False),
        sa.Column("fingerprint_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reference_compounds_cas", "reference_compounds", ["cas"], unique=True)

    op.create_table(
        "compound_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_smiles", sa.Text(), nullable=False),
        sa.Column("canonical_smiles", sa.Text(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("base_score", sa.Float(), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), nullable=False),
        sa.Column("fingerprint_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cached", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compound_results_calc_id", "compound_results", ["calc_id"], unique=True)

    op.create_table(
        "formula_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("formula_name", sa.String(length=128), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_formula_results_calc_id", "formula_results", ["calc_id"], unique=True)

    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("result_file_url", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "batch_job_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=False),
        sa.Column("input_smiles", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["batch_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batch_job_items_job_id", "batch_job_items", ["job_id"], unique=False)

    op.create_table(
        "formula_components",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("calc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingredient_name", sa.String(length=128), nullable=False),
        sa.Column("resolved_compound_name", sa.String(length=128), nullable=True),
        sa.Column("resolved_smiles", sa.Text(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("resolved_source", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["calc_id"], ["formula_results.calc_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_formula_components_calc_id", "formula_components", ["calc_id"], unique=False)


def downgrade() -> None:
    import alembic

    op = getattr(alembic, "op")

    op.drop_index("ix_formula_components_calc_id", table_name="formula_components")
    op.drop_table("formula_components")

    op.drop_index("ix_batch_job_items_job_id", table_name="batch_job_items")
    op.drop_table("batch_job_items")

    op.drop_table("batch_jobs")

    op.drop_index("ix_formula_results_calc_id", table_name="formula_results")
    op.drop_table("formula_results")

    op.drop_index("ix_compound_results_calc_id", table_name="compound_results")
    op.drop_table("compound_results")

    op.drop_index("ix_reference_compounds_cas", table_name="reference_compounds")
    op.drop_table("reference_compounds")
