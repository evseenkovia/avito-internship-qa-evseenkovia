import random

import pytest_asyncio
from httpx import AsyncClient


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
        "name": "Async Test Item",
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }

    # Делаем запрос и сразу проверяем статус
    response = await api_client.post("/api/1/item", json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Setup failed: {response.text}")

    status_text = response.json().get("status", "")
    return status_text.split(" - ")[-1].strip()


@pytest_asyncio.fixture(loop_scope="session")
async def item_for_deletion(api_client):
    payload = {
        "sellerId": 111999,
        "name": "Item to be deleted",
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }
    response = await api_client.post("/api/1/item", json=payload)
    item_id = response.json().get("status").split(" - ")[-1].strip()
    return item_id
