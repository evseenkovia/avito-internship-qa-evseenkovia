from typing import List, Union

import pytest
from pydantic import TypeAdapter

from models.models import ItemRequest, Statistics


def normalize_stats(data: Union[dict, list]) -> Statistics:
    if isinstance(data, list):
        return Statistics.model_validate(data[0])
    return Statistics.model_validate(data)


@pytest.mark.parametrize("api_version", ["api/1", "api/2"])
@pytest.mark.asyncio(loop_scope="session")
async def test_statistic_consistency_v1_v2(api_client, api_version):
    target_stats = Statistics(likes=777, viewCount=1000, contacts=50)
    payload = {
        "sellerId": 999888,
        "name": f"Item for {api_version}",
        "price": 100000,
        "statistics": target_stats.model_dump(),
    }

    post_res = await api_client.post("/api/1/item", json=payload)
    item_id = post_res.json().get("status").split(" - ")[-1].strip()

    stat_res = await api_client.get(f"/{api_version}/statistic/{item_id}")
    assert stat_res.status_code == 200

    received_data = normalize_stats(stat_res.json())
    assert received_data.likes == target_stats.likes
    assert received_data.viewCount == target_stats.viewCount
    assert received_data.contacts == target_stats.contacts

    target_stats = Statistics(likes=777, viewCount=1000, contacts=50)
    payload = ItemRequest(
        sellerId=999888, name="Kia optima", price=100000, statistics=target_stats
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
    except Exception:
        pytest.fail(
            "Ответ v2 не соответствует схеме List[StatisticItem]."
        )

    assert len(stats_list) > 0, "Список статистики пуст"

    received_stat = stats_list[0]
    assert received_stat.likes == target_stats.likes, (
        f"Ожидали {target_stats.likes} лайков, получили {received_stat.likes}"
    )
    assert received_stat.viewCount == target_stats.viewCount
    assert received_stat.contacts == target_stats.contacts


@pytest.mark.parametrize("api_version", ["api/1", "api/2"])
@pytest.mark.asyncio(loop_scope="session")
async def test_statistic_not_found_v1_v2(api_client, api_version):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await api_client.get(f"/{api_version}/statistic/{fake_id}")

    assert response.status_code == 404
    data = response.json()

    assert "result" in data, f"В {api_version} отсутствует поле 'result' при 404"
    assert "status" in data, f"В {api_version} отсутствует поле 'status' при 404"


@pytest.mark.parametrize("api_version", ["api/1", "api/2"])
@pytest.mark.asyncio(loop_scope="session")
async def test_statistic_idempotency_v1_v2(api_client, created_item_id, api_version):
    endpoint = f"/{api_version}/statistic/{created_item_id}"

    res1 = await api_client.get(endpoint)
    res2 = await api_client.get(endpoint)

    assert res1.status_code == 200
    assert res1.json() == res2.json(), (
        f"Данные в {api_version} изменились при повторном GET"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_invalid_id_format(api_client):
    response = await api_client.get("/api/2/statistic/no-id-like-that")
    assert response.status_code in [400, 404], (
        f"Неправильный статус для несуществующего ID: {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_invalid_id_range(api_client):
    response = await api_client.get(f"/api/2/statistic/{-5}")
    assert response.status_code in [400, 404], (
        f"Неправильный статус для несуществующего ID: {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_item_statistic_extra_slash(api_client, created_item_id):
    response = await api_client.get(f"/api/2/statistic//{created_item_id}")
    assert response.status_code == 200, (
        f"Неправильный статус для запроса с лишним /: {response.status_code}"
    )


@pytest.mark.parametrize("api_version", ["api/1", "api/2"])
@pytest.mark.asyncio(loop_scope="session")
async def test_statistic_invalid_id_v1_v2(api_client, api_version):
    for invalid_id in ["not-a-uuid", "-5", " "]:
        response = await api_client.get(f"/{api_version}/statistic/{invalid_id}")
        assert response.status_code in [400, 404], (
            f"{api_version} неверный статус {response.status_code} для ID: {invalid_id}"
        )
