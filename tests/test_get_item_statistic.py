import pytest
from models.models import ItemRequest, Statistics
from pydantic import TypeAdapter
from typing import List

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_consistency(api_client):

    target_stats = Statistics(likes=777, viewCount=1000, contacts=50)
    payload = ItemRequest(
        sellerId=999888,
        name="Kia optima",
        price=100000,
        statistics=target_stats
    )
    
    post_res = await api_client.post("/api/1/item", json=payload.model_dump())
    assert post_res.status_code == 200
    
    item_id = post_res.json().get("status").split(" - ")[-1].strip()

    stat_res = await api_client.get(f"/api/2/statistic/{item_id}")
    assert stat_res.status_code == 200
    
    raw_data = stat_res.json()
    
    adapter = TypeAdapter(List[Statistics])
    try:
        stats_list = adapter.validate_python(raw_data)
    except Exception as e:
        pytest.fail(f"Ответ v2 не соответствует схеме List[StatisticItem]. Данные: {raw_data}. Ошибка: {e}")

    assert len(stats_list) > 0, "Список статистики пуст"
    
    received_stat = stats_list[0]
    assert received_stat.likes == target_stats.likes, f"Ожидали {target_stats.likes} лайков, получили {received_stat.likes}"
    assert received_stat.viewCount == target_stats.viewCount
    assert received_stat.contacts == target_stats.contacts

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_not_found(api_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await api_client.get(f"/api/2/statistic/{fake_id}")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "result" in data, "Отсутствует поле 'result' при 404"
    assert "status" in data, "Отсутствует поле 'status' при 404"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_idempotency(api_client, created_item_id):
 
    res1 = await api_client.get(f"/api/2/statistic/{created_item_id}")
    
    res2 = await api_client.get(f"/api/2/statistic/{created_item_id}")
    
    res3 = await api_client.get(f"/api/2/statistic/{created_item_id}")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200

    assert res1.json() == res2.json() == res3.json(), "Данные статистики изменились (не идемпотентно)"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_invalid_id_format(api_client):
    response = await api_client.get("/api/2/statistic/no-id-like-that")
    assert response.status_code in [400, 404], f"Неправильный статус для несуществующего ID: {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_invalid_id_range(api_client):
    response = await api_client.get(f"/api/2/statistic/{-5}")
    assert response.status_code in [400, 404], f"Неправильный статус для несуществующего ID: {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_extra_slash(api_client, created_item_id):
    response = await api_client.get(f"/api/2/statistic//{created_item_id}")
    assert response.status_code == 200, f"Неправильный статус для запроса с лишним /: {response.status_code}"
