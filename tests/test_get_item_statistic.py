import pytest
import allure
import json
from typing import List, Union
from pydantic import TypeAdapter
from models.models import ItemRequest, Statistics

def normalize_stats(data: Union[dict, list]) -> Statistics:
    if isinstance(data, list):
        return Statistics.model_validate(data[0])
    return Statistics.model_validate(data)

@allure.epic("Объявления")
@allure.feature("Статистика объявлений")
class TestGetStatistic:

    @allure.title("Консистентность статистики: {api_version}")
    @allure.description("Проверка соответствия данных в сервисе статистики после создания объявления")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("api_version", ["api/1", "api/2"])
    @pytest.mark.asyncio(loop_scope="session")
    async def test_statistic_consistency_v1_v2(self, api_client, api_version, item_payload_factory):
        with allure.step("Подготовка тестовых данных"):
            target_stats = Statistics(likes=777, view_count=1000, contacts=50)
            payload = item_payload_factory(
                name=f"Stat Check {api_version}",
                price=100000,
                statistics=target_stats
            )

        with allure.step("Создание объявления через POST"):
            post_res = await api_client.post("/api/1/item", json=payload.model_dump(by_alias=True))
            item_id = post_res.json().get("status").split(" - ")[-1].strip()
            allure.attach(item_id, name="Created Item ID", attachment_type=allure.attachment_type.TEXT)

        with allure.step(f"Запрос статистики через {api_version}"):
            stat_res = await api_client.get(f"/{api_version}/statistic/{item_id}")
            allure.attach(stat_res.text, name=f"Response {api_version}", attachment_type=allure.attachment_type.JSON)
            assert stat_res.status_code == 200

        with allure.step("Валидация и сравнение данных"):
            received_data = normalize_stats(stat_res.json())
            assert received_data.likes == target_stats.likes
            assert received_data.view_count == target_stats.view_count
            assert received_data.contacts == target_stats.contacts

    @allure.title("Обработка 404 ошибки в сервисе статистики: {api_version}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("api_version", ["api/1", "api/2"])
    @pytest.mark.asyncio(loop_scope="session")
    async def test_statistic_not_found_v1_v2(self, api_client, api_version, fake_uuid):
        
        with allure.step(f"Запрос несуществующего ID через {api_version}"):
            response = await api_client.get(f"/{api_version}/statistic/{fake_uuid}")
            assert response.status_code == 404
            data = response.json()

        with allure.step("Проверка наличия полей result и status согласно документации"):
            assert "result" in data, f"BUG: В {api_version} отсутствует 'result'"
            assert "status" in data, f"BUG: В {api_version} отсутствует 'status'"

    @allure.title("Идемпотентность GET запроса статистики: {api_version}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("api_version", ["api/1", "api/2"])
    @pytest.mark.asyncio(loop_scope="session")
    async def test_statistic_idempotency_v1_v2(self, api_client, created_item_id, api_version):
        endpoint = f"/{api_version}/statistic/{created_item_id}"

        with allure.step(f"Выполнение повторных запросов к {endpoint}"):
            res1 = await api_client.get(endpoint)
            res2 = await api_client.get(endpoint)

        with allure.step("Сравнение ответов"):
            assert res1.status_code == 200
            assert res1.json() == res2.json(), "Данные изменились при повторном чтении"

    @allure.title("Валидация формата ID в статистике")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("invalid_path, expected_codes", [
        ("no-id-like-that", [400, 404]),
        ("-5", [400, 404]),
        ("/extra-slash/", [200, 404]) # пример для лишнего слеша
    ], ids=["string_id", "negative_id", "extra_slash"])
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_item_statistic_invalid_formats(self, api_client, invalid_path, expected_codes, created_item_id):
        # Логика для формирования URL (обработка спецкейса со слешем)
        path = f"/api/2/statistic/{invalid_path}"
        if "slash" in path: path = f"/api/2/statistic//{created_item_id}"
            
        with allure.step(f"Запрос по невалидному пути: {path}"):
            response = await api_client.get(path)
            allure.attach(str(response.status_code), name="Actual Status")
            assert response.status_code in expected_codes
