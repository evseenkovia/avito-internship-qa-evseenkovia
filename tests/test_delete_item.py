
import asyncio

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_item_e2e(api_client, created_item_id):
    delete_res = await api_client.delete(f"/api/1/item/{created_item_id}")

    assert delete_res.status_code in [200, 204, 405], (
        f"DELETE вернул {delete_res.status_code}, ожидался 200/204/405. "
        f"API не удаляет объявление или метод не поддерживается"
    )

    await asyncio.sleep(0.5)

    get_res = await api_client.get(f"/api/1/item/{created_item_id}")

    assert get_res.status_code == 404, (
        f"GET после DELETE вернул {get_res.status_code}, ожидался 404. "
        f"Объявление не было удалено"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_non_existent_item(api_client, fake_uuid):
    response = await api_client.delete(f"/api/1/item/{fake_uuid}")
    assert response.status_code == 404, (
        f"Вернул {response.status_code}, ожидался 404. "
        f"API не различает существующий и несуществующий ID"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_already_deleted_item(api_client, created_item_id):
    await api_client.delete(f"/api/1/item/{created_item_id}")
    response = await api_client.delete(f"/api/1/item/{created_item_id}")
    assert response.status_code == 404, (
        f"Вернул {response.status_code}, ожидался 404. "
        f"Повторное удаление не обрабатывается как 404"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_invalid_format_id(api_client):
    response = await api_client.delete("/api/1/item/invalid-uuid-format")
    assert response.status_code in [400, 404, 405], (
        f"Вернул {response.status_code}, ожидался 400/404/405. "
        f"API не валидирует формат ID"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_negative_id(api_client):
    response = await api_client.delete("/api/1/item/-1")
    assert response.status_code in [400, 404, 405], (
        f"Вернул {response.status_code}, ожидался 400/404/405. "
        f"API принимает отрицательный ID"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_empty_id(api_client):
    response = await api_client.delete("/api/1/item/")
    assert response.status_code in [404, 405], (
        f"Вернул {response.status_code}, ожидался 404/405. "
        f"Пустой ID обработан некорректно"
    )
