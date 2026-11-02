"""API tests: the real routes, run against the pretend map in the test database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import api
from build_metrics import build_region_metrics

EQUAL_WEIGHTS = {"heat": 1 / 3, "canopy": 1 / 3, "irsd": 1 / 3}

TEST_DATASETS = [
    {"id": "test_sa2", "title": "Test SA2s", "publisher": "Test", "licence": "CC BY 4.0", "source_url": None},
    {"id": "test_seifa", "title": "Test SEIFA", "publisher": "Test", "licence": "CC BY 4.0", "source_url": None},
]


@pytest.fixture(scope="module")
def api_data(engine, pretend_map):
    # Rebuild with equal weights: an earlier test may have left region_metrics built differently.
    build_region_metrics(engine, EQUAL_WEIGHTS)
    with engine.begin() as conn:
        for dataset in TEST_DATASETS:
            conn.execute(text("""
                INSERT INTO datasets (id, title, publisher, licence, source_url)
                VALUES (:id, :title, :publisher, :licence, :source_url)
            """), dataset)


@pytest.fixture
def client(engine, api_data):
    def test_conn():
        with engine.connect() as conn:
            yield conn

    api.app.dependency_overrides[api.get_conn] = test_conn
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}