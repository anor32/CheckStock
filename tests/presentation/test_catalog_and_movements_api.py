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


@pytest.mark.asyncio
async def test_fbo_out_rejects_when_available_less_than_requested_due_to_fbs_reserve(
    client,
) -> None:
    product_resp = await client.post(
        "/api/v1/products",
        json={"sku": "SKU-FBO-1", "name": "Product FBO"},
    )
    assert product_resp.status_code == 201
    product_id = product_resp.json()["id"]

    warehouse_resp = await client.post(
        "/api/v1/warehouses",
        json={"name": "WH-FBO-1"},
    )
    assert warehouse_resp.status_code == 201
    warehouse_id = warehouse_resp.json()["id"]

    inbound_resp = await client.post(
        "/api/v1/movements/inbound",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "qty": 10,
            "idempotency_key": "inbound-fbo-1",
        },
    )
    assert inbound_resp.status_code == 201

    reserve_resp = await client.post(
        "/api/v1/movements/fbs-reserve",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "qty": 8,
            "idempotency_key": "reserve-fbo-1",
        },
    )
    assert reserve_resp.status_code == 201

    fbo_resp = await client.post(
        "/api/v1/movements/fbo-out",
        json={
            "product_id": product_id,
            "from_warehouse_id": warehouse_id,
            "qty": 3,
            "idempotency_key": "fbo-out-1",
        },
    )

    assert fbo_resp.status_code == 409
    body = fbo_resp.json()
    assert body.get("available") == 2
    assert body.get("requested") == 3
    assert "Недостаточно остатка" in body.get("detail", "")
