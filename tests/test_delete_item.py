import asyncio

import allure
import pytest


@allure.epic("Объявления")
@allure.feature("Удаление объявлений")
class TestDeleteItem:
    @allure.title("E2E сценарий: Полное удаление существующего объявления")
    @pytest.mark.xfail(
        reason="BUG-08/09: Метод DELETE не работает или не удаляет данные"
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_delete_item_e2e(self, api_client, created_item_id):
        with allure.step(f"Выполнение запроса DELETE для ID: {created_item_id}"):
            delete_res = await api_client.delete(f"/api/1/item/{created_item_id}")
            allure.attach(
                str(delete_res.status_code),
                name="Delete Status Code",
                attachment_type=allure.attachment_type.TEXT,
            )

            assert delete_res.status_code in [200, 204, 405], (
                f"Ошибка при удалении: {delete_res.status_code}"
            )

        with allure.step("Ожидание синхронизации базы данных (0.5s)"):
            await asyncio.sleep(0.5)

        with allure.step("Проверка отсутствия объявления через GET"):
            get_res = await api_client.get(f"/api/1/item/{created_item_id}")
            allure.attach(
                str(get_res.status_code),
                name="GET Status After Delete",
                attachment_type=allure.attachment_type.TEXT,
            )

        get_res = await api_client.get(f"/api/1/item/{created_item_id}")
        assert get_res.status_code == 404

    @allure.title("Удаление несуществующего ID")
    @pytest.mark.xfail(
        reason="BUG-10: Сервер возвращает 405 вместо 404 для несуществующих ID"
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_delete_non_existent_item(self, api_client, fake_uuid):
        response = await api_client.delete(f"/api/1/item/{fake_uuid}")
        assert response.status_code == 404

    @allure.title("Повторное удаление уже удаленного ресурса")
    @allure.description(
        "Проверка идемпотентности/корректности обработки повторных DELETE запросов"
    )
    @pytest.mark.xfail(
        reason="BUG-08/09: Метод DELETE не работает или не удаляет данные"
    )
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.asyncio(loop_scope="session")
    async def test_delete_already_deleted_item(self, api_client, created_item_id):
        with allure.step("Первичное удаление"):
            await api_client.delete(f"/api/1/item/{created_item_id}")

        with allure.step("Повторное удаление того же ID"):
            response = await api_client.delete(f"/api/1/item/{created_item_id}")

        with allure.step("Ожидание статуса 404"):
            assert response.status_code == 404

    @allure.title("Валидация формата ID при удалении")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(
        "invalid_id, test_name",
        [
            ("invalid-uuid-format", "строковый формат"),
            ("-1", "отрицательное число"),
            ("", "пустой id"),
        ],
        ids=["string", "negative", "empty"],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_delete_invalid_ids(self, api_client, invalid_id, test_name):
        with allure.step(
            f"Удаление ID с нарушением формата: {test_name} ('{invalid_id}')"
        ):
            url = f"/api/1/item/{invalid_id}" if invalid_id else "/api/1/item/"
            response = await api_client.delete(url)

        with allure.step("Проверка возвращаемого статус-кода (ожидаем 400/404/405)"):
            allure.attach(
                str(response.status_code),
                name="Actual Status Code",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert response.status_code in [400, 404, 405]
