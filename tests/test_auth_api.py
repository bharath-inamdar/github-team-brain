from app import models
from app.core.security import create_access_token


def _register(client, email, password="password123", username=None):
    payload = {"email": email, "password": password}
    if username:
        payload["username"] = username
    return client.post("/api/v1/auth/register", json=payload)


def _auth_headers(client, email, password="password123"):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_register_returns_access_token(client):
    test_client, _ = client

    response = _register(
        test_client,
        email="alice@example.com",
        username="alice",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["username"] == "alice"
    assert body["user"]["is_active"] is True


def test_register_accepts_optional_username(client):
    test_client, _ = client

    response = _register(
        test_client,
        email="no-username@example.com",
    )

    assert response.status_code == 201
    assert (
        response.json()["user"]["username"]
        == "no-username"
    )


def test_register_rejects_duplicate_email(client):
    test_client, _ = client

    first = _register(
        test_client,
        email="dup@example.com",
    )
    assert first.status_code == 201

    second = _register(
        test_client,
        email="dup@example.com",
    )
    assert second.status_code == 409


def test_register_rejects_invalid_payload(client):
    test_client, _ = client

    invalid_email = _register(
        test_client,
        email="not-an-email",
    )
    assert invalid_email.status_code == 422

    short_password = _register(
        test_client,
        email="short-pw@example.com",
        password="short",
    )
    assert short_password.status_code == 422


def test_login_returns_token(client):
    test_client, _ = client
    _register(
        test_client,
        email="bob@example.com",
        username="bob",
    )

    response = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "bob@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "bob@example.com"


def test_login_rejects_wrong_password(client):
    test_client, _ = client
    _register(
        test_client,
        email="carol@example.com",
    )

    response = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "carol@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user(client):
    test_client, _ = client

    response = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "nobody@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401


def test_me_returns_current_user(client):
    test_client, _ = client
    _register(
        test_client,
        email="dave@example.com",
        username="dave",
    )

    response = test_client.get(
        "/api/v1/auth/me",
        headers=_auth_headers(
            test_client,
            "dave@example.com",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "dave@example.com"
    assert body["username"] == "dave"


def test_me_requires_valid_token(client):
    test_client, _ = client
    _register(
        test_client,
        email="eve@example.com",
    )

    missing = test_client.get("/api/v1/auth/me")
    assert missing.status_code == 401

    garbage = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert garbage.status_code == 401

    expired_token = create_access_token(
        99999,
        expires_minutes=-1,
    )
    expired = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired.status_code == 401


def test_me_rejects_unknown_user_token(client):
    test_client, session_factory = client
    _register(
        test_client,
        email="frank@example.com",
    )
    db = session_factory()
    try:
        user = (
            db.query(models.User)
            .filter(models.User.email == "frank@example.com")
            .first()
        )
        db.delete(user)
        db.commit()
    finally:
        db.close()

    token = create_access_token(user.id)
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_protected_routes_require_authentication(client):
    test_client, _ = client

    assert (
        test_client.get("/api/v1/repositories").status_code
        == 401
    )
    assert (
        test_client.post("/api/v1/ai/index-review").status_code
        == 401
    )
    assert (
        test_client.get("/api/v1/dashboard/overview").status_code
        == 401
    )
