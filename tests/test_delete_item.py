import asyncio

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_item_e2e(api_client, item_for_deletion):
    delete_res = await api_client.delete(f"/api/1/item/{item_for_deletion}")

    assert delete_res.status_code in [200, 204, 405], (
        f"Удаление не удалось: {delete_res.status_code}"
    )

    await asyncio.sleep(0.5)

    get_res = await api_client.get(f"/api/1/item/{item_for_deletion}")

    assert get_res.status_code == 404, (
        f"Объявдение {item_for_deletion} все еще доступно через GET после удаления! "
        f"Статус: {get_res.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_non_existent_item(api_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await api_client.delete(f"/api/1/item/{fake_id}")
    assert response.status_code == 404, (
        f"Ожидали 404 для удаления фейка, получили {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_already_deleted_item(api_client, item_for_deletion):
    await api_client.delete(f"/api/1/item/{item_for_deletion}")
    response = await api_client.delete(f"/api/1/item/{item_for_deletion}")
    assert response.status_code == 404, (
        f"Ожидали 404 для уже удаленного, получили {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_invalid_format_id(api_client):
    response = await api_client.delete("/api/1/item/invalid-uuid-format")
    assert response.status_code in [400, 404, 405], (
        f"Unexpected status: {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_negative_id(api_client):
    response = await api_client.delete("/api/1/item/-1")
    assert response.status_code in [400, 404, 405], (
        f"Unexpected status: {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_empty_id(api_client):
    response = await api_client.delete("/api/1/item/")
    assert response.status_code in [404, 405], (
        f"Unexpected status: {response.status_code}"
    )
