#!/usr/bin/env python3
"""CryptoGhost v5 - Testes de stack completa (DB, Redis, Ollama, API, Celery)."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONPATH", str(ROOT))

import httpx

API_BASE = os.environ.get("CRYPTOGHOST_TEST_API", "http://localhost:8000")
TIMEOUT = 30.0


def ok(name: str, passed: bool, detail: str = "") -> bool:
    mark = "✅" if passed else "❌"
    msg = f"{mark} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return passed


async def test_database() -> bool:
    from backend.shared.health_service import check_database

    result = await check_database()
    return ok("Database", result["status"] == "healthy", str(result))


async def test_redis() -> bool:
    from backend.shared.health_service import check_redis

    result = await check_redis()
    return ok("Redis", result["status"] == "healthy", str(result))


async def test_ollama() -> bool:
    from backend.shared.health_service import check_ollama

    result = await check_ollama()
    return ok("Ollama", result["status"] in ("healthy", "degraded"), str(result))


def test_celery() -> bool:
    from backend.shared.health_service import check_celery

    result = check_celery()
    return ok("Celery", result["status"] in ("healthy", "degraded"), str(result))


async def test_api_health() -> bool:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{API_BASE}/health/full")
    data = r.json()
    return ok("API /health/full", r.status_code == 200 and data.get("status") in ("healthy", "degraded"), data.get("status", ""))


async def test_migrations() -> bool:
    from sqlalchemy import text
    from backend.shared.database import async_engine

    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            version = result.scalar()
        return ok("Migrations", bool(version), f"head={version}")
    except Exception as exc:
        return ok("Migrations", False, str(exc))


async def test_dashboard_v5() -> bool:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{API_BASE}/api/v1/v5/dashboard")
    passed = r.status_code == 200
    return ok("Dashboard v5", passed, f"status={r.status_code}")


async def test_investment() -> bool:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{API_BASE}/api/v1/investment/best-opportunity")
    passed = r.status_code in (200, 404)
    return ok("Investment best-opportunity", passed, f"status={r.status_code}")


async def test_intelligence_analyze() -> bool:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{API_BASE}/api/v1/intelligence/analyze/BTC/USDT")
    passed = r.status_code in (200, 202, 401)
    return ok("Intelligence analyze BTC/USDT", passed, f"status={r.status_code}")


async def test_websocket() -> bool:
    import websockets

    ws_url = API_BASE.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    try:
        async with websockets.connect(ws_url, open_timeout=10) as ws:
            await ws.send("ping")
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
        return ok("WebSocket", "pong" in msg.lower() or "type" in msg.lower(), msg[:80])
    except Exception as exc:
        return ok("WebSocket", False, str(exc))


async def test_prometheus() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{API_BASE}/metrics")
        return ok("Prometheus metrics", r.status_code == 200, f"bytes={len(r.content)}")
    except Exception as exc:
        return ok("Prometheus metrics", False, str(exc))


async def main() -> int:
    print("\n🧪 CryptoGhost v5 — Full Stack Tests\n")
    print(f"API: {API_BASE}\n")

    results = [
        await test_database(),
        await test_redis(),
        await test_ollama(),
        test_celery(),
        await test_migrations(),
        await test_api_health(),
        await test_prometheus(),
        await test_dashboard_v5(),
        await test_investment(),
        await test_intelligence_analyze(),
        await test_websocket(),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 40}\nResultado: {passed}/{total} testes passaram\n{'=' * 40}\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
