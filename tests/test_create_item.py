import json

import allure
import pytest

from models.models import ItemRequest, ItemResponse, Statistics


@allure.epic("Объявления")
@allure.feature("Создание объявлений")
class TestCreateItem:
    @allure.title("Успешное создание объявления с полным набором данных")
    @allure.description(
        "Проверка корректности создания айтема и валидация схемы ответа"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.xfail(reason="Сервис возвращает строку вместо объекта (BUG-01)")
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_positive(self, api_client, valid_item_payload):
        with allure.step("Подготовка данных объявления"):
            payload = valid_item_payload.model_dump(by_alias=True)
            allure.attach(
                json.dumps(payload, indent=2, ensure_ascii=False),
                "Request Payload",
                allure.attachment_type.JSON,
            )

        with allure.step("Отправка POST запроса на /api/1/item"):
            response = await api_client.post("/api/1/item", json=payload)
            allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

        with allure.step("Проверка статус-кода 200"):
            assert response.status_code == 200

        with allure.step("Валидация структуры ответа через модель ItemResponse"):
            try:
                data = ItemResponse.model_validate(response.json())
                assert data.seller_id == valid_item_payload.seller_id
                assert data.name == valid_item_payload.name
            except Exception as e:
                allure.attach(str(e), "Validation Error", allure.attachment_type.TEXT)
                pytest.fail(f"BUG-01: Несоответствие структуры ответа. Ошибка: {e}")

    @allure.title("Проверка обязательности объекта статистики")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_without_statistics(self, api_client):
        payload = ItemRequest(
            seller_id=235839, name="Ноутбук", price=150000, statistics=None
        )

        response = await api_client.post(
            "/api/1/item", json=payload.model_dump(by_alias=True)
        )

        assert response.status_code == 400, (
            "Сервис должен запрещать создание без статистики"
        )

    @allure.title("Проверка идемпотентности POST-запроса")
    @allure.description(
        "При отправке двух одинаковых запросов должны создаваться разные объявления"
    )
    @pytest.mark.xfail(reason="Сервер вернул один и тот же ID для разных сущностей (BUG-03)")
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_idempotency(self, api_client):
        payload = ItemRequest(
            seller_id=777886,
            name="iPad 2026",
            price=50000,
            statistics=Statistics(likes=0, view_count=0, contacts=0),
        )

        with allure.step("Первый запрос на создание"):
            res1 = await api_client.post(
                "/api/1/item", json=payload.model_dump(by_alias=True)
            )
            id1 = res1.json().get("status").split(" - ")[-1].strip()

        with allure.step("Второй запрос на создание"):
            res2 = await api_client.post(
                "/api/1/item", json=payload.model_dump(by_alias=True)
            )
            id2 = res2.json().get("status").split(" - ")[-1].strip()

        assert id1 != id2, "BUG-03: Сервер вернул один и тот же ID для разных сущностей"

    @allure.title("Валидация поля Price (Параметризованный тест)")
    @pytest.mark.xfail(reason="API не дает возможность создать объявление с бесплатной услугой (BUG-07)")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "price_value, expected_status, message",
        [
            (
                pytest.param(
                    -150000,
                    400,
                    "Negative price",
                    marks=pytest.mark.xfail(reason="BUG-02"),
                )
            ),
            (0, 200, "Zero price"),
            (
                pytest.param(
                    "10000",
                    400,
                    "String price",
                    marks=pytest.mark.xfail(reason="BUG-04"),
                )
            ),
            (5200.96, 400, "Float price"),
            (150000, 200, "Valid price"),
        ],
        ids=["negative", "zero", "string", "float", "valid"],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_price_validation(
        self, api_client, item_payload_factory, price_value, expected_status, message
    ):
        with allure.step(f"Тестирование цены: {price_value}"):
            payload = item_payload_factory(price=price_value)
            response = await api_client.post(
                "/api/1/item", json=payload.model_dump(by_alias=True)
            )

            allure.attach(response.text, "Response", allure.attachment_type.JSON)
            assert response.status_code == expected_status, (
                f"{message}: {response.text}"
            )

    @allure.title("Консистентность данных (Create -> Get)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_consistency(self, api_client, created_item):
        item_id = created_item["id"]
        original_payload = created_item["payload"]

        with allure.step(f"Запрос созданного айтема по ID: {item_id}"):
            get_res = await api_client.get(f"/api/1/item/{item_id}")
            assert get_res.status_code == 200

        with allure.step("Сравнение полученных данных с исходными"):
            # Предполагаем, что API возвращает список
            db_item = ItemResponse.model_validate(get_res.json()[0])
            assert db_item.name == original_payload.name
            assert db_item.price == original_payload.price

    @allure.title("Проверка устойчивости к некорректному JSON")
    @allure.description("Попытка вызвать 500 ошибку через Malformed JSON")
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_malformed_json_500_check(self, api_client):
        malformed_json = (
            '{"sellerId": 123, "name": "Broken", "price": 100, "statistics": {'
        )
        headers = {"Content-Type": "application/json"}

        with allure.step("Отправка битого JSON"):
            # Используем напрямую клиент httpx для отправки сырой строки
            response = await api_client.post(
                "/api/1/item", content=malformed_json, headers=headers
            )

        with allure.step("Проверка отсутствия 500 ошибки"):
            assert response.status_code != 500, (
                "Сервер упал при парсинге некорректного JSON"
            )
            assert response.status_code == 400

    @allure.title("Валидация значений в объекте статистики")
    @allure.description(
        "Проверка граничных и некорректных значений"
        + "для лайков и просмотров (BUG-05, BUG-06)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    
    @pytest.mark.parametrize(
        "likes_val, expected_status, bug_id",
        [
            (
                pytest.param(
                    -5,
                    400,
                    "BUG-05",
                    marks=pytest.mark.xfail(reason="Разрешены отрицательные лайки"),
                )
            ),
            (
                pytest.param(
                    0,
                    200,
                    "BUG-06",
                    marks=pytest.mark.xfail(reason="Сервер требует likes > 0"),
                )
            ),
            (100, 200, "Valid case"),
        ],
        ids=["negative_likes", "zero_likes", "valid_likes"],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_item_statistics_validation(
        self, api_client, item_payload_factory, likes_val, expected_status, bug_id
    ):
        with allure.step(f"Подготовка данных со статистикой: likes={likes_val}"):
            # Создаем объект статистики с заданным количеством лайков
            stats = Statistics(likes=likes_val, view_count=10, contacts=5)
            payload = item_payload_factory(statistics=stats)

        with allure.step(f"Отправка запроса (Ожидаем {expected_status})"):
            response = await api_client.post(
                "/api/1/item", json=payload.model_dump(by_alias=True)
            )
            allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

            assert response.status_code == expected_status, (
                f"{bug_id}: Ожидали {expected_status},"
                + " но получили {response.status_code}. Ответ: {response.text}"
            )
