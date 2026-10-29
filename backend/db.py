"""Database connection, shared by the loaders, the tests, and the API."""

import os

from sqlalchemy import create_engine

def get_engine(database=None):
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = database or os.environ["POSTGRES_DB"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql+psycopg://{user}:{password}@localhost:{port}/{db}")