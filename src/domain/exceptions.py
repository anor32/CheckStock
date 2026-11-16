from __future__ import annotations

from typing import Any

from src.domain.value_objects.insufficient_stock import InsufficientStockInfo


class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class CheckStockDomainError(AppError):
    """Базовая доменная ошибка CheckStock."""


class EntityNotFoundError(CheckStockDomainError):
    """Сущность не найдена."""


class ProductNotFoundError(EntityNotFoundError):
    """Товар/SKU не найден."""


class StockNotFoundError(ProductNotFoundError):
    """Остаток/SKU не найден."""


class InsufficientStockError(CheckStockDomainError):
    """Недостаточно остатка для операции."""

    def __init__(
        self,
        message: str = "",
        data: dict[str, Any] | None = None,
        info: InsufficientStockInfo | None = None,
    ) -> None:
        resolved_message = message or (info.detail if info is not None else "")
        resolved_data = (
            data if data is not None else (info.to_error_data() if info is not None else None)
        )
        super().__init__(resolved_message, resolved_data)
        self.info = info
        self.data = resolved_data


class InvalidMovementError(CheckStockDomainError):
    """Движение имеет некорректное состояние (например, qty <= 0)."""


class DuplicateIdempotencyKeyError(CheckStockDomainError):
    """Дублирующийся запрос с тем же ключом идемпотентности."""


class WarehouseDeletedError(CheckStockDomainError):
    """Операция запрещена для удалённого склада."""


class ProductAlreadyExistsError(CheckStockDomainError):
    """Товар с таким SKU уже существует."""
