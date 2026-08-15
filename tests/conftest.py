import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "api"
sys.path.insert(0, str(API_DIR))

os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["JWT_SECRET"] = "test-jwt-secret-that-is-longer-than-thirty-two-bytes"

from app.core.security import hash_password
from app.models import Base, User


@pytest.fixture()
def client():
    """
    TestClient backed by a shared in-memory SQLite database so that
    seeded data is visible to every request handled by the app.
    """
    from sqlalchemy.pool import StaticPool

    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client, TestingSessionLocal
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_user(db_session):
    def _make_user(
        email="user@example.com",
        password="password123",
        username="user",
    ):
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _make_user
