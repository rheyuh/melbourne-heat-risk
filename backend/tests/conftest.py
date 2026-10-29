"""Shared test setup: a throwaway PostGIS database built from the real schema."""
import os

import pytest
from sqlalchemy import text

from config import PROJECT_ROOT
from ingest import get_engine

SCHEMA_SQL = PROJECT_ROOT / "db" / "init" / "20_schema.sql"
TEST_DB = os.environ["POSTGRES_DB"] + "_test"


@pytest.fixture(scope="session")
def engine():
    # CREATE/DROP DATABASE cannot run inside a transaction, so use autocommit.
    admin = get_engine().execution_options(isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))

    test_engine = get_engine(TEST_DB)
    with test_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION postgis"))
        conn.exec_driver_sql(SCHEMA_SQL.read_text())

    yield test_engine

    test_engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE {TEST_DB}"))
