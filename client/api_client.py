import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.fixture(scope="session")
async def api_client():
    async with AsyncClient(base_url="https://qa-internship.avito.com", timeout=10.0) as client:
        yield client
