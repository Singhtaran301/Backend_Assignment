import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from fastapi_limiter import FastAPILimiter
from src.common.cache import cache

# 1. Base URL for tests
BASE_URL = "http://test"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    # Initialize Rate Limiter
    await FastAPILimiter.init(cache.redis)

    transport = ASGITransport(app=app)
    # --- FIX IS HERE: follow_redirects=True ---
    async with AsyncClient(transport=transport, base_url=BASE_URL, follow_redirects=True) as c:
        yield c

# 3. Helper to get a Token
@pytest.fixture
async def auth_token(client):
    login_payload = {
        "email": "patient@gmail.com", 
        "password": "password123"
    }
    headers = {"Idempotency-Key": "test-login-helper"}
    response = await client.post("/auth/login", json=login_payload, headers=headers)
    return response.json()["access_token"]