import random
import pytest
import allure
import json
from typing import List
from pydantic import TypeAdapter
from models.models import ItemRequest, ItemResponse

@allure.epic("Объявления")
@allure.feature("Объявления продавца")
class TestGetSellerItems:

    @allure.title("Проверка списка объявлений конкретного продавца")
    @allure.description("Создание нескольких айтемов и проверка корректности фильтрации по sellerId")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_items_by_seller_id_full_check(self, api_client):
        with allure.step("Генерация уникального sellerId и данных"):
            seller_id = random.randint(200000, 300000)
            payload = ItemRequest(
                seller_id=seller_id,
                name="Товар продавца",
                price=1000,
                statistics={"likes": 1, "view_count": 1, "contacts": 1},
            )

        with allure.step(f"Создание двух объявлений для продавца {seller_id}"):
            await api_client.post("/api/1/item", json=payload.model_dump(by_alias=True))
            payload.name = "Второй товар продавца"
            await api_client.post("/api/1/item", json=payload.model_dump(by_alias=True))

        with allure.step(f"Запрос списка объявлений для sellerId: {seller_id}"):
            response = await api_client.get(f"/api/1/{seller_id}/item")
            allure.attach(response.text, name="Seller Items Response", attachment_type=allure.attachment_type.JSON)
            assert response.status_code == 200

        with allure.step("Валидация схемы списка и проверка изоляции данных"):
            data = response.json()
            adapter = TypeAdapter(List[ItemResponse])
            try:
                items = adapter.validate_python(data)
            except Exception as e:
                allure.attach(str(e), name="Validation Error")
                pytest.fail(f"Структура списка не соответствует ItemResponse: {e}")

            assert len(items) >= 2, f"Ожидали минимум 2 товара, получили {len(items)}"
            for item in items:
                assert item.seller_id == seller_id, (
                    f"BUG: Найдено чужое объявление! Ожидали {seller_id}, получили {item.seller_id}"
                )

    @allure.title("Запрос списка для нового продавца (без объявлений)")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_items_empty_seller(self, api_client):
        new_seller_id = random.randint(1000001, 1999999)

        with allure.step(f"Запрос списка для пустого sellerId: {new_seller_id}"):
            response = await api_client.get(f"/api/1/{new_seller_id}/item")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0, f"Ожидался пустой список, но найдено {len(data)} элементов"

    @allure.title("Валидация некорректных типов SellerId")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("invalid_id, expected_status", [
        ("not-a-number", 400),
        ("-500", 400),
        ("999999999999999999999", 400)
    ], ids=["string", "negative", "overflow"])
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_items_invalid_seller_ids(self, api_client, invalid_id, expected_status):
        with allure.step(f"Запрос списка для некорректного ID: {invalid_id}"):
            response = await api_client.get(f"/api/1/{invalid_id}/item")
            
            allure.attach(str(response.status_code), name="Actual Status Code")
            # Проверяем на 500 ошибку (устойчивость)
            assert response.status_code != 500, "Сервер упал с 500 ошибкой"
            # Проверяем соответствие ожидаемому статусу (400/404)
            assert response.status_code in [expected_status, 404]

        if response.status_code == 400:
            with allure.step("Проверка структуры сообщения об ошибке 400"):
                data = response.json()
                assert "result" in data and "status" in data
