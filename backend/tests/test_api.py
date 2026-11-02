"""API tests: the real routes, run against the pretend map in the test database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import api
from build_metrics import build_region_metrics
from schemas import REGION_CSV_COLUMNS

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


def test_regions_is_a_feature_collection_of_every_sa2(client):
    response = client.get("/regions")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"

    codes = []
    for feature in body["features"]:
        codes.append(feature["id"])
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")
        assert "crs" not in feature["geometry"]
    assert codes == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]


def test_regions_without_scores_are_null_not_missing(client):
    properties = {}
    for feature in client.get("/regions").json()["features"]:
        properties[feature["id"]] = feature["properties"]

    assert properties["S5"]["double_burden"] is True
    assert properties["S6"]["risk_score"] is None
    assert properties["S7"]["risk_score"] is None


def test_region_detail_has_metrics_and_sources(client):
    response = client.get("/regions/S5")
    assert response.status_code == 200
    body = response.json()
    assert body["sa2_code"] == "S5"
    assert body["risk_score"] == pytest.approx(41 / 54, abs=1e-3)
    assert body["double_burden"] is True

    source_ids = []
    for source in body["sources"]:
        source_ids.append(source["id"])
    assert source_ids == ["test_sa2", "test_seifa"]


def test_region_detail_without_metrics_row(client):
    response = client.get("/regions/S7")
    assert response.status_code == 200
    body = response.json()
    assert body["heat_uhi"] is None
    assert body["risk_score"] is None
    assert body["vic_decile"] == 8


def test_unknown_region_is_404(client):
    assert client.get("/regions/nope").status_code == 404


def test_point_lookup_finds_containing_region(client):
    # The middle of S3, which spans units 4 to 5: longitude 145.045, halfway between SOUTH and NORTH.
    response = client.get("/regions/at", params={"lat": -37.805, "lon": 145.045})
    assert response.status_code == 200
    assert response.json()["sa2_code"] == "S3"


def test_point_outside_map_is_404(client):
    response = client.get("/regions/at", params={"lat": -33.8688, "lon": 151.2093})
    assert response.status_code == 404


@pytest.mark.parametrize("params", [
    {"lat": 500, "lon": 145.0},
    {"lat": -37.8, "lon": 999},
    {"lat": "abc", "lon": 145.0},
    {"lon": 145.0},
])
def test_point_lookup_rejects_bad_coordinates(client, params):
    assert client.get("/regions/at", params=params).status_code == 422


def test_hotspots_are_ranked_by_risk(client):
    response = client.get("/hotspots")
    assert response.status_code == 200

    codes = []
    ranks = []
    for hotspot in response.json():
        codes.append(hotspot["sa2_code"])
        ranks.append(hotspot["rank"])
    # S6 has no score and S7 has no metrics row, so neither can be ranked.
    assert codes == ["S3", "S5", "S1", "S4", "S2"]
    assert ranks == [1, 2, 3, 4, 5]


def test_hotspots_top_limits_the_list(client):
    response = client.get("/hotspots", params={"top": 2})
    codes = []
    for hotspot in response.json():
        codes.append(hotspot["sa2_code"])
    assert codes == ["S3", "S5"]


@pytest.mark.parametrize("top", [0, 101, "abc"], ids=["zero", "over 100", "not a number"])
def test_hotspots_rejects_bad_top(client, top):
    assert client.get("/hotspots", params={"top": top}).status_code == 422


def test_datasets_lists_sources(client):
    response = client.get("/datasets")
    assert response.status_code == 200
    ids = []
    for dataset in response.json():
        ids.append(dataset["id"])
    assert ids == ["test_sa2", "test_seifa"]


def test_regions_csv_has_headers_and_every_region(client):
    response = client.get("/regions.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    lines = response.text.splitlines()
    assert lines[0] == ",".join(REGION_CSV_COLUMNS)
    assert len(lines) == 1 + 7