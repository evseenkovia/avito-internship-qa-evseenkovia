import asyncio
import random

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models.models import ItemRequest, Statistics


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def api_client():
    async with AsyncClient(
        base_url="https://qa-internship.avito.com", timeout=10.0
    ) as client:
        yield client


@pytest_asyncio.fixture(loop_scope="session")
async def created_item_id(api_client):
    payload = {
        "sellerId": random.randint(111111, 999999),
        "name": "QA Test Item",
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }

    response = await api_client.post("/api/1/item", json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Setup failed: {response.text}")

    status_text = response.json().get("status", "")
    return status_text.split(" - ")[-1].strip()


@pytest.fixture(scope="session")
def valid_item_payload():
    return ItemRequest(
        seller_id=random.randint(111111, 999999),
        name="Игровой ноутбук",
        price=150000,
        statistics=Statistics(likes=10, view_count=100, contacts=15),
    )


@pytest.fixture
def minimal_item_payload():
    return ItemRequest(
        sellerId=random.randint(111111, 999999),
        name="Минимальный товар",
        price=100,
        statistics=None,
    )


@pytest.fixture
def item_payload_factory():
    def _create(**overrides):
        params = {
            "sellerId": random.randint(111111, 999999),
            "name": "Товар по умолчанию",
            "price": 1000,
            "statistics": Statistics(likes=5, view_count=50, contacts=3),
        }
        params.update(overrides)

        return ItemRequest(**params)

    return _create


@pytest_asyncio.fixture(scope="session")
async def created_item(api_client, valid_item_payload):
    response = await api_client.post(
        "/api/1/item", json=valid_item_payload.model_dump(by_alias=True)
    )
    assert response.status_code == 200
    status_text = response.json().get("status", "")
    item_id = status_text.split(" - ")[-1].strip()

    return {"id": item_id, "payload": valid_item_payload}


@pytest.fixture
def fake_uuid():
    return "00000000-0000-0000-0000-000000000000"
