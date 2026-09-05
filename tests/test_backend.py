"""
OceanEmbed — Tests for FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


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
