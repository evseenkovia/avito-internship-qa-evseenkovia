import random
from typing import List

import pytest
from pydantic import TypeAdapter

from models.models import ItemRequest, ItemResponse


@pytest.mark.asyncio(loop_scope="session")
async def test_get_items_by_seller_id_full_check(api_client):
    import random

    seller_id = random.randint(200000, 300000)
    payload = ItemRequest(
        sellerId=seller_id,
        name="Товар продавца",
        price=1000,
        statistics={"likes": 1, "viewCount": 1, "contacts": 1},
    )

    await api_client.post("/api/1/item", json=payload.model_dump())
    payload.name = "Второй товар продавца"
    await api_client.post("/api/1/item", json=payload.model_dump())

    response = await api_client.get(f"/api/1/{seller_id}/item")
    assert response.status_code == 200

    data = response.json()
    adapter = TypeAdapter(List[ItemResponse])

    try:
        items = adapter.validate_python(data)
    except Exception as e:
        pytest.fail(f"Структура списка не соответствует ItemResponse. Ошибка: {e}")

    assert len(items) >= 2, f"Ожидали минимум 2 товара, получили {len(items)}"
    for item in items:
        assert item.sellerId == seller_id, (
            f"Найдено чужое объявление! SellerId: {item.sellerId}"
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_items_empty_seller(api_client):
    new_seller_id = random.randint(1000001, 1999999)

    response = await api_client.get(f"/api/1/{new_seller_id}/item")

    assert response.status_code == 200, (
        f"Ожидали 200 для пустого списка, получили {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Ответ должен быть списком (массивом)"
    assert len(data) == 0, (
        f"Список должен быть пустым, но найдено {len(data)} элементов"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_items_invalid_seller_id_type(api_client):
    invalid_id = "not-a-number"
    response = await api_client.get(f"/api/1/{invalid_id}/item")

    assert response.status_code == 400, (
        f"Ожидали 400 для невалидного ID, получили {response.status_code}"
    )

    data = response.json()
    assert "result" in data, "Отсутствует объект 'result' в ответе 400"
    assert "status" in data, "Отсутствует поле 'status' в ответе 400"
    assert "message" in data["result"], "Отсутствует текстовое сообщение об ошибке"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_items_negative_seller_id(api_client):
    response = await api_client.get("/api/1/-500/item")

    assert response.status_code in [400, 404], (
        f"Неправильный статус для отрицательного ID: {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_items_large_seller_id(api_client):
    large_id = 999999999999999999999
    response = await api_client.get(f"/api/1/{large_id}/item")

    assert response.status_code != 500, (
        "Сервер упал с 500 ошибкой при слишком большом sellerId"
    )
