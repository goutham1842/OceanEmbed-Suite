"""
OceanEmbed — Tests for FastAPI Endpoints.
"""

import asyncio
import sys
from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app


def run_sync(coro):
    return asyncio.run(coro)


class SimpleAsyncTestClient:
    def __init__(self, app):
        self.app = app

    def get(self, path):
        async def _do():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as c:
                return await c.get(path)
        return run_sync(_do())

    def post(self, path, json=None):
        async def _do():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as c:
                return await c.post(path, json=json)
        return run_sync(_do())


def get_test_client():
    return SimpleAsyncTestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "OceanEmbed"
    assert "demo_mode" in data


def test_depths_endpoint(client):
    res = client.get("/api/depths")
    assert res.status_code == 200
    data = res.json()
    assert len(data["sih_standard_depths"]) == 15
    assert data["continuous_depth_supported"] is True


def test_prediction_continuous_query(client):
    # Query non-standard depth e.g. 173.5m
    res = client.get("/api/prediction?lat=14.0&lon=68.0&date=2020-06-15&depth=173.5")
    assert res.status_code == 200
    data = res.json()
    assert data["lat"] == 14.0
    assert data["lon"] == 68.0
    assert data["depths"] == [173.5]
    assert len(data["temperatures"]) == 1
    assert len(data["uncertainties"]) == 1


def test_profile_post_endpoint(client):
    payload = {
        "lat": 16.0,
        "lon": 85.0,
        "date": "2020-06-15",
        "masks": {"sss": True},
    }
    res = client.post("/api/profile", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["temperatures"]) == 15
    assert len(data["uncertainties"]) == 15


if pytest is not None:
    @pytest.fixture
    def client():
        return get_test_client()


if __name__ == "__main__":
    c = get_test_client()
    test_health_endpoint(c)
    test_depths_endpoint(c)
    test_prediction_continuous_query(c)
    test_profile_post_endpoint(c)
    print("ALL BACKEND ENDPOINT TESTS PASSED!")
