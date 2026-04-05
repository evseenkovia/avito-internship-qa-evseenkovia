import pytest
from models.models import ItemRequest, ItemResponse, Statistics

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_positive(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price=150000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 200, f"Ожидаемый код: 200, получен {response.status_code}"
    
    try:
        data = ItemResponse.model_validate(response.json())
        assert data.sellerId == payload.sellerId
        assert data.name == payload.name
    except Exception as e:
        pytest.fail(f"Схема ответа не соответствует ожидаемой.")

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_without_statistics(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price=150000,
        statistics=None
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_price_negative(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price=-150000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_price_zero(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price=0,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_price_string(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price="10000",
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}. Цена не должна быть строкой."

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_price_float(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="Игровой ноутбук",
        price=5200.96,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}. Цена должна быть целочисленным параметром."

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_absent(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, f"Ожидаемый код: 400, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_long(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="qwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopasdfghjklzxcvbnmmnbvqwertyuiopqwertyuiopqwerty",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 200, f"Ожидаемый код: 200, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_name_numeric(api_client):
    
    payload = ItemRequest(
        sellerId=235839,
        name="12345678987654321",
        price=15000,
        statistics=Statistics(likes=10, viewCount=100, contacts=15)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 200, f"Ожидаемый код: 200, получен {response.status_code}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_idempotency(api_client):
    
    payload = ItemRequest(
        sellerId=777886,
        name="Идемпотентный котик",
        price=5000,
        statistics=Statistics(likes=0, viewCount=0, contacts=0)
    )
    
    response1 = await api_client.post("/api/1/item", json=payload.model_dump())
    status_text1 = response1.json().get("status", "")    
    id1 = status_text1.split(" - ")[-1].strip()

    response2 = await api_client.post("/api/1/item", json=payload.model_dump())
    status_text2 = response2.json().get("status", "")
    id2 = status_text2.split(" - ")[-1].strip()
    
    assert id1 != id2, "Сервис вернул тот же ID, хотя POST для объявлений обычно создает дубликат"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_statistics_negative(api_client):
    
    payload = ItemRequest(
        sellerId=111222,
        name="Котик со странной статистикой",
        price=1000,
        statistics=Statistics(likes=-5, viewCount=-10, contacts=-1)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 400, (
        f"Ожидался статус 400 для отрицательной статистики, но пришел {response.status_code}"
    )

@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_statistics_zero_values(api_client):
    
    payload = ItemRequest(
        sellerId=111222,
        name="Котик со странной статистикой",
        price=1000,
        statistics=Statistics(likes=0, viewCount=0, contacts=0)
    )
    
    response = await api_client.post("/api/1/item", json=payload.model_dump())
    
    assert response.status_code == 200, (
        f"Ожидался статус 400 для нулевых значений статистики, но пришел {response.status_code}"
    )
    
@pytest.mark.asyncio(loop_scope="session")
async def test_create_item_consistency(api_client):

    payload = ItemRequest(
        sellerId=555666,
        name="Британский котик для проверки",
        price=35000,
        statistics={"likes": 12, "viewCount": 150, "contacts": 5}
    )
    
    post_res = await api_client.post("/api/1/item", json=payload.model_dump())
    assert post_res.status_code == 200
    
    status_text = post_res.json().get("status", "")
    item_id = status_text.split(" - ")[-1].strip()
    
    get_res = await api_client.get(f"/api/1/item/{item_id}")
    assert get_res.status_code == 200, f"Не удалось найти созданное объявление с ID {item_id}"
    
    db_item = ItemResponse.model_validate(get_res.json()[0])
    
    assert db_item.name == payload.name, f"Имя изменилось! Ожидали {payload.name}, получили {db_item.name}"
    assert db_item.price == payload.price, f"Цена изменилась! Ожидали {payload.price}, получили {db_item.price}"
    assert db_item.sellerId == payload.sellerId
    
    assert db_item.statistics.likes == payload.statistics.likes
    assert db_item.statistics.viewCount == payload.statistics.viewCount
    assert db_item.statistics.contacts == db_item.statistics.contacts


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
    
    response = await api_client.post("/api/1/item", content=malformed_json_string, headers=headers)
    
    assert response.status_code != 500, (
        f"Сервер упал с 500 ошибкой при парсинге битого JSON. "
        f"Фактический статус: {response.status_code}"
    )
    
    assert response.status_code == 400, f"Ожидали 400 на битый JSON, но получили {response.status_code}"
