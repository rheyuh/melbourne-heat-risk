import os
from sqlalchemy import create_engine, text

def get_engine():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql+psycopg://{user}:{password}@localhost:{port}/{db}")

if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        query = text("SELECT postgis_version()")
        result = conn.execute(query).scalar()
        print(result)