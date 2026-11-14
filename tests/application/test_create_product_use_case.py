from __future__ import annotations

import pytest

from src.application.usecases.products.create_product import CreateProductUseCase
from src.domain.exceptions import ProductAlreadyExistsError


@pytest.mark.asyncio
async def test_create_product_returns_created_dto(
    mock_uow, created_product, create_product_input
) -> None:
    mock_uow.sku_repo.add.return_value = created_product
    use_case = CreateProductUseCase(uow=mock_uow)

    result = await use_case.execute(create_product_input)

    assert result.id == created_product.id
    assert result.sku == created_product.sku
    assert result.name == created_product.name
    mock_uow.sku_repo.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_product_raises_when_sku_already_exists(
    mock_uow, create_product_duplicate_input
) -> None:
    mock_uow.sku_repo.add.side_effect = ProductAlreadyExistsError(
        "Product with this SKU already exists"
    )
    use_case = CreateProductUseCase(uow=mock_uow)

    with pytest.raises(ProductAlreadyExistsError) as exc:
        await use_case.execute(create_product_duplicate_input)

    assert str(exc.value) == "Product with this SKU already exists"
    mock_uow.sku_repo.add.assert_awaited_once()
