"""Unit tests for formats.py: plain dicts in, GeoJSON or CSV out. No database."""

import pytest

import formats

REGION = {
    "sa2_code": "S1",
    "sa2_name": "Test region",
    "risk_score": None,
    "double_burden": None,
    "geometry": '{"type":"Polygon","coordinates":[[[145.0,-37.81],[145.01,-37.81],[145.01,-37.8],[145.0,-37.8],[145.0,-37.81]]]}',
}


def test_to_feature_parses_geometry_and_keeps_nulls():
    feature = formats.to_feature(REGION)
    assert feature["type"] == "Feature"
    assert feature["id"] == "S1"
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["properties"]["risk_score"] is None


@pytest.mark.parametrize("value, expected", [
    ('=HYPERLINK("x")', '\'=HYPERLINK("x")'),
    ("+1", "'+1"),
    ("-1", "'-1"),
    ("@SUM(A1)", "'@SUM(A1)"),
    ("St Albans - South", "St Albans - South"),
    (-0.12, -0.12),
    (None, None),
])
def test_csv_safe(value, expected):
    assert formats.csv_safe(value) == expected


def test_to_csv_writes_header_escapes_and_drops_extra_columns():
    rows = [{"sa2_code": "S1", "sa2_name": "=evil", "secret": "no"}]
    lines = formats.to_csv(rows, ["sa2_code", "sa2_name"]).splitlines()
    assert lines == ["sa2_code,sa2_name", "S1,'=evil"]


def test_to_csv_with_no_rows_writes_only_header():
    assert formats.to_csv([], ["sa2_code"]).splitlines() == ["sa2_code"]