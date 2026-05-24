"""Testes da API CryptoGhost."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CryptoGhost"
    assert data["paper_trading"] is True


@pytest.mark.asyncio
async def test_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "bruce", "password": "test-password"},
        )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "wrong", "password": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_full_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/full")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
    assert "ollama" in data["checks"]
