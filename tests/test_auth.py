from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.db
PASSWORD = "test-password-123"


@pytest.mark.parametrize("prefix", ["", "/api"])
def test_register_login_and_profile(client, db_session, app_modules, prefix):
    from sqlalchemy import select
    from models.user import User

    credentials = {"email": "person@example.com", "password": PASSWORD}
    response = client.post(f"{prefix}/auth/register", json=credentials)
    assert response.status_code == 201
    user = response.json()
    assert set(user) == {"id", "email"}
    assert isinstance(user["id"], int)
    assert user["email"] == credentials["email"]
    stored = db_session.scalar(select(User).where(User.email == user["email"]))
    assert stored.hashed_password != PASSWORD
    assert app_modules[2].verify_password(PASSWORD, stored.hashed_password)
    login = client.post(f"{prefix}/auth/login", json=credentials)
    assert login.status_code == 200
    assert set(login.json()) == {"access_token", "token_type"}
    assert login.json()["token_type"] == "bearer"
    profile = client.get(f"{prefix}/auth/me", headers={"Authorization": "Bearer " + login.json()["access_token"]})
    assert profile.status_code == 200
    assert profile.json() == user


def test_duplicate_registration_preserves_original_password(client):
    credentials = {"email": "duplicate@example.com", "password": PASSWORD}
    assert client.post("/auth/register", json=credentials).status_code == 201
    duplicate = client.post("/auth/register", json={**credentials, "password": "replacement-password"})
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "Email already registered"}
    assert client.post("/auth/login", json=credentials).status_code == 200
    assert client.post("/auth/login", json={**credentials, "password": "replacement-password"}).status_code == 401


@pytest.mark.parametrize("payload", [
    {"email": "invalid", "password": PASSWORD},
    {"email": "valid@example.com", "password": "short"},
    {"email": "valid@example.com", "password": "x" * 129},
    {"email": "valid@example.com"},
])
def test_invalid_registration(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


@pytest.mark.parametrize("email,password", [("missing@example.com", PASSWORD), ("owner@example.com", "incorrect")])
def test_invalid_login(client, account, email, password):
    account()
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


@pytest.mark.parametrize("kind", ["missing", "basic", "malformed", "expired", "signature", "missing_sub", "missing_exp", "invalid_sub", "nonexistent"])
def test_invalid_bearer_authentication(client, account, app_modules, kind):
    import jwt

    user, _ = account()
    security = app_modules[2]
    payload = {"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    key = security.JWT_SECRET_KEY
    if kind == "expired":
        payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
    elif kind == "signature":
        key = "different-test-secret-key-that-is-long-enough"
    elif kind == "missing_sub":
        payload.pop("sub")
    elif kind == "missing_exp":
        payload.pop("exp")
    elif kind == "invalid_sub":
        payload["sub"] = "not-an-integer"
    elif kind == "nonexistent":
        payload["sub"] = "2147483647"
    token = jwt.encode(payload, key, algorithm="HS256")
    headers = {"Authorization": "Bearer " + token}
    if kind == "missing":
        headers = {}
    elif kind == "basic":
        headers = {"Authorization": "Basic abc"}
    elif kind == "malformed":
        headers = {"Authorization": "Bearer not-a-jwt"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid or missing access token"}
