"""init

Revision ID: 19ad6358a9df
Revises:
Create Date: 2026-11-12 16:09:50.611697

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "19ad6358a9df"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)

    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("qty_physical", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qty_reserved_fbs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "qty_reserved_fbs <= qty_physical", name="ck_stock_reserved_le_physical"
        ),
        sa.CheckConstraint("qty_physical >= 0", name="ck_stock_physical_non_negative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "warehouse_id", name="uq_stock_product_warehouse"),
    )
    op.create_index("ix_stock_warehouse_id", "stocks", ["warehouse_id"], unique=False)

    op.create_table(
        "movements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("from_warehouse_id", sa.Integer(), nullable=True),
        sa.Column("to_warehouse_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_movements_idempotency_key"), "movements", ["idempotency_key"], unique=True
    )
    op.create_index(
        "ix_movement_product_created",
        "movements",
        ["product_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_movement_status_created",
        "movements",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index("ix_movement_type", "movements", ["type"], unique=False)
    op.create_index("ix_movement_from_warehouse", "movements", ["from_warehouse_id"], unique=False)
    op.create_index("ix_movement_to_warehouse", "movements", ["to_warehouse_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_movement_to_warehouse", table_name="movements")
    op.drop_index("ix_movement_from_warehouse", table_name="movements")
    op.drop_index("ix_movement_type", table_name="movements")
    op.drop_index("ix_movement_status_created", table_name="movements")
    op.drop_index("ix_movement_product_created", table_name="movements")
    op.drop_index(op.f("ix_movements_idempotency_key"), table_name="movements")
    op.drop_table("movements")
    op.drop_index("ix_stock_warehouse_id", table_name="stocks")
    op.drop_table("stocks")
    op.drop_table("warehouses")
    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_table("products")
