from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("url", "params"),
    [
        ("/api/v1/products", None),
        ("/api/v1/warehouses", None),
        ("/api/v1/stocks", {"page": 1, "page_size": 20}),
        ("/api/v1/movements", {"page": 1, "page_size": 20}),
    ],
)
async def test_catalog_and_movements_endpoints_return_success_collections(
    client, url: str, params: dict[str, int] | None
) -> None:
    response = await client.get(url, params=params)

    assert response.status_code == 200
    body = response.json()
    if params is None:
        assert isinstance(body, list)
    else:
        assert set(body.keys()) == {"items", "total", "page", "page_size"}
        assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_get_stock_by_pair_returns_not_found_for_missing_pair(client) -> None:
    response = await client.get("/api/v1/stocks/999999/999999")

    assert response.status_code == 404
    assert "detail" in response.json()
