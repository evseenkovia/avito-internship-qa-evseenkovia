import pytest

from models.models import ItemRequest, ItemResponse, Statistics


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_positive(api_client, valid_item_payload):
    response = await api_client.post("/api/1/item",
                                     json=valid_item_payload.model_dump(by_alias=True))
    assert response.status_code == 200
    try:
        data = ItemResponse.model_validate(response.json())
        assert data.seller_id == valid_item_payload.seller_id
        assert data.name == valid_item_payload.name
    except Exception:
        pytest.fail("Сервер вернул некорректную структуру ответа" +
                    "(поле status вместо объекта)")


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_without_statistics(api_client):
    payload = ItemRequest(
        sellerId=235839, name="Игровой ноутбук", price=150000, statistics=None
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 400, (
        f"400 != {response.status_code}: Объявление нельзя создать без статистики"
    )

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_absent(api_client):
    payload = ItemRequest(
        sellerId=235839,
        name="",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15),
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 400, (
        f"Ожидаемый код: 400, получен {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_long(api_client):
    payload = ItemRequest(
        sellerId=235839,
        name="qwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopqwertyuiopqwerty",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15),
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 200, (
        f"200 != {response.status_code}: Некорректная обработка длинного названия"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_numeric(api_client):
    payload = ItemRequest(
        sellerId=235839,
        name="12345678987654321",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15),
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 400, (
        f"200 != {response.status_code}:"
        + "Нельзя создать объвление только из цифр в названии"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_idempotency(api_client):
    payload = ItemRequest(
        sellerId=777886,
        name="iPad 2026",
        price=50000,
        statistics=Statistics(likes=0, viewCount=0, contacts=0),
    )

    response1 = await api_client.post("/api/1/item", json=payload.model_dump())
    status_text1 = response1.json().get("status", "")
    id1 = status_text1.split(" - ")[-1].strip()

    response2 = await api_client.post("/api/1/item", json=payload.model_dump())
    status_text2 = response2.json().get("status", "")
    id2 = status_text2.split(" - ")[-1].strip()

    assert id1 != id2, (
        "Сервис вернул тот же ID, хотя POST для объявлений обычно создает дубликат"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_statistics_negative(api_client):
    payload = ItemRequest(
        sellerId=111222,
        name="Котик со странной статистикой",
        price=1000,
        statistics=Statistics(likes=-5, viewCount=-10, contacts=-1),
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 400, (
        f"Ожидался статус 400 для отриц. статистики, но пришел {response.status_code}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_statistics_zero_values(api_client):
    payload = ItemRequest(
        sellerId=111222,
        name="Торшер",
        price=1000,
        statistics=Statistics(likes=0, viewCount=0, contacts=0),
    )

    response = await api_client.post("/api/1/item", json=payload.model_dump())

    assert response.status_code == 200, (
        f"Ожидался статус 200 для нулевых значений, пришел {response.status_code}"
    )

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_consistency(api_client, created_item):
    item_id = created_item["id"]
    original_payload = created_item["payload"]

    print(f"\nRequesting GET /api/1/item/{item_id}")

    get_res = await api_client.get(f"/api/1/item/{item_id}")
    assert get_res.status_code == 200

    db_item = ItemResponse.model_validate(get_res.json()[0])
    assert db_item.name == original_payload.name
    assert db_item.price == original_payload.price

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_malformed_json_500_check(api_client):
    malformed_json_string = """
    {
        "sellerId": 123456,
        "name": "Broken JSON Item",
        "price": 100,
        "statistics": {
            "likes": 10,
            "viewCount": 100,
            "contacts": 15
    """

    headers = {"Content-Type": "application/json"}

    response = await api_client.post(
        "/api/1/item", content=malformed_json_string, headers=headers
    )

    assert response.status_code != 500, (
        f"Сервер упал с 500 ошибкой при парсинге битого JSON. "
        f"Фактический статус: {response.status_code}"
    )

    assert response.status_code == 400, (
        f"Ожидали 400 на битый JSON, но получили {response.status_code}"
    )

@pytest.mark.parametrize("price_value, expected_status, message", [
    (-150000, 400, "Negative price should return 400"),
    (0, 200, "Zero price should be accepted"),
    ("10000", 400, "String price should return 400"),
    (5200.96, 400, "Float price should return 400"),
    (150000, 200, "Valid price should return 200"),
], ids=[
    "negative_price",
    "zero_price",
    "string_price",
    "float_price",
    "valid_price"
])
async def test_create_item_price_validation(api_client, item_payload_factory,
                                            price_value, expected_status, message):
    payload = item_payload_factory(price=price_value)

    payload_dict = payload.model_dump(by_alias=True)
    response = await api_client.post("/api/1/item", json=payload_dict)

    assert response.status_code == expected_status, message
