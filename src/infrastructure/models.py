"""SQLAlchemy ORM models for CheckStock (TASK_04)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    desc,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.domain.entities import (
    Movement,
    MovementStatus,
    MovementType,
    Product,
    Stock,
    Warehouse,
)


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""


class ProductModel(Base):
    """ORM model for Product."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @classmethod
    def from_entity(cls, product: Product) -> ProductModel:
        return cls(
            sku=product.sku,
            name=product.name,
        )

    def to_entity(self) -> Product:
        return Product(
            id=self.id,
            sku=self.sku,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class WarehouseModel(Base):
    """ORM model for Warehouse (soft-delete)."""

    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @classmethod
    def from_entity(cls, warehouse: Warehouse) -> WarehouseModel:
        return cls(
            name=warehouse.name,
            is_deleted=warehouse.is_deleted,
            deleted_at=warehouse.deleted_at,
        )

    def to_entity(self) -> Warehouse:
        return Warehouse(
            id=self.id,
            name=self.name,
            is_deleted=self.is_deleted,
            deleted_at=self.deleted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class StockModel(Base):
    """ORM model for Stock (product/warehouse pair)."""

    __tablename__ = "stocks"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_stock_product_warehouse"),
        CheckConstraint("qty_reserved_fbs <= qty_physical", name="ck_stock_reserved_le_physical"),
        CheckConstraint("qty_physical >= 0", name="ck_stock_physical_non_negative"),
        Index("ix_stock_warehouse_id", "warehouse_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    qty_physical: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qty_reserved_fbs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def qty_available(self) -> int:
        return self.qty_physical - self.qty_reserved_fbs

    @classmethod
    def from_create_dto(cls, data: Any) -> StockModel:
        return cls(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            qty_physical=data.qty_physical,
            qty_reserved_fbs=data.qty_reserved_fbs,
        )

    def to_entity(self) -> Stock:
        return Stock(
            id=self.id,
            product_id=self.product_id,
            warehouse_id=self.warehouse_id,
            qty_physical=self.qty_physical,
            qty_reserved_fbs=self.qty_reserved_fbs,
            updated_at=self.updated_at,
        )


class MovementModel(Base):
    """ORM model for Movement journal."""

    __tablename__ = "movements"
    __table_args__ = (
        Index("ix_movement_product_created", "product_id", desc("created_at")),
        Index("ix_movement_status_created", "status", desc("created_at")),
        Index("ix_movement_type", "type"),
        Index("ix_movement_from_warehouse", "from_warehouse_id"),
        Index("ix_movement_to_warehouse", "to_warehouse_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    from_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id"), nullable=True
    )
    to_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_entity(self) -> Movement:
        return Movement(
            id=self.id,
            product_id=self.product_id,
            type=MovementType(self.type),
            qty=self.qty,
            from_warehouse_id=self.from_warehouse_id,
            to_warehouse_id=self.to_warehouse_id,
            status=MovementStatus(self.status),
            idempotency_key=self.idempotency_key,
            created_at=self.created_at,
            completed_at=self.completed_at,
        )
