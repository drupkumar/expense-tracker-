import pytest
from pathlib import Path

from app import create_app
from models import db


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "UPLOAD_FOLDER": Path(__file__).parent / ".uploads",
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(client):
    client.post("/register", data={"name": "Test User", "email": "test@example.com", "password": "StrongPass1"})
    return {"email": "test@example.com", "password": "StrongPass1"}
