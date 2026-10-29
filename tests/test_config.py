from sqlalchemy import create_engine

from config import normalize_database_url


def test_render_postgres_urls_use_psycopg_driver():
    for value in ("postgres://u:p@host/db", "postgresql://u:p@host/db"):
        normalized = normalize_database_url(value)
        assert normalized.startswith("postgresql+psycopg://")
        create_engine(normalized).dispose()
