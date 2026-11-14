"""add warehouse idempotency key

Revision ID: b7c1d2e3f4a5
Revises: 19ad6358a9df
Create Date: 2026-11-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c1d2e3f4a5"
down_revision: str | None = "19ad6358a9df"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "warehouses",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        op.f("ix_warehouses_idempotency_key"),
        "warehouses",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_warehouses_idempotency_key"), table_name="warehouses")
    op.drop_column("warehouses", "idempotency_key")
