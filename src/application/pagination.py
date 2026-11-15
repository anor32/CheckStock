"""Pagination value object for application layer."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Pagination:
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        page = self.page if self.page >= 1 else DEFAULT_PAGE
        page_size = DEFAULT_PAGE_SIZE if self.page_size < 1 else min(self.page_size, MAX_PAGE_SIZE)
        object.__setattr__(self, "page", page)
        object.__setattr__(self, "page_size", page_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
