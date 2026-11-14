from typing import Any


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


class InvalidMovementError(CheckStockDomainError):
    """Движение имеет некорректное состояние (например, qty <= 0)."""


class DuplicateIdempotencyKeyError(CheckStockDomainError):
    """Дублирующийся запрос с тем же ключом идемпотентности."""


class WarehouseDeletedError(CheckStockDomainError):
    """Операция запрещена для удалённого склада."""


class ProductAlreadyExistsError(CheckStockDomainError):
    """Товар с таким SKU уже существует."""
