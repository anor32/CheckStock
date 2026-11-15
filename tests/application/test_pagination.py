from __future__ import annotations

import pytest

from src.application.pagination import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Pagination


@pytest.mark.parametrize(
    ("page", "page_size", "expected_page", "expected_page_size"),
    [
        (1, 20, 1, 20),
        (3, 50, 3, 50),
        (2, MAX_PAGE_SIZE, 2, MAX_PAGE_SIZE),
    ],
)
def test_pagination_happy_path(
    page: int, page_size: int, expected_page: int, expected_page_size: int
) -> None:
    pagination = Pagination(page=page, page_size=page_size)

    assert pagination.page == expected_page
    assert pagination.page_size == expected_page_size


@pytest.mark.parametrize(
    ("page", "page_size", "expected_page", "expected_page_size"),
    [
        (0, 20, DEFAULT_PAGE, 20),
        (-5, 10, DEFAULT_PAGE, 10),
        (1, 0, 1, DEFAULT_PAGE_SIZE),
        (1, -1, 1, DEFAULT_PAGE_SIZE),
        (0, 0, DEFAULT_PAGE, DEFAULT_PAGE_SIZE),
    ],
)
def test_pagination_normalizes_invalid_values_to_defaults(
    page: int, page_size: int, expected_page: int, expected_page_size: int
) -> None:
    pagination = Pagination(page=page, page_size=page_size)

    assert pagination.page == expected_page
    assert pagination.page_size == expected_page_size


@pytest.mark.parametrize(
    ("page_size", "expected_page_size"),
    [
        (MAX_PAGE_SIZE + 1, MAX_PAGE_SIZE),
        (500, MAX_PAGE_SIZE),
    ],
)
def test_pagination_clamps_excess_page_size(page_size: int, expected_page_size: int) -> None:
    pagination = Pagination(page=2, page_size=page_size)

    assert pagination.page == 2
    assert pagination.page_size == expected_page_size


def test_pagination_uses_defaults_when_data_absent() -> None:
    pagination = Pagination()

    assert pagination.page == DEFAULT_PAGE
    assert pagination.page_size == DEFAULT_PAGE_SIZE


@pytest.mark.parametrize(
    ("page", "page_size", "expected_offset", "expected_limit"),
    [
        (1, 20, 0, 20),
        (2, 20, 20, 20),
        (3, 10, 20, 10),
        (1, MAX_PAGE_SIZE, 0, MAX_PAGE_SIZE),
    ],
)
def test_pagination_offset_and_limit(
    page: int, page_size: int, expected_offset: int, expected_limit: int
) -> None:
    pagination = Pagination(page=page, page_size=page_size)

    assert pagination.offset == expected_offset
    assert pagination.limit == expected_limit
